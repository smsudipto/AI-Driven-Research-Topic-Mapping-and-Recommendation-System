from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.db.models import Q
from urllib.parse import quote
from .forms import ProposalRequestForm, ResearchTopicForm
from .models import ResearchTopic, SupervisorRequest, ThesisProposal
from accounts.models import Accounts
from profiles.models import StudentProfile, SupervisorProfile


def _is_role(user, role):
    return getattr(user, 'role', '').lower() == role


def _prepare_supervisor_request(supervisor_request):
    feedback_marker = '\n\nSupervisor feedback:\n'
    message, separator, feedback = supervisor_request.message.partition(feedback_marker)
    supervisor_request.proposed_title = supervisor_request.topic_title or 'Supervisor request'
    supervisor_request.proposed_abstract = message
    supervisor_request.supervisor_feedback = feedback if separator else ''
    supervisor_request.status = supervisor_request.status.lower()
    supervisor_request.review_kind = 'request'
    return supervisor_request


def _ensure_request_project(supervisor_request):
    from progress_tracker.models import ThesisProject

    return ThesisProject.objects.get_or_create(
        proposal=None,
        student=supervisor_request.student,
        supervisor=supervisor_request.supervisor,
        defaults={
            'title': supervisor_request.topic_title or 'Supervisor request project',
        },
    )[0]


@login_required(login_url='login')
def topic_list_view(request):
    topics = ResearchTopic.objects.select_related('supervisor').all()
    query = request.GET.get('q', '').strip()
    selected_domain = request.GET.get('domain', '').strip()

    if query:
        topics = topics.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(domain__icontains=query)
            | Q(prerequisites__icontains=query)
        )
    if selected_domain:
        topics = topics.filter(domain__iexact=selected_domain)

    domains = ResearchTopic.objects.values_list('domain', flat=True).distinct().order_by('domain')
    return render(request, 'proposals/topics.html', {
        'topics': topics,
        'domains': domains,
        'query': query,
        'selected_domain': selected_domain,
        'topic_form': ResearchTopicForm() if _is_role(request.user, 'supervisor') else None,
        'proposal_form': ProposalRequestForm() if _is_role(request.user, 'student') else None,
    })


@login_required(login_url='login')
def create_topic_view(request):
    if not _is_role(request.user, 'supervisor'):
        messages.error(request, 'Only supervisors can create research topics.')
        return redirect('topics')
    if request.method != 'POST':
        return redirect('topics')

    form = ResearchTopicForm(request.POST)
    if form.is_valid():
        topic = form.save(commit=False)
        topic.supervisor = request.user
        topic.save()
        messages.success(request, 'Research topic added successfully.')
    else:
        messages.error(request, 'Please correct the topic form and try again.')
    return redirect('topics')


@login_required(login_url='login')
def edit_topic_view(request, topic_id):
    topic = get_object_or_404(ResearchTopic, id=topic_id, supervisor=request.user)
    if request.method == 'POST':
        form = ResearchTopicForm(request.POST, instance=topic)
        if form.is_valid():
            form.save()
            messages.success(request, 'Research topic updated successfully.')
        else:
            messages.error(request, 'Please correct the topic form and try again.')
    return redirect('topics')


@login_required(login_url='login')
def toggle_topic_status_view(request, topic_id):
    if not _is_role(request.user, 'supervisor'):
        messages.error(request, 'Only supervisors can change topic status.')
        return redirect('topics')
    topic = get_object_or_404(ResearchTopic, id=topic_id, supervisor=request.user)
    if request.method == 'POST':
        topic.status = 'Closed' if topic.status == 'Open' else 'Open'
        topic.save(update_fields=('status',))
        messages.success(request, f'Topic is now {topic.status.lower()}.')
    return redirect('topics')


