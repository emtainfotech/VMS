from django import forms
from App.models import company_invoice

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = company_invoice
        fields = '__all__'
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'invoice_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'payment_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        self.fields['invoice_attachment'].widget.attrs.update({'class': 'form-control-file'})