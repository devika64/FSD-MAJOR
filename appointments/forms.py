from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import Doctor, Appointment
from datetime import date

class AppointmentForm(forms.ModelForm):
    doctor = forms.ModelChoiceField(
        queryset=Doctor.objects.filter(is_active=True),
        empty_label="Select Doctor",
        widget=forms.Select(attrs={'class': 'form-select glass-input'})
    )

    class Meta:
        model = Appointment
        fields = ['patient_name', 'patient_phone', 'doctor', 'appointment_date', 'time_slot', 'reason']
        widgets = {
            'patient_name': forms.TextInput(attrs={'class': 'form-control glass-input', 'placeholder': 'Enter patient full name'}),
            'patient_phone': forms.TextInput(attrs={'class': 'form-control glass-input', 'placeholder': 'Enter contact number'}),
            'appointment_date': forms.DateInput(attrs={'class': 'form-control glass-input', 'type': 'date'}),
            'time_slot': forms.Select(attrs={'class': 'form-select glass-input'}),
            'reason': forms.Textarea(attrs={'class': 'form-control glass-input', 'rows': 3, 'placeholder': 'Briefly describe symptoms...'}),
        }

    def clean_appointment_date(self):
        appointment_date = self.cleaned_data.get('appointment_date')
        if appointment_date and appointment_date < date.today():
            raise ValidationError("You cannot book appointments in the past.")
        return appointment_date

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        appointment_date = cleaned_data.get('appointment_date')
        time_slot = cleaned_data.get('time_slot')

        # Model validation handles most checks, but we do standard form validation here
        if doctor and appointment_date and time_slot:
            overlapping_appointment = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                time_slot=time_slot
            ).exclude(status='DECLINED')
            
            if self.instance and self.instance.pk:
                overlapping_appointment = overlapping_appointment.exclude(pk=self.instance.pk)
            
            if overlapping_appointment.exists():
                raise ValidationError(
                    f"Dr. {doctor.name} is already booked for {time_slot} on {appointment_date.strftime('%B %d, %Y')}."
                )

        return cleaned_data

class PatientRegisterForm(forms.ModelForm):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control glass-input', 'placeholder': 'Username'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control glass-input', 'placeholder': 'Email address'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control glass-input', 'placeholder': 'Password'}))
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control glass-input', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control glass-input', 'placeholder': 'Last Name'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("A user with that username already exists.")
        return username

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data.get('username'),
            email=self.cleaned_data.get('email'),
            password=self.cleaned_data.get('password'),
            first_name=self.cleaned_data.get('first_name'),
            last_name=self.cleaned_data.get('last_name')
        )
        return user

class DoctorForm(forms.ModelForm):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control glass-input', 'placeholder': 'Doctor Username'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control glass-input', 'placeholder': 'Doctor Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control glass-input', 'placeholder': 'Password'}), required=False)

    class Meta:
        model = Doctor
        fields = ['name', 'department', 'specialization', 'consultation_fee', 'available_days', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control glass-input', 'placeholder': 'Dr. First Last'}),
            'department': forms.Select(attrs={'class': 'form-select glass-input'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control glass-input', 'placeholder': 'e.g. Cardiology'}),
            'consultation_fee': forms.NumberInput(attrs={'class': 'form-control glass-input', 'placeholder': 'Fee in ₹'}),
            'available_days': forms.TextInput(attrs={'class': 'form-control glass-input', 'placeholder': 'e.g. Monday, Wednesday, Friday'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.user:
            self.fields['username'].initial = self.instance.user.username
            self.fields['email'].initial = self.instance.user.email
            self.fields['username'].disabled = True
            self.fields['password'].required = False
            self.fields['password'].help_text = "Leave blank if not updating password."
        else:
            self.fields['password'].required = True

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not self.instance.pk and User.objects.filter(username=username).exists():
            raise ValidationError("A user with that username already exists.")
        return username

    def save(self, commit=True):
        doctor = super().save(commit=False)
        username = self.cleaned_data.get('username')
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if not doctor.user:
            user = User.objects.create_user(username=username, email=email, password=password)
            doctor.user = user
        else:
            user = doctor.user
            user.email = email
            if password:
                user.set_password(password)
            user.save()

        if commit:
            doctor.save()
        return doctor

