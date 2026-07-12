from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import date

class Doctor(models.Model):
    DEPARTMENT_CHOICES = [
        ('CARDIO', 'Cardiology'),
        ('PEDIA', 'Pediatrics'),
        ('ORTHO', 'Orthopedics'),
        ('NEURO', 'Neurology'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile', null=True, blank=True)
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=10, choices=DEPARTMENT_CHOICES)
    specialization = models.CharField(max_length=150)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2)
    available_days = models.CharField(
        max_length=200, 
        help_text="Comma-separated days, e.g. Monday, Wednesday, Friday"
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Dr. {self.name} ({self.get_department_display()})"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('DECLINED', 'Declined'),
        ('COMPLETED', 'Completed'),
        ('RESCHEDULED', 'Rescheduled'),
    ]

    TIME_SLOT_CHOICES = [
        ('09:00 - 10:00', '09:00 AM - 10:00 AM'),
        ('10:00 - 11:00', '10:00 AM - 11:00 AM'),
        ('11:00 - 12:00', '11:00 AM - 12:00 PM'),
        ('12:00 - 13:00', '12:00 PM - 01:00 PM'),
        ('14:00 - 15:00', '02:00 PM - 03:00 PM'),
        ('15:00 - 16:00', '03:00 PM - 04:00 PM'),
        ('16:00 - 17:00', '04:00 PM - 05:00 PM'),
    ]

    PATIENT_RESPONSE_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    ]

    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments', null=True, blank=True)
    patient_name = models.CharField(max_length=100)
    patient_phone = models.CharField(max_length=20)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateField()
    time_slot = models.CharField(max_length=20, choices=TIME_SLOT_CHOICES)
    reason = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    
    # Extended workflow fields
    doctor_response_message = models.TextField(blank=True, null=True)
    rescheduled_date = models.DateField(null=True, blank=True)
    rescheduled_time = models.CharField(max_length=20, choices=TIME_SLOT_CHOICES, null=True, blank=True)
    patient_response = models.CharField(max_length=20, choices=PATIENT_RESPONSE_CHOICES, default='PENDING')
    declined_reason = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        
        # 1. Booking past dates
        if self.appointment_date and self.appointment_date < date.today():
            raise ValidationError({'appointment_date': "You cannot book appointments in the past."})
            
        # 2. Inactive doctor
        if self.doctor and not self.doctor.is_active:
            raise ValidationError({'doctor': f"Dr. {self.doctor.name} is currently inactive and cannot accept appointments."})
            
        # 3. Invalid time slot
        valid_slots = [choice[0] for choice in self.TIME_SLOT_CHOICES]
        if self.time_slot not in valid_slots:
            raise ValidationError({'time_slot': "Invalid time slot chosen."})
            
        # 4. Double booking (only check active appointments: PENDING, CONFIRMED, RESCHEDULED)
        # We check both the main date/slot and the rescheduled date/slot.
        overlapping = Appointment.objects.filter(
            doctor=self.doctor,
            appointment_date=self.appointment_date,
            time_slot=self.time_slot
        ).exclude(status='DECLINED')
        
        if self.pk:
            overlapping = overlapping.exclude(pk=self.pk)
            
        if overlapping.exists():
            raise ValidationError(
                f"Dr. {self.doctor.name} is already booked for {self.time_slot} on {self.appointment_date.strftime('%B %d, %Y')}."
            )
            
        # Validate rescheduled fields if status is RESCHEDULED
        if self.status == 'RESCHEDULED':
            if not self.rescheduled_date or not self.rescheduled_time:
                raise ValidationError("Rescheduled date and time slot must be provided when requesting reschedule.")
            if self.rescheduled_date < date.today():
                raise ValidationError({'rescheduled_date': "Rescheduled date cannot be in the past."})
            if self.rescheduled_time not in valid_slots:
                raise ValidationError({'rescheduled_time': "Invalid rescheduled time slot."})
                
            # Check double booking for rescheduled date/time
            overlapping_reschedule = Appointment.objects.filter(
                doctor=self.doctor,
                appointment_date=self.rescheduled_date,
                time_slot=self.rescheduled_time
            ).exclude(status='DECLINED')
            
            if self.pk:
                overlapping_reschedule = overlapping_reschedule.exclude(pk=self.pk)
                
            if overlapping_reschedule.exists():
                raise ValidationError(
                    f"Dr. {self.doctor.name} is already booked for {self.rescheduled_time} on {self.rescheduled_date.strftime('%B %d, %Y')}."
                )

    def __str__(self):
        return f"{self.patient_name} - {self.doctor.name} ({self.appointment_date} @ {self.time_slot})"

