from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.contrib import messages
from proposals.models import SupervisorRequest, ThesisProposal
from .forms import MilestoneCreateForm, MilestoneReviewForm, MilestoneSubmissionForm
from .models import Milestone, MilestoneSubmission, ThesisGroup, ThesisProject


def _role(user):
    return getattr(user, 'role', '').lower()


def _accepted_projects(supervisor=None, student=None):
    proposals = ThesisProposal.objects.filter(status__in=('accepted', 'approved'))
    if supervisor is not None:
        proposals = proposals.filter(supervisor=supervisor)
    if student is not None:
        proposals = proposals.filter(student=student)
    for proposal in proposals:
        ThesisProject.objects.get_or_create(
            proposal=proposal,
            defaults={
                'student': proposal.student,
                'supervisor': proposal.supervisor,
                'title': proposal.proposed_title,
            },
        )
    requests = SupervisorRequest.objects.filter(status='Accepted', initiated_by='Student')
    if supervisor is not None:
        requests = requests.filter(supervisor=supervisor)
    if student is not None:
        requests = requests.filter(student=student)
    for supervisor_request in requests:
        existing_project = ThesisProject.objects.filter(
            proposal__isnull=True,
            student=supervisor_request.student,
            supervisor=supervisor_request.supervisor,
        ).first()
        if existing_project is None:
            ThesisProject.objects.create(
                student=supervisor_request.student,
                supervisor=supervisor_request.supervisor,
                title=supervisor_request.topic_title or 'Supervisor request project',
            )
    milestones = Prefetch(
        'milestones',
        queryset=Milestone.objects.order_by('-updated_at', '-id'),
    )
    return ThesisProject.objects.select_related('student', 'supervisor', 'proposal').prefetch_related(milestones)


def _step_state(status):
    if status == 'Completed':
        return 'completed'
    if status in ('In Progress', 'Submitted', 'Under Review', 'Revision Required'):
        return 'in-progress'
    return 'pending'


STANDARD_WORKFLOW = (
    ('Supervisor Matching', ('supervisor matching', 'matching', 'supervisor')),
    ('Proposal Submission', ('proposal submission', 'submit proposal', 'project proposal', 'proposal')),
    ('Planning', ('planning', 'detailed plan', 'project plan')),
    ('Requirement Analysis', ('requirement analysis', 'requirements', 'literature review', 'literature')),
    ('System Design', ('system design', 'system architecture', 'architecture', 'design')),
    ('Coding', ('implementation', 'coding', 'development')),
    ('Testing', ('testing', 'test', 'validation', 'quality assurance')),
    ('Deployment', ('deployment', 'deploy', 'release', 'launch')),
    ('Maintenance', ('maintenance', 'support', 'enhancement')),
    ('Final Defense', ('thesis defense', 'final defense', 'book submission', 'defense', 'final thesis')),
)


def _workflow_steps(project):
    milestones = list(project.milestones.all())
    used_ids = set()
    steps = []
    for stage_number, (stage_title, keywords) in enumerate(STANDARD_WORKFLOW, start=1):
        milestone = next(
            (item for item in milestones
             if item.id not in used_ids
             and any(keyword in item.title.lower() for keyword in keywords)),
            None,
        )
        if milestone is not None:
            used_ids.add(milestone.id)
        status = milestone.status if milestone else 'Pending'
        if stage_number == 1 and project.supervisor_id:
            status = 'Completed'
            if milestone is not None and milestone.status != 'Completed':
                milestone.status = 'Completed'
                milestone.save(update_fields=('status', 'submitted_at', 'updated_at'))
        steps.append({
            'title': stage_title,
            'milestone': milestone,
            'status': status,
            'state': _step_state(status),
            'is_standard': True,
        })
    return steps


def _with_workflow_steps(projects):
    projects = list(projects)
    for project in projects:
        project.workflow_steps = _workflow_steps(project)
        project.completion_percentage = sum(
            step['is_standard'] and step['status'] == 'Completed'
            for step in project.workflow_steps
        ) * 10
    return projects

# ১. থিসিস গ্রুপের লিস্ট এবং ড্যাশবোর্ড দেখা
@login_required
def group_dashboard_view(request):
    if _role(request.user) == 'supervisor':
        return redirect('student_progress')
    return redirect('my_progress')


