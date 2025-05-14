from django import forms

class CommentForm(forms.Form):
    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Add your comment here...',
            'class': 'form-control'
        }),
        required=True,
        label=''
    )