@login_required(login_url='login')
def request_proposal_view(request, topic_id):
    if not _is_role(request.user, 'student'):
        messages.error(request, 'Only students can send proposal requests.')
        return redirect('topics')

    topic = get_object_or_404(ResearchTopic.objects.select_related('supervisor'), id=topic_id)
    if request.method != 'POST':
        return redirect('topics')

    form = ProposalRequestForm(request.POST)
    if topic.status != 'Open' or topic.available_seats < 1:
        messages.error(request, 'This topic is not currently accepting applications.')
    elif ThesisProposal.objects.filter(student=request.user, topic=topic).exists():
        messages.error(request, 'You have already sent a request for this topic.')
    elif form.is_valid():
        proposal = ThesisProposal.objects.create(
            student=request.user,
            supervisor=topic.supervisor,
            topic=topic,
            proposed_title=topic.title,
            proposed_abstract=form.cleaned_data['message'],
            status='pending',
        )
        student_name = request.user.get_full_name() or request.user.username
        try:
            send_mail(
                subject=f'New thesis proposal request: {topic.title}',
                message=(
                    f'{student_name} has requested to work on "{topic.title}".\n\n'
                    f'Cover note:\n{proposal.proposed_abstract}\n\n'
                    f'Student email: {request.user.email}'
                ),
                from_email=None,
                recipient_list=[topic.supervisor.email],
                fail_silently=False,
            )
            messages.success(request, 'Your proposal request was sent to the supervisor.')
        except Exception:
            messages.error(request, 'Your proposal was saved, but the notification email could not be sent.')
    else:
        messages.error(request, 'Please write a cover note of at least 20 characters.')
    return redirect('topics')


# 1. Proposal List View (Students view their own, supervisors view assigned proposals)
@login_required
def proposal_list_view(request):
    user = request.user
    received_requests = SupervisorRequest.objects.none()
    
    if user.role == 'student':
        proposals = ThesisProposal.objects.filter(student=user).order_by('-created_at')
        requests = SupervisorRequest.objects.filter(student=user).order_by('-created_at')
        for supervisor_request in requests:
            _prepare_supervisor_request(supervisor_request)
        proposals = sorted(
            [*proposals, *requests],
            key=lambda item: item.created_at,
            reverse=True,
        )
    elif user.role == 'supervisor':
        proposals = ThesisProposal.objects.filter(supervisor=user).order_by('-created_at')
        for proposal in proposals:
            proposal.review_kind = 'proposal'
        received_requests = SupervisorRequest.objects.filter(
            supervisor=user,
            initiated_by='Student',
        ).order_by('-id')
        for supervisor_request in received_requests:
            _prepare_supervisor_request(supervisor_request)
        proposals = sorted(
            [*proposals, *received_requests],
            key=lambda item: item.created_at,
            reverse=True,
        )
    else:
        proposals = ThesisProposal.objects.all().order_by('-created_at')
        
    return render(request, 'proposals/proposal_list.html', {
        'proposals': proposals,
        'received_requests': received_requests,
    })


my_proposals_view = proposal_list_view


# 2. Create Proposal View (For students only)
@login_required
def create_proposal_view(request):
    if request.user.role != 'student':
        messages.error(request, "Only students can submit proposals.")
        return redirect('proposal_list')

    if request.method == 'POST':
        proposed_title = request.POST.get('proposed_title')
        proposed_abstract = request.POST.get('abstract') or request.POST.get('proposed_abstract')
        supervisor_id = request.POST.get('target_supervisor') or request.POST.get('supervisor')

        supervisor = get_object_or_404(Accounts, id=supervisor_id, role='supervisor')

        ThesisProposal.objects.create(
            student=request.user,
            supervisor=supervisor,
            proposed_title=proposed_title,
            proposed_abstract=proposed_abstract,
            status='pending'
        )
        messages.success(request, "Your thesis proposal has been submitted successfully!")
        return redirect('proposal_list')

    supervisors = Accounts.objects.filter(role='supervisor')
    return render(request, 'proposals/create_proposal.html', {'supervisors': supervisors})


