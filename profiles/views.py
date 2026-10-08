from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.db.models import Count, Q
from .models import StudentProfile, SupervisorProfile
from proposals.models import SupervisorRequest

MAX_SUPERVISOR_CAPACITY = 5


def _decorate_supervisor_profile(profile):
    """
    Helper function to attach formatted display attributes to supervisor profile.
    """
    full_name = profile.user.get_full_name() if hasattr(profile.user, 'get_full_name') else ''
    profile.display_name = full_name or profile.user.username or 'Supervisor'
    profile.avatar_name = profile.display_name
    profile.designation_label = profile.designation or 'Designation not specified'
    profile.department_label = profile.department or 'Not specified'
    profile.expertise_areas_label = profile.expertise_areas or 'Not specified'
    
    assigned_count = getattr(profile, 'assigned_count', profile.current_student_count or 0)
    profile.assigned_count = assigned_count
    max_cap = profile.max_student_capacity or MAX_SUPERVISOR_CAPACITY
    profile.capacity_label = f"{assigned_count}/{max_cap}"
    profile.is_accepting = assigned_count < max_cap
    profile.status_label = profile.status if profile.status else ('Accepting Students' if profile.is_accepting else 'Full')
    profile.research_interests_list = profile.get_interests_list()
    return profile


def _decorate_student_profile(profile):
    """
    Helper function to attach formatted display attributes to student profile.
    """
    full_name = profile.user.get_full_name() if hasattr(profile.user, 'get_full_name') else ''
    profile.display_name = full_name or profile.user.username or 'Student'
    profile.avatar_name = profile.display_name
    profile.department_label = profile.department or 'Not specified'
    profile.intake_label = profile.intake or 'Not specified'
    profile.section_label = profile.section or 'Not specified'
    profile.cgpa_label = profile.cgpa if profile.cgpa is not None else 'Not specified'
    profile.research_interests_list = profile.get_interests_list()
    profile.skills_list = profile.get_skills_list()
    return profile


@login_required
def profile_view(request):
    """
    Renders the profile details based on user role (Student/Supervisor).
    """
    user = request.user
    
    if user.role == 'student':
        profile, created = StudentProfile.objects.get_or_create(user=user)
        return render(request, 'profiles/student_profile.html', {'profile': _decorate_student_profile(profile)})
    elif user.role == 'supervisor':
        profile, created = SupervisorProfile.objects.get_or_create(user=user)
        return render(request, 'profiles/supervisor_profile.html', {'profile': _decorate_supervisor_profile(profile)})
    else:
        return redirect('dashboard')


@login_required
def edit_profile_view(request):
    """
    Handles updates to user profile information including supervisor/student details and profile pictures.
    """
    user = request.user
    
    if request.method == 'POST':
        if user.role == 'student':
            profile, created = StudentProfile.objects.get_or_create(user=user)
            profile.student_id = request.POST.get('student_id', profile.student_id)
            profile.department = request.POST.get('department', profile.department)
            profile.intake = request.POST.get('intake', profile.intake)
            profile.section = request.POST.get('section', profile.section)
            profile.cgpa = request.POST.get('cgpa', profile.cgpa)
            profile.research_interests = request.POST.get('research_interests', profile.research_interests)
            profile.skills = request.POST.get('skills', profile.skills)
            profile.phone_number = request.POST.get('phone_number', profile.phone_number)
            if 'profile_picture' in request.FILES:
                profile.profile_picture = request.FILES['profile_picture']
            profile.save()
            
        elif user.role == 'supervisor':
            profile, created = SupervisorProfile.objects.get_or_create(user=user)
            
            # Update user full name
            full_name = request.POST.get('full_name')
            if full_name:
                names = full_name.strip().split(' ', 1)
                user.first_name = names[0]
                user.last_name = names[1] if len(names) > 1 else ''
                user.save()

            # Update supervisor fields from registration/edit form
            profile.designation = request.POST.get('designation', profile.designation)
            profile.expertise_areas = request.POST.get('expertise_areas', profile.expertise_areas)
            profile.department = request.POST.get('department', profile.department)
            profile.research_interests = request.POST.get('research_interests', profile.research_interests)
            profile.status = request.POST.get('status', profile.status)
            profile.max_student_capacity = request.POST.get('max_student_capacity', profile.max_student_capacity)
            
            # Handle profile picture upload
            if 'profile_pic' in request.FILES:
                profile.profile_pic = request.FILES['profile_pic']
                
            profile.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    # Handles GET requests
    if user.role == 'student':
        profile, created = StudentProfile.objects.get_or_create(user=user)
        profile = _decorate_student_profile(profile)
    else:
        profile, created = SupervisorProfile.objects.get_or_create(user=user)
        profile = _decorate_supervisor_profile(profile)
        
    return render(request, 'profiles/edit_profile.html', {'profile': profile})


@login_required(login_url='login')
def student_detail_view(request, student_id):
    """
    Renders detailed profile view for a specific student.
    """
    profile = get_object_or_404(
        StudentProfile.objects.select_related('user'),
        student_id=student_id,
    )

    if not request.user.is_supervisor and request.user != profile.user:
        messages.error(request, 'You do not have permission to view this student profile.')
        return redirect('dashboard')

    profile = _decorate_student_profile(profile)
    return render(request, 'profiles/student_detail.html', {'profile': profile})


@login_required(login_url='login')
def supervisor_detail_view(request, supervisor_id):
    """
    Renders detailed profile view of a specific supervisor for students and visitors.
    """
    profile = get_object_or_404(
        SupervisorProfile.objects.select_related('user'),
        id=supervisor_id,
    )
    profile = _decorate_supervisor_profile(profile)
    return render(request, 'profiles/supervisor_detail.html', {'profile': profile})


