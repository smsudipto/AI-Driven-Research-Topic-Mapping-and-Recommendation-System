from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import Accounts
from profiles.models import StudentProfile, SupervisorProfile
from research_library.models import ThesisPaper

# 1. User Registration View
def register_view(request):
    if request.method == 'POST':
        form_data = request.POST
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role', 'student')
        student_id = request.POST.get('student_id', '').strip()
        student_department = request.POST.get('student_department', 'Computer Science')
        intake = request.POST.get('intake', '').strip()
        section = request.POST.get('section', '').strip()
        cgpa = request.POST.get('cgpa', '').strip()
        student_phone_number = request.POST.get('phone_number', '').strip()
        student_research_interests = request.POST.get('student_research_interests', '').strip()
        skills = request.POST.get('skills', '').strip()
        student_profile_picture = request.FILES.get('profile_picture')
        designation = request.POST.get('designation', '').strip()
        expertise_areas = request.POST.get('expertise_areas', '').strip()
        capacity_raw = request.POST.get('capacity')
        department = request.POST.get('department', 'Computer Science')
        research_interests = request.POST.get('research_interests', '').strip()
        status = request.POST.get('status', 'Accepting Students')
        profile_pic = request.FILES.get('profile_pic')

        # Check if Username already exists
        if Accounts.objects.filter(username=username).exists():
            messages.error(request, "Username already taken!")
            return render(request, 'accounts/auth.html', {'form_data': form_data, 'auth_mode': 'register'})

        # Check if Email already exists
        if Accounts.objects.filter(email=email).exists():
            messages.error(request, "This Email is already registered!")
            return render(request, 'accounts/auth.html', {'form_data': form_data, 'auth_mode': 'register'})

        if role == 'student':
            if not student_id or not student_department or not cgpa:
                messages.error(request, "Please complete the required student fields, including Student ID, Department, and CGPA.")
                return render(request, 'accounts/auth.html', {'form_data': form_data, 'auth_mode': 'register'})

        if role == 'supervisor':
            if not designation or not expertise_areas or not capacity_raw or not department or not research_interests or not status or not profile_pic:
                messages.error(request, "Please complete all supervisor fields, including the profile picture.")
                return render(request, 'accounts/auth.html', {'form_data': form_data, 'auth_mode': 'register'})

        with transaction.atomic():
            # Create the base account first so related profiles can point to it
            user = Accounts.objects.create_user(
                username=username,
                email=email,
                password=password,
                role=role
            )

            if role == 'supervisor':
                capacity = int(capacity_raw) if capacity_raw else 5
                supervisor_profile, _ = SupervisorProfile.objects.update_or_create(
                    user=user,
                    defaults={
                        'designation': designation,
                        'expertise_areas': expertise_areas,
                        'max_student_capacity': capacity,
                        'department': department,
                        'research_interests': research_interests,
                        'status': status,
                    }
                )

                if profile_pic:
                    supervisor_profile.profile_pic = profile_pic
                    supervisor_profile.save(update_fields=['profile_pic'])

            elif role == 'student':
                StudentProfile.objects.update_or_create(
                    user=user,
                    defaults={
                        'student_id': student_id,
                        'profile_picture': student_profile_picture,
                        'department': student_department,
                        'intake': intake or None,
                        'section': section or None,
                        'cgpa': cgpa,
                        'research_interests': student_research_interests,
                        'skills': skills,
                        'phone_number': student_phone_number or None,
                    }
                )

        login(request, user, backend='accounts.backends.EmailOrUsernameModelBackend')
        return redirect('dashboard')

    return render(request, 'accounts/auth.html', {'form_data': {}, 'auth_mode': 'register'})


# 2. User Login View
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password!")

    return render(request, 'accounts/auth.html', {'auth_mode': 'login'})


# 3. User Logout View
def logout_view(request):
    logout(request)
    return redirect('login')


# 4. Public landing page for guests and dashboard for authenticated users
def dashboard_view(request):
    if not request.user.is_authenticated:
        base_threshold = 1000
        return render(request, 'home.html', {
            'student_count': base_threshold + Accounts.objects.filter(role='student').count(),
            'supervisor_count': base_threshold + Accounts.objects.filter(role='supervisor').count(),
            'paper_count': base_threshold + ThesisPaper.objects.count(),
        })

    return render(request, 'dashboard.html')


@login_required(login_url='login')
def topics_view(request):
    topics = [
        {
            'title': 'Artificial Intelligence',
            'description': 'Machine learning, automation, and intelligent decision systems.',
        },
        {
            'title': 'Data Science',
            'description': 'Analytics, visualization, and evidence-driven research workflows.',
        },
        {
            'title': 'Software Engineering',
            'description': 'Architecture, testing, collaboration, and maintainable systems.',
        },
        {
            'title': 'Embedded Systems',
            'description': 'Hardware-aware thesis topics for sensors, control, and devices.',
        },
    ]
    return render(request, 'topics.html', {'topics': topics})