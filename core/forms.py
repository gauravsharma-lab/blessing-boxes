from django import forms
from .models import FoodDonation
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone



class FoodDonationForm(forms.ModelForm):
    image = forms.ImageField(required=False) 
    
    
    class Meta:
        model = FoodDonation
        fields = ['description', 'quantity', 'phone_number', 'available_until', 'image']  # ✅ ONLY THIS

        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'quantity': forms.TextInput(attrs={'class': 'form-control'}),
            'available_until': forms.DateTimeInput(
                attrs={
                    'class': 'form-control',
                    'type': 'datetime-local',
                }
            ),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter mobile number'
            }),
        }

    def clean_available_until(self):
        value = self.cleaned_data.get('available_until')

        if value and value < timezone.now():
            raise forms.ValidationError("Valid till date cannot be in the past!")

        return value


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username',
            'required': True
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password',
            'required': True
        })
    )


class SignupForm(UserCreationForm):

    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username'
        })
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email'
        })
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

        widgets = {
    
    'description': forms.Textarea(attrs={'class': 'form-control'}),
    'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
    'available_until': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
}

def clean_available_until(self):
    value = self.cleaned_data.get('available_until')

    if value and value < timezone.now():
        raise forms.ValidationError("Valid till date cannot be in the past!")

    return value