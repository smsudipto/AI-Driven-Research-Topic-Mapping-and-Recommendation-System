from django import forms

from .models import ResearchTopic


class ResearchTopicForm(forms.ModelForm):
    available_seats = forms.IntegerField(
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(attrs={
            'class': 'form-control rounded-2 py-2 mb-3',
            'min': 1,
            'max': 5,
        }),
    )

    class Meta:
        model = ResearchTopic
        fields = ('title', 'domain', 'description', 'prerequisites', 'available_seats', 'status')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control rounded-2 py-2 mb-3', 'placeholder': 'e.g. Explainable AI for healthcare'}),
            'domain': forms.TextInput(attrs={'class': 'form-control rounded-2 py-2 mb-3', 'placeholder': 'Artificial Intelligence'}),
            'description': forms.Textarea(attrs={'class': 'form-control rounded-2 py-2 mb-3', 'rows': 3}),
            'prerequisites': forms.Textarea(attrs={'class': 'form-control rounded-2 py-2 mb-3', 'rows': 3, 'placeholder': 'Required skills, tools, or knowledge'}),
            'status': forms.Select(attrs={'class': 'form-control rounded-2 py-2 mb-3'}),
        }


class ProposalRequestForm(forms.Form):
    message = forms.CharField(
        label='Cover note',
        min_length=20,
        max_length=3000,
        widget=forms.Textarea(attrs={
            'rows': 6,
            'placeholder': 'Why are you interested in this topic, and what background do you bring?',
        }),
    )