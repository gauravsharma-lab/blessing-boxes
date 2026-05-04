from django import forms
from .models import FoodDonation, NGO
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
                'placeholder': 'Enter 10-digit number',
                'maxlength': '10',
                'pattern': '[0-9]{10}',
                'oninput': "this.value = this.value.replace(/[^0-9]/g, '');",
                'inputmode': 'numeric'
            }),
        }

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        # Remove any non-numeric characters if needed, but here we expect clean input
        if not phone.isdigit():
            raise forms.ValidationError("Phone number must contain only digits.")
        if len(phone) != 10:
            raise forms.ValidationError("Phone number must be exactly 10 digits.")
        return phone

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

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email'
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email.lower().endswith('@gmail.com'):
            raise forms.ValidationError("Please provide a legitimate @gmail.com address.")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

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


class NGOForm(forms.ModelForm):
    class Meta:
        model = NGO
        fields = ['name', 'location', 'phone_number']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Organization Name'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Delivery Address'}),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'NGO Contact Number',
                'maxlength': '15'
            }),
        }

from .models import Profile

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone_number']
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Your Phone Number',
                'maxlength': '15'
            }),
        }