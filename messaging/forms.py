from django import forms
from .models import Message, MessageReport


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content', 'file_attachment']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Type your message...',
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].label = 'Message'
        self.fields['file_attachment'].label = 'Attachment (optional)'
    
    def clean_file_attachment(self):
        file = self.cleaned_data.get('file_attachment')
        if file:
            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('File size cannot exceed 10MB.')
            
            # Check file type
            allowed_types = [
                'image/jpeg', 'image/png', 'image/gif', 'image/webp',
                'application/pdf', 'text/plain', 'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            ]
            
            if file.content_type not in allowed_types:
                raise forms.ValidationError(
                    'File type not allowed. Please upload images, PDFs, or documents.'
                )
        
        return file


class MessageReportForm(forms.ModelForm):
    class Meta:
        model = MessageReport
        fields = ['reason', 'description']
        widgets = {
            'reason': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Please provide additional details about your report...',
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False
        self.fields['description'].label = 'Additional Details (optional)'
