from django.contrib import admin
from .models import Doctor, Appointment

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'specialization', 'consultation_fee', 'is_active')
    list_filter = ('department', 'is_active')
    search_fields = ('name', 'specialization')

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient_name', 'patient_phone', 'doctor', 'appointment_date', 'time_slot', 'status')
    list_filter = ('status', 'appointment_date', 'doctor')
    search_fields = ('patient_name', 'patient_phone')
