from django import forms
from .models import EmailCredential

class EmailCredentialForm(forms.ModelForm):
    class Meta:
        model = EmailCredential
        fields = ['email', 'app_password']
        widgets = {
            'app_password': forms.PasswordInput(),
        }