# 3. Contact Student View (For supervisors to send contact request to students)
@login_required(login_url='login')
def contact_student_view(request, student_id):
    if request.user.role != 'supervisor':
        messages.error(request, 'Only supervisors can contact students from this page.')
        return redirect('dashboard')

    student_profile = get_object_or_404(
        StudentProfile.objects.select_related('user'),
        student_id=student_id,
        user__role='student',
    )

    student_profile.display_name = (
        student_profile.user.get_full_name()
        if hasattr(student_profile.user, 'get_full_name') and student_profile.user.get_full_name()
        else student_profile.user.username
    )
    student_profile.avatar_name = student_profile.display_name

    if request.method == 'POST':
        quick_message = request.POST.get('message', '').strip()
        subject = f"ThesisBridge contact request for {student_profile.display_name}"
        body = quick_message or (
            f"Hello {student_profile.display_name},\n\n"
            "I would like to contact you regarding a potential thesis proposal discussion."
        )

        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=None,
                recipient_list=[student_profile.user.email],
                fail_silently=False,
            )
        except Exception:
            messages.error(request, 'The email could not be sent. Please try again.')
            return render(request, 'proposals/contact_student.html', {
                'student': student_profile.user,
                'student_profile': student_profile,
                'quick_message': quick_message,
            })

        messages.success(
            request,
            f'Email sent successfully to {student_profile.user.username}!'
        )
        return redirect('find_students')

    return render(request, 'proposals/contact_student.html', {
        'student': student_profile.user,
        'student_profile': student_profile,
        'quick_message': '',
    })


# 4. Supervisor Detail View (View full supervisor profile details)
@login_required(login_url='login')
def supervisor_detail_view(request, supervisor_id):
    supervisor_profile = get_object_or_404(
        SupervisorProfile.objects.select_related('user'),
        id=supervisor_id
    )

    display_name = (
        supervisor_profile.user.get_full_name()
        if hasattr(supervisor_profile.user, 'get_full_name') and supervisor_profile.user.get_full_name()
        else supervisor_profile.user.username
    )

    return render(request, 'proposals/supervisor_detail.html', {
        'supervisor_profile': supervisor_profile,
        'display_name': display_name,
    })


# 5. Contact Supervisor View (For students to prepare message and contact supervisor)
@login_required(login_url='login')
def contact_supervisor_view(request, supervisor_id):
    supervisor_profile = get_object_or_404(
        SupervisorProfile.objects.select_related('user'),
        id=supervisor_id
    )

    display_name = (
        supervisor_profile.user.get_full_name()
        if hasattr(supervisor_profile.user, 'get_full_name') and supervisor_profile.user.get_full_name()
        else supervisor_profile.user.username
    )

    quick_message = ''
    mailto_link = None

    if request.method == 'POST':
        quick_message = request.POST.get('message', '').strip()
        subject = f"Thesis Proposal Discussion Request - {request.user.get_full_name() or request.user.username}"
        body = quick_message or (
            f"Hello {display_name},\n\n"
            "I would like to contact you regarding a potential thesis proposal discussion under your supervision."
        )
        mailto_link = (
            f"mailto:{supervisor_profile.user.email}"
            f"?subject={quote(subject)}"
            f"&body={quote(body)}"
        )

    return render(request, 'proposals/contact_supervisor.html', {
        'supervisor_profile': supervisor_profile,
        'display_name': display_name,
        'quick_message': quick_message,
        'mailto_link': mailto_link,
    })