@login_required(login_url='login')
def contact_supervisor_view(request, supervisor_id):
    """Save a student request and notify the selected supervisor."""
    if request.user.role != 'student':
        messages.error(request, 'Only students can contact supervisors from this page.')
        return redirect('dashboard')

    supervisor_profile = get_object_or_404(
        SupervisorProfile.objects.select_related('user'),
        id=supervisor_id,
        user__role='supervisor',
    )
    supervisor_profile = _decorate_supervisor_profile(supervisor_profile)

    if request.method == 'POST':
        action = request.POST.get('action', 'save_request')
        if action == 'cancel':
            return redirect('my_proposals')

        if action == 'send_mail':
            supervisor_request = get_object_or_404(
                SupervisorRequest,
                id=request.POST.get('request_id'),
                student=request.user,
                supervisor=supervisor_profile.user,
                status='Pending',
                initiated_by='Student',
            )
            student_name = request.user.get_full_name() or request.user.username
            try:
                send_mail(
                    subject=f'ThesisBridge supervisor request from {student_name}',
                    message=(
                        f'{student_name} sent you a supervisor request.\n\n'
                        f'Message:\n{supervisor_request.message}\n\n'
                        f'Student email: {request.user.email}'
                    ),
                    from_email=None,
                    recipient_list=[supervisor_profile.user.email],
                    fail_silently=False,
                )
            except Exception:
                messages.error(request, 'The request was saved, but the email could not be sent. Please try again.')
                return render(request, 'profiles/contact_supervisor.html', {
                    'supervisor_profile': supervisor_profile,
                    'quick_message': supervisor_request.message,
                    'saved_request': supervisor_request,
                })
            messages.success(request, 'Your supervisor request email was sent successfully.')
            return redirect('my_proposals')

        quick_message = request.POST.get('message', '').strip()
        if not quick_message:
            messages.error(request, 'Please enter a message before saving your request.')
            return render(request, 'profiles/contact_supervisor.html', {
                'supervisor_profile': supervisor_profile,
                'quick_message': quick_message,
            })

        supervisor_request = SupervisorRequest.objects.create(
            student=request.user,
            supervisor=supervisor_profile.user,
            message=quick_message,
            status='Pending',
            initiated_by='Student',
        )
        messages.success(request, 'Request saved. Send the email notification when ready.')
        return render(request, 'profiles/contact_supervisor.html', {
            'supervisor_profile': supervisor_profile,
            'quick_message': quick_message,
            'saved_request': supervisor_request,
        })

    return render(request, 'profiles/contact_supervisor.html', {
        'supervisor_profile': supervisor_profile,
        'quick_message': '',
    })


def find_supervisor(request):
    """
    Handles supervisor searching and filtering dynamically based on search query, department, and status.
    """
    supervisors = (
        SupervisorProfile.objects
        .select_related('user')
        .annotate(assigned_count=Count('user__supervised_groups', distinct=True))
        .order_by('-id')
    )

    # 1. Filter by search keyword (name, username, research interests, or expertise areas)
    search_query = (request.GET.get('search') or request.GET.get('q') or '').strip()
    if search_query:
        supervisors = supervisors.filter(
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(research_interests__icontains=search_query) |
            Q(expertise_areas__icontains=search_query)
        )

    # 2. Filter by Department
    dept_query = (request.GET.get('department') or '').strip()
    if dept_query and dept_query != 'all':
        supervisors = supervisors.filter(department=dept_query)

    # 3. Filter by Availability Status
    status_query = (request.GET.get('status') or 'all').strip().lower()
    if status_query == 'accepting':
        supervisors = supervisors.filter(assigned_count__lt=MAX_SUPERVISOR_CAPACITY)
    elif status_query == 'full':
        supervisors = supervisors.filter(assigned_count__gte=MAX_SUPERVISOR_CAPACITY)

    supervisors = list(supervisors)
    for supervisor in supervisors:
        _decorate_supervisor_profile(supervisor)

    context = {
        'supervisors': supervisors
    }
    return render(request, 'profiles/find_supervisor.html', context)


@login_required(login_url='login')
def find_students(request):
    """
    Handles student searching and filtering for supervisors.
    """
    if not request.user.is_supervisor:
        messages.error(request, 'Only supervisors can access the student search page.')
        return redirect('dashboard')

    students = (
        StudentProfile.objects
        .select_related('user')
        .filter(user__role='student')
        .order_by('user__first_name', 'user__last_name', 'student_id')
    )

    search_query = (request.GET.get('search') or request.GET.get('q') or '').strip()
    if search_query:
        students = students.filter(
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(student_id__icontains=search_query) |
            Q(department__icontains=search_query) |
            Q(intake__icontains=search_query) |
            Q(section__icontains=search_query) |
            Q(research_interests__icontains=search_query) |
            Q(skills__icontains=search_query)
        )

    department_query = (request.GET.get('department') or '').strip()
    if department_query and department_query != 'all':
        students = students.filter(department=department_query)

    intake_query = (request.GET.get('intake') or '').strip()
    if intake_query:
        students = students.filter(intake__icontains=intake_query)

    section_query = (request.GET.get('section') or '').strip()
    if section_query:
        students = students.filter(section__icontains=section_query)

    interests_query = (request.GET.get('interests') or request.GET.get('skills') or '').strip()
    if interests_query:
        students = students.filter(
            Q(research_interests__icontains=interests_query) |
            Q(skills__icontains=interests_query)
        )

    students = list(students)
    for student in students:
        _decorate_student_profile(student)

    context = {
        'students': students,
        'search_query': search_query,
    }
    return render(request, 'profiles/find_students.html', context)