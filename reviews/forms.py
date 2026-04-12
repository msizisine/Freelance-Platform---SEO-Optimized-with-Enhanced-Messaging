from django import forms
from .models import Review, ReviewResponse


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment', 'communication', 'quality', 'delivery', 'is_public']
        widgets = {
            'rating': forms.RadioSelect(choices=Review.RATING_CHOICES),
            'comment': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Share your experience working with this freelancer...'}),
            'communication': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'quality': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'delivery': forms.NumberInput(attrs={'min': 1, 'max': 5}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rating'].required = True
        self.fields['comment'].required = True
        self.fields['communication'].required = False
        self.fields['quality'].required = False
        self.fields['delivery'].required = False
        
        # Add help text for criteria ratings
        self.fields['communication'].help_text = "How was the communication? (1-5)"
        self.fields['quality'].help_text = "How was the quality of work? (1-5)"
        self.fields['delivery'].help_text = "Was the delivery on time? (1-5)"


class ReviewResponseForm(forms.ModelForm):
    class Meta:
        model = ReviewResponse
        fields = ['response']
        widgets = {
            'response': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Respond to the review...'}),
        }
