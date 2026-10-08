from django.db import models
from django.conf import settings


class SupervisorRequest(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
    )
    INITIATOR_CHOICES = (
        ('Student', 'Student'),
        ('Teacher', 'Teacher'),
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_requests',
    )
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='supervisor_requests',
    )
    topic_title = models.CharField(max_length=255, blank=True, null=True)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    initiated_by = models.CharField(max_length=10, choices=INITIATOR_CHOICES, default='Student')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.initiated_by} Request: {self.student.username} -> {self.supervisor.username} ({self.status})"


class ResearchTopic(models.Model):
    STATUS_CHOICES = (
        ('Open', 'Open'),
        ('Closed', 'Closed'),
    )

    title = models.CharField(max_length=255)
    description = models.TextField()
    domain = models.CharField(max_length=100)
    prerequisites = models.TextField()
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='research_topics',
    )
    available_seats = models.PositiveIntegerField(default=5)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Open')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class ThesisProposal(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )

    # স্টুডেন্ট ও সুপারভাইজার (Custom User Model / Accounts-এর সাথে কানেক্টেড)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='submitted_proposals'
    )
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='received_proposals'
    )
    topic = models.ForeignKey(
        ResearchTopic,
        on_delete=models.SET_NULL,
        related_name='proposals',
        blank=True,
        null=True,
    )

    # প্রপোজালের তথ্য (আপনার views.py অনুযায়ী)
    proposed_title = models.CharField(max_length=255)
    proposed_abstract = models.TextField()
    supervisor_feedback = models.TextField(blank=True, null=True)
    
    # প্রপোজালের সাথে ফাইল আপলোড অপশন (ঐচ্ছিক)
    file = models.FileField(upload_to='proposals/', blank=True, null=True)

    # স্ট্যাটাস ফিল্ড
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )

    # তারিখ ও সময়
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.proposed_title} - {self.student.username} ({self.status})"