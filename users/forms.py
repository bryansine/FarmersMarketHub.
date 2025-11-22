from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import User

# --- 1. User Registration Form ---
class UserRegisterForm(UserCreationForm):
    """
    Form for registering a new user. Uses the Custom User model.
    Adds a simple role radio (customer | farmer).
    """
    ROLE_CHOICES = (
        ('customer', 'Customer (Buying Produce)'),
        ('farmer', 'Farmer (Selling Produce)'),
    )

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect,
        initial='customer',
        label='I am registering as a',
        help_text='Choose your primary role on the platform.'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'phone_number', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Email required
        self.fields['email'].required = True
        self.fields['email'].widget = forms.EmailInput(attrs={'placeholder': 'you@example.com'})
        self.fields['username'].widget = forms.TextInput(attrs={'placeholder': 'Your unique username'})

        for name, field in self.fields.items():
            if name != 'role':  # don't add the class to radioselect wrapper
                field.widget.attrs.update({'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500'})
            else:
                field.widget.attrs.update({'class': 'mt-2'})

    def save(self, commit=True):
        user = super().save(commit=False)
        role = self.cleaned_data.get('role')
        if role == 'farmer':
            user.is_farmer = True
            user.is_customer = False
        else:
            user.is_farmer = False
            user.is_customer = True

        if commit:
            user.save()
        return user


# --- 2. User Login Form ---
class UserLoginForm(AuthenticationForm):
    """
    Standard Django form for user login, customized for appearance.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].widget.attrs.update({
            'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500',
            'placeholder': 'Username or Email'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500',
            'placeholder': 'Password'
        })

        self.fields['username'].label = 'Username or Email'
        self.fields['password'].label = 'Password'


# --- 3. User Profile Update Form ---
class UserProfileForm(forms.ModelForm):
    """
    Basic profile form used in profile editing (exposes only editable fields).
    """
    class Meta:
        model = User
        fields = ('username', 'email', 'phone_number')
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'you@example.com'}),
            'username': forms.TextInput(attrs={'placeholder': 'Your username'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make email required in profile form too
        self.fields['email'].required = True
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'w-full px-3 py-2 border rounded-lg'})
