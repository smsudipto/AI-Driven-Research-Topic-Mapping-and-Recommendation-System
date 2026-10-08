from django import forms

from .models import ThesisPaper


class ThesisPaperForm(forms.ModelForm):
    class Meta:
        model = ThesisPaper
        fields = [
            'title',
            'abstract',
            'authors',
            'supervisor_name',
            'domain',
            'publication_year',
            'pdf_file',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Paper title'}),
            'abstract': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Abstract'}),
            'authors': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Author names'}),
            'supervisor_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Supervisor name'}),
            'domain': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Artificial Intelligence'}),
            'publication_year': forms.NumberInput(attrs={'class': 'form-control', 'min': 1900, 'max': 2100}),
            'pdf_file': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'application/pdf,.pdf'}),
        }

    def clean_pdf_file(self):
        pdf_file = self.cleaned_data['pdf_file']
        if not pdf_file.name.lower().endswith('.pdf'):
            raise forms.ValidationError('Please upload a PDF file.')
        return pdf_file