# 6. Review Proposal View (For supervisors to approve or reject proposals & update capacity)
@login_required
def review_proposal_view(request, proposal_id):
    proposal = get_object_or_404(ThesisProposal, id=proposal_id)

    if request.user != proposal.supervisor and request.user.role != 'admin':
        messages.error(request, "You do not have permission to review this proposal.")
        return redirect('proposal_list')

    if request.method == 'POST':
        new_status = request.POST.get('status')  # Expected: 'accepted' or 'rejected'
        supervisor_feedback = request.POST.get('feedback') or request.POST.get('supervisor_feedback', '')

        old_status = proposal.status

        # Update proposal details
        proposal.status = new_status
        proposal.supervisor_feedback = supervisor_feedback
        proposal.save()

        # Update Supervisor Capacity Logic
        supervisor_profile = SupervisorProfile.objects.filter(user=proposal.supervisor).first()

        if supervisor_profile:
            capacity_field = None
            if hasattr(supervisor_profile, 'current_students'):
                capacity_field = 'current_students'
            elif hasattr(supervisor_profile, 'current_capacity'):
                capacity_field = 'current_capacity'

            if capacity_field:
                current_val = getattr(supervisor_profile, capacity_field) or 0

                # If status changed to accepted, increment capacity
                if new_status in ['accepted', 'approved'] and old_status not in ['accepted', 'approved']:
                    setattr(supervisor_profile, capacity_field, current_val + 1)
                    supervisor_profile.save()

                # If status changed from accepted to rejected/pending, decrement capacity
                elif old_status in ['accepted', 'approved'] and new_status not in ['accepted', 'approved']:
                    setattr(supervisor_profile, capacity_field, max(0, current_val - 1))
                    supervisor_profile.save()

        try:
            send_mail(
                subject=f'ThesisBridge proposal update: {proposal.proposed_title}',
                message=(
                    f'Your proposal status is now {new_status}.\n\n'
                    f'Supervisor feedback:\n{supervisor_feedback or "No feedback provided."}'
                ),
                from_email=None,
                recipient_list=[proposal.student.email],
                fail_silently=False,
            )
        except Exception:
            messages.warning(request, 'The proposal was updated, but the student notification email could not be sent.')
        messages.success(request, f"The proposal status has been updated to '{new_status}'.")
        return redirect('received_proposals')

    return render(request, 'proposals/review_proposal.html', {'proposal': proposal})


@login_required
def review_request_view(request, request_id):
    supervisor_request = get_object_or_404(
        SupervisorRequest,
        id=request_id,
        supervisor=request.user,
        initiated_by='Student',
    )
    feedback_marker = '\n\nSupervisor feedback:\n'
    saved_feedback = ''
    original_message = supervisor_request.message
    if feedback_marker in original_message:
        original_message, saved_feedback = original_message.split(feedback_marker, 1)

    if request.method == 'POST':
        new_status = request.POST.get('status', '').lower()
        supervisor_feedback = request.POST.get('feedback') or request.POST.get('supervisor_feedback', '')
        status_map = {'accepted': 'Accepted', 'rejected': 'Rejected'}
        if new_status not in status_map:
            messages.error(request, 'Please choose Accept or Reject before saving the review.')
            return redirect('review_request', request_id=supervisor_request.id)

        supervisor_request.status = status_map[new_status]
        supervisor_request.message = original_message + (
            f'{feedback_marker}{supervisor_feedback}' if supervisor_feedback else ''
        )
        supervisor_request.save(update_fields=('status', 'message', 'updated_at'))
        if supervisor_request.status == 'Accepted':
            _ensure_request_project(supervisor_request)
        try:
            send_mail(
                subject=f'ThesisBridge supervisor request update: {supervisor_request.topic_title or "Supervisor request"}',
                message=(
                    f'Your supervisor request status is now {supervisor_request.status}.\n\n'
                    f'Supervisor feedback:\n{supervisor_feedback or "No feedback provided."}'
                ),
                from_email=None,
                recipient_list=[supervisor_request.student.email],
                fail_silently=False,
            )
        except Exception:
            messages.warning(request, 'The request was updated, but the student notification email could not be sent.')
        messages.success(request, f"The request status has been updated to '{supervisor_request.status}'.")
        return redirect('received_proposals')

    supervisor_request.proposed_title = supervisor_request.topic_title or 'Supervisor request'
    supervisor_request.proposed_abstract = original_message
    supervisor_request.supervisor_feedback = saved_feedback
    supervisor_request.status = supervisor_request.status.lower()
    supervisor_request.review_kind = 'request'
    return render(request, 'proposals/review_proposal.html', {'proposal': supervisor_request})