@login_required
def my_progress_view(request):
    projects = _with_workflow_steps(_accepted_projects(student=request.user).filter(student=request.user))
    return render(request, 'progress_tracker/my_progress.html', {'projects': projects})


@login_required
def student_progress_view(request):
    projects = _with_workflow_steps(_accepted_projects(supervisor=request.user).filter(supervisor=request.user))
    return render(request, 'progress_tracker/student_progress.html', {'projects': projects})


# ২. নির্দিষ্ট একটি গ্রুপের মাইলস্টোন ও প্রোগ্রেস ডিটেইলস দেখা
@login_required
def group_detail_view(request, group_id):
    milestones = Prefetch(
        'milestones',
        queryset=Milestone.objects.order_by('-updated_at', '-id'),
    )
    project = get_object_or_404(ThesisProject.objects.prefetch_related(milestones), id=group_id)
    if _role(request.user) == 'student' and project.student_id != request.user.id:
        messages.error(request, 'You do not have access to this project.')
        return redirect('my_progress')
    if _role(request.user) == 'supervisor' and project.supervisor_id != request.user.id:
        messages.error(request, 'You do not have access to this project.')
        return redirect('student_progress')
    workflow_steps = _workflow_steps(project)
    completed_stages_count = sum(
        step['is_standard'] and step['status'] == 'Completed'
        for step in workflow_steps
    )
    completion_percentage = completed_stages_count * 10
    return render(request, 'progress_tracker/group_detail.html', {
        'project': project,
        'completion_percentage': round(completion_percentage, 2),
        'workflow_steps': workflow_steps,
    })


# ৩. নতুন মাইলস্টোন বা টাস্ক যোগ করা (সুপারভাইজার বা গ্রুপ মেম্বারদের জন্য)
@login_required
def create_milestone_view(request, group_id):
    project = get_object_or_404(ThesisProject, id=group_id, supervisor=request.user)
    if request.method == 'POST':
        form = MilestoneCreateForm(request.POST)
        if form.is_valid():
            milestone, created = Milestone.objects.get_or_create(
                project=project,
                title=form.cleaned_data['title'],
                defaults={
                    'description': form.cleaned_data['description'],
                    'due_date': form.cleaned_data['due_date'],
                },
            )
            if not created:
                milestone.description = form.cleaned_data['description']
                milestone.due_date = form.cleaned_data['due_date']
                milestone.save(update_fields=('description', 'due_date', 'updated_at'))
            messages.success(request, 'Milestone task updated successfully.')
            return redirect('group_detail', group_id=project.id)
    else:
        form = MilestoneCreateForm()
    return render(request, 'progress_tracker/create_milestone.html', {'project': project, 'form': form})


# ৪. মাইলস্টোনের স্ট্যাটাস আপডেট করা (যেমন: Pending -> Completed)
@login_required
def update_milestone_status_view(request, milestone_id):
    milestone = get_object_or_404(Milestone.objects.select_related('project'), id=milestone_id)
    if request.method == 'POST' and milestone.project:
        if milestone.project.student_id == request.user.id:
            if milestone.status not in ('Pending', 'Revision Required'):
                messages.error(request, 'This milestone is not currently accepting a submission.')
                return redirect('group_detail', group_id=milestone.project_id)
            form = MilestoneSubmissionForm(request.POST, request.FILES, instance=milestone)
            message = 'Progress submitted for supervisor review.'
            next_status = 'Submitted'
        elif milestone.project.supervisor_id == request.user.id:
            form = MilestoneReviewForm(request.POST, instance=milestone)
            message = 'Milestone review saved.'
            next_status = None
        else:
            form = None
            message = ''
            next_status = None
        if form and form.is_valid():
            milestone = form.save(commit=False)
            if next_status:
                milestone.status = next_status
            milestone.save()
            MilestoneSubmission.objects.create(
                milestone=milestone,
                submitted_by=request.user,
                status=milestone.status,
                submission_link=milestone.submission_link,
                submission_notes=milestone.submission_notes,
                submitted_file=milestone.submitted_file,
                supervisor_feedback=milestone.supervisor_feedback,
            )
            messages.success(request, message)
            if milestone.project.supervisor_id == request.user.id:
                return redirect(f'{reverse("student_progress")}#milestone-{milestone.id}')
            return redirect('group_detail', group_id=milestone.project_id)
    return redirect('group_dashboard')


@login_required
def update_milestone_view(request, milestone_id):
    return update_milestone_status_view(request, milestone_id)