from django.db import models
from accounts.models import Accounts
from proposals.models import ThesisProposal


class ThesisGroup(models.Model):
    id = models.AutoField(primary_key=True)
    proposal = models.OneToOneField(ThesisProposal, on_delete=models.CASCADE, related_name='thesis_group')
    assigned_supervisor = models.ForeignKey(Accounts, on_delete=models.CASCADE, related_name='supervised_groups')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Group: {self.proposal.proposed_title} (Supervisor: {self.assigned_supervisor.username})"


class ThesisProject(models.Model):
    proposal = models.OneToOneField(
        ThesisProposal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='thesis_project',
    )
    student = models.ForeignKey(
        Accounts,
        on_delete=models.CASCADE,
        related_name='thesis_projects',
    )
    supervisor = models.ForeignKey(
        Accounts,
        on_delete=models.CASCADE,
        related_name='supervised_projects',
    )
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def progress_percentage(self):
        stage_keywords = (
            ('supervisor matching', 'matching', 'supervisor'),
            ('proposal submission', 'submit proposal', 'project proposal', 'proposal'),
            ('planning', 'detailed plan', 'project plan'),
            ('requirement analysis', 'requirements', 'literature review', 'literature'),
            ('system design', 'system architecture', 'architecture', 'design'),
            ('implementation', 'coding', 'development'),
            ('testing', 'test', 'validation', 'quality assurance'),
            ('deployment', 'deploy', 'release', 'launch'),
            ('maintenance', 'support', 'enhancement'),
            ('thesis defense', 'final defense', 'book submission', 'defense', 'final thesis'),
        )
        milestones = list(self.milestones.all())
        used_ids = set()
        completed = 0
        for stage_number, keywords in enumerate(stage_keywords, start=1):
            milestone = next(
                (item for item in milestones
                 if item.id not in used_ids
                 and any(keyword in item.title.lower() for keyword in keywords)),
                None,
            )
            if milestone is not None:
                used_ids.add(milestone.id)
            if (stage_number == 1 and self.supervisor_id) or (
                milestone is not None and milestone.status == 'Completed'
            ):
                completed += 1
        return completed * 10

    def __str__(self):
        return f"{self.title} - {self.student.username}"


class Milestone(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Submitted', 'Submitted'),
        ('Under Review', 'Under Review'),
        ('Completed', 'Completed'),
        ('Revision Required', 'Revision Required'),
    )

    id = models.AutoField(primary_key=True)
    project = models.ForeignKey(
        ThesisProject,
        on_delete=models.CASCADE,
        related_name='milestones',
        null=True,
        blank=True,
    )
    group = models.ForeignKey(
        ThesisGroup,
        on_delete=models.CASCADE,
        related_name='legacy_milestones',
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    due_date = models.DateField(blank=True, null=True)
    submission_link = models.URLField(blank=True)
    submission_notes = models.TextField(blank=True)
    supervisor_feedback = models.TextField(blank=True)
    submitted_file = models.FileField(upload_to='milestone_submissions/', blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        project_title = self.project.title if self.project else 'Legacy group milestone'
        return f"{self.title} - {project_title}"


class MilestoneSubmission(models.Model):
    STATUS_CHOICES = Milestone.STATUS_CHOICES

    milestone = models.ForeignKey(
        Milestone,
        on_delete=models.CASCADE,
        related_name='submission_history',
    )
    submitted_by = models.ForeignKey(
        Accounts,
        on_delete=models.CASCADE,
        related_name='milestone_submissions',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    submission_link = models.URLField(blank=True)
    submission_notes = models.TextField(blank=True)
    submitted_file = models.FileField(upload_to='milestone_submissions/history/', blank=True, null=True)
    supervisor_feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.milestone.title} - {self.status} - {self.created_at:%Y-%m-%d}'