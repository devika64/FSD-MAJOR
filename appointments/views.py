from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.db.models import Count
from datetime import date, datetime

from .models import Doctor, Appointment
from .forms import AppointmentForm, DoctorForm, PatientRegisterForm

class DoctorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and hasattr(self.request.user, 'doctor_profile')
        
    def handle_no_permission(self):
        messages.error(self.request, "Access restricted. You must be logged in as a Doctor to view this page.")
        return redirect('login')

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.is_superuser or self.request.user.is_staff)
        
    def handle_no_permission(self):
        messages.error(self.request, "Access restricted. You must be logged in as an Administrator to view this page.")
        return redirect('login')

# ----------------- Authentication Views -----------------

class LoginPortalView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, 'portal/login.html')

    def post(self, request):
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, 'portal/login.html')

class LogoutPortalView(View):
    def get(self, request):
        logout(request)
        messages.success(request, "You have been logged out successfully.")
        return redirect('login')

class RegisterPatientView(CreateView):
    model = User
    form_class = PatientRegisterForm
    template_name = 'portal/register.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        messages.success(self.request, "Account created successfully! Please log in.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Failed to register. Please check the registration details below.")
        return super().form_invalid(form)

# ----------------- Dashboard Dispatcher -----------------

class DashboardView(LoginRequiredMixin, View):
    login_url = 'login'
    
    def get(self, request):
        user = request.user
        if user.is_superuser or user.is_staff:
            return redirect('admin_dashboard')
        elif hasattr(user, 'doctor_profile') and user.doctor_profile:
            return redirect('doctor_dashboard')
        else:
            return redirect('patient_dashboard')

# ----------------- Patient Module Views -----------------

class DoctorListView(ListView):
    model = Doctor
    template_name = 'portal/doctor_list.html'
    context_object_name = 'doctors'

    def get_queryset(self):
        return Doctor.objects.all().order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = Doctor.DEPARTMENT_CHOICES
        return context

class AppointmentCreateView(LoginRequiredMixin, CreateView):
    login_url = 'login'
    model = Appointment
    form_class = AppointmentForm
    template_name = 'portal/book_appointment.html'
    success_url = reverse_lazy('dashboard')

    def get_initial(self):
        initial = super().get_initial()
        if self.request.user.is_authenticated:
            initial['patient_name'] = self.request.user.get_full_name() or self.request.user.username
            # Attempt to prefill phone from last appointment
            last_app = Appointment.objects.filter(patient=self.request.user).order_by('-created_at').first()
            if last_app:
                initial['patient_phone'] = last_app.patient_phone
        return initial

    def form_valid(self, form):
        appointment = form.save(commit=False)
        appointment.patient = self.request.user
        appointment.status = 'PENDING'
        
        # Model level full clean to ensure ORM validations run
        try:
            appointment.full_clean()
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    form.add_error(field, error)
            return self.form_invalid(form)
            
        appointment.save()
        messages.success(self.request, "Appointment booked successfully!")
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "There was an error booking your appointment. Please check the details below.")
        return super().form_invalid(form)

class PatientDashboardView(LoginRequiredMixin, ListView):
    login_url = 'login'
    model = Appointment
    template_name = 'portal/patient_dashboard.html'
    context_object_name = 'appointments'

    def get_queryset(self):
        return Appointment.objects.filter(patient=self.request.user).order_by('-appointment_date', 'time_slot')

class PatientRespondRescheduleView(LoginRequiredMixin, View):
    def post(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk, patient=request.user)
        response_type = request.POST.get('response')
        
        if response_type == 'accept':
            # Update date & slot to proposed rescheduled date & slot
            appointment.appointment_date = appointment.rescheduled_date
            appointment.time_slot = appointment.rescheduled_time
            appointment.status = 'CONFIRMED'
            appointment.patient_response = 'ACCEPTED'
            appointment.save()
            messages.success(request, "Patient accepted rescheduling.")
        elif response_type == 'reject':
            appointment.status = 'DECLINED'
            appointment.patient_response = 'REJECTED'
            appointment.save()
            messages.success(request, "Patient rejected rescheduling.")
        else:
            messages.error(request, "Invalid response action.")
            
        return redirect('dashboard')

# ----------------- Doctor Module Views -----------------

class DoctorDashboardView(LoginRequiredMixin, DoctorRequiredMixin, View):
    def get(self, request):
        doctor = request.user.doctor_profile
        today = date.today()
        
        # Today's appointments
        todays_appointments = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=today
        ).order_by('time_slot')
        
        # All appointments by tab categories
        pending_appointments = Appointment.objects.filter(doctor=doctor, status='PENDING').order_by('-appointment_date')
        confirmed_appointments = Appointment.objects.filter(doctor=doctor, status='CONFIRMED').order_by('-appointment_date')
        completed_appointments = Appointment.objects.filter(doctor=doctor, status='COMPLETED').order_by('-appointment_date')
        declined_appointments = Appointment.objects.filter(doctor=doctor, status='DECLINED').order_by('-appointment_date')
        rescheduled_appointments = Appointment.objects.filter(doctor=doctor, status='RESCHEDULED').order_by('-appointment_date')
        
        context = {
            'doctor': doctor,
            'todays_appointments': todays_appointments,
            'pending_appointments': pending_appointments,
            'confirmed_appointments': confirmed_appointments,
            'completed_appointments': completed_appointments,
            'declined_appointments': declined_appointments,
            'rescheduled_appointments': rescheduled_appointments,
            'time_slots': Appointment.TIME_SLOT_CHOICES
        }
        return render(request, 'portal/doctor_dashboard.html', context)

class DoctorAcceptView(LoginRequiredMixin, DoctorRequiredMixin, View):
    def post(self, request, pk):
        doctor = request.user.doctor_profile
        appointment = get_object_or_404(Appointment, pk=pk, doctor=doctor)
        appointment.status = 'CONFIRMED'
        appointment.save()
        messages.success(request, "Doctor accepted the appointment.")
        return redirect('dashboard')

class DoctorDeclineView(LoginRequiredMixin, DoctorRequiredMixin, View):
    def post(self, request, pk):
        doctor = request.user.doctor_profile
        appointment = get_object_or_404(Appointment, pk=pk, doctor=doctor)
        reason = request.POST.get('declined_reason', '').strip()
        appointment.status = 'DECLINED'
        appointment.declined_reason = reason
        appointment.save()
        messages.success(request, "Doctor declined the appointment.")
        return redirect('dashboard')

class DoctorRescheduleView(LoginRequiredMixin, DoctorRequiredMixin, View):
    def post(self, request, pk):
        doctor = request.user.doctor_profile
        appointment = get_object_or_404(Appointment, pk=pk, doctor=doctor)
        
        new_date_str = request.POST.get('rescheduled_date')
        new_time = request.POST.get('rescheduled_time')
        message = request.POST.get('doctor_response_message', '').strip()
        
        if not new_date_str or not new_time:
            messages.error(request, "Please specify a new date and time slot.")
            return redirect('dashboard')
            
        try:
            new_date = datetime.strptime(new_date_str, '%Y-%m-%d').date()
            appointment.rescheduled_date = new_date
            appointment.rescheduled_time = new_time
            appointment.doctor_response_message = message or "Dear Patient, I will not be available during the selected slot. Kindly consider the following alternative appointment."
            appointment.status = 'RESCHEDULED'
            appointment.patient_response = 'PENDING'
            appointment.full_clean()
            appointment.save()
            messages.success(request, "Doctor requested rescheduling.")
        except ValidationError as e:
            messages.error(request, f"Reschedule failed: {e.messages[0] if isinstance(e.messages, list) else e}")
        except Exception as e:
            messages.error(request, f"Error requesting reschedule: {e}")
            
        return redirect('dashboard')

# ----------------- Administrator Module Views -----------------

class AdminDashboardView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request):
        today = date.today()
        
        # Statistics
        total_appointments = Appointment.objects.count()
        today_appointments_count = Appointment.objects.filter(appointment_date=today).count()
        
        # Department stats
        dept_stats = []
        for code, label in Doctor.DEPARTMENT_CHOICES:
            count = Appointment.objects.filter(doctor__department=code).count()
            dept_stats.append({'label': label, 'count': count})
            
        # Get query parameters for filtering
        doctor_id = request.GET.get('doctor')
        department = request.GET.get('department')
        status = request.GET.get('status')
        date_str = request.GET.get('date')
        
        appointments = Appointment.objects.all().order_by('-appointment_date', 'time_slot')
        
        # Apply filters
        if doctor_id:
            appointments = appointments.filter(doctor_id=doctor_id)
        if department:
            appointments = appointments.filter(doctor__department=department)
        if status:
            appointments = appointments.filter(status=status)
        if date_str:
            try:
                filter_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                appointments = appointments.filter(appointment_date=filter_date)
            except ValueError:
                pass
                
        # Lists for filter dropdowns
        doctors = Doctor.objects.all().order_by('name')
        departments = Doctor.DEPARTMENT_CHOICES
        statuses = Appointment.STATUS_CHOICES
        
        context = {
            'total_appointments': total_appointments,
            'today_appointments_count': today_appointments_count,
            'dept_stats': dept_stats,
            'appointments': appointments,
            'doctors': doctors,
            'departments': departments,
            'statuses': statuses,
            # Selected filters to maintain UI state
            'selected_doctor': int(doctor_id) if doctor_id and doctor_id.isdigit() else None,
            'selected_department': department,
            'selected_status': status,
            'selected_date': date_str
        }
        return render(request, 'portal/admin_dashboard.html', context)

class AdminConfirmView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        appointment.status = 'CONFIRMED'
        appointment.save()
        messages.success(request, f"Appointment for {appointment.patient_name} confirmed.")
        return redirect('admin_dashboard')

class AdminCancelView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        appointment.status = 'DECLINED'
        appointment.declined_reason = "Cancelled by Administrator"
        appointment.save()
        messages.success(request, f"Appointment for {appointment.patient_name} cancelled.")
        return redirect('admin_dashboard')

class AdminCompleteView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        appointment.status = 'COMPLETED'
        appointment.save()
        messages.success(request, f"Appointment for {appointment.patient_name} marked as Completed.")
        return redirect('admin_dashboard')

class AdminAddDoctorView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Doctor
    form_class = DoctorForm
    template_name = 'portal/doctor_form.html'
    success_url = reverse_lazy('admin_dashboard')

    def form_valid(self, form):
        messages.success(self.request, "Doctor added successfully!")
        return super().form_valid(form)
        
    def form_invalid(self, form):
        messages.error(self.request, "Failed to add doctor. Please verify details.")
        return super().form_invalid(form)

class AdminEditDoctorView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Doctor
    form_class = DoctorForm
    template_name = 'portal/doctor_form.html'
    success_url = reverse_lazy('admin_dashboard')

    def form_valid(self, form):
        messages.success(self.request, "Doctor details updated successfully!")
        return super().form_valid(form)
        
    def form_invalid(self, form):
        messages.error(self.request, "Failed to edit doctor. Please verify details.")
        return super().form_invalid(form)

class AdminDeleteDoctorView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, pk):
        doctor = get_object_or_404(Doctor, pk=pk)
        name = doctor.name
        
        # Clean up User account too
        if doctor.user:
            doctor.user.delete()
        else:
            doctor.delete()
            
        messages.success(request, f"Doctor {name} and their account deleted successfully.")
        return redirect('admin_dashboard')

class AdminToggleDoctorActiveView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, pk):
        doctor = get_object_or_404(Doctor, pk=pk)
        doctor.is_active = not doctor.is_active
        doctor.save()
        status_str = "activated" if doctor.is_active else "deactivated"
        messages.success(request, f"Dr. {doctor.name} {status_str} successfully.")
        return redirect('admin_dashboard')

