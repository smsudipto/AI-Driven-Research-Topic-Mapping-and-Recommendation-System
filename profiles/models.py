from django.conf import settings
from django.db import models

# Choice Options for Dropdowns
DEPARTMENT_CHOICES = [
    ('Computer Science', 'Computer Science'),
    ('Electrical Engineering', 'Electrical Engineering'),
    ('Civil', 'Civil'),
    ('Business', 'Business'),
]

STATUS_CHOICES = [
    ('Accepting Students', 'Accepting Students'),
    ('Full', 'Full'),
]


class StudentProfile(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=50, unique=True)
    profile_picture = models.ImageField(upload_to='students/', blank=True, null=True)
    department = models.CharField(max_length=100)
    intake = models.CharField(max_length=50, blank=True, null=True)
    section = models.CharField(max_length=50, blank=True, null=True)
    cgpa = models.DecimalField(max_digits=3, decimal_places=2)
    research_interests = models.TextField(blank=True, null=True)
    skills = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.student_id}"

    def get_interests_list(self):
        if self.research_interests:
            return [item.strip() for item in self.research_interests.split(',') if item.strip()]
        return []

    def get_skills_list(self):
        if self.skills:
            return [item.strip() for item in self.skills.split(',') if item.strip()]
        return []


class SupervisorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='supervisor_profile')
    
    # Existing fields
    designation = models.CharField(max_length=100, blank=True, null=True)
    expertise_areas = models.TextField(blank=True, null=True)
    max_student_capacity = models.IntegerField(default=5)
    current_student_count = models.IntegerField(default=0)
    
    # Updated & new fields (Profile picture, Department choices, Status)
    department = models.CharField(max_length=100, choices=DEPARTMENT_CHOICES, default='Computer Science')
    profile_pic = models.ImageField(upload_to='supervisors/', default='supervisors/default.png', blank=True, null=True)
    research_interests = models.CharField(max_length=255, blank=True, null=True, help_text="Comma-separated interests (e.g. AI, ML)")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Accepting Students')

    def __str__(self):
        # Uses get_full_name if available in Accounts model, otherwise falls back to username
        full_name = self.user.get_full_name() if hasattr(self.user, 'get_full_name') and self.user.get_full_name() else self.user.username
        desig = f" ({self.designation})" if self.designation else ""
        return f"{full_name}{desig} - {self.department}"

    def get_interests_list(self):
        """
        Converts comma-separated research interests or expertise areas into a clean list for Django templates.
        """
        interests_data = self.research_interests or self.expertise_areas
        if interests_data:
            # Splitting by comma, stripping extra spaces, and excluding empty strings
            return [item.strip() for item in interests_data.split(',') if item.strip()]
        return []