from django import forms

from .models import Milestone


class MilestoneCreateForm(forms.ModelForm):
    title = forms.ChoiceField(
        choices=tuple((title, title) for title, _ in (
            ('Supervisor Matching', ()),
            ('Proposal Submission', ()),
            ('Planning', ()),
            ('Requirement Analysis', ()),
            ('System Design', ()),
            ('Coding', ()),
            ('Testing', ()),
            ('Deployment', ()),
            ('Maintenance', ()),
            ('Final Defense', ()),
        )),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = Milestone
        fields = ('title', 'description', 'due_date')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Literature Review'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class MilestoneSubmissionForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = ('submission_link', 'submission_notes', 'submitted_file')
        widgets = {
            'submission_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'submission_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the work completed or in progress.'}),
            'submitted_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class MilestoneReviewForm(forms.ModelForm):
    status = forms.ChoiceField(
        choices=(
            ('Pending', 'Pending'),
            ('Submitted', 'Submitted'),
            ('Under Review', 'Under Review'),
            ('Completed', 'Completed'),
            ('Revision Required', 'Revision Required'),
        ),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = Milestone
        fields = ('status', 'supervisor_feedback')
        widgets = {
            'supervisor_feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Add feedback for the student.'}),
        }


MilestoneUpdateForm = MilestoneSubmissionForm