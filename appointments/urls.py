from django.urls import path
from . import views

urlpatterns = [
    # General & Patient URLs
    path('', views.DoctorListView.as_view(), name='doctor_list'),
    path('book/', views.AppointmentCreateView.as_view(), name='book_appointment'),
    
    # Auth URLs
    path('login/', views.LoginPortalView.as_view(), name='login'),
    path('logout/', views.LogoutPortalView.as_view(), name='logout'),
    path('register/', views.RegisterPatientView.as_view(), name='register'),
    
    # Dashboards Dispatcher
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    
    # Patient Dashboards & Actions
    path('patient/dashboard/', views.PatientDashboardView.as_view(), name='patient_dashboard'),
    path('patient/appointment/<int:pk>/respond/', views.PatientRespondRescheduleView.as_view(), name='patient_respond_reschedule'),
    
    # Doctor Dashboard & Actions
    path('doctor/dashboard/', views.DoctorDashboardView.as_view(), name='doctor_dashboard'),
    path('doctor/appointment/<int:pk>/accept/', views.DoctorAcceptView.as_view(), name='doctor_accept'),
    path('doctor/appointment/<int:pk>/decline/', views.DoctorDeclineView.as_view(), name='doctor_decline'),
    path('doctor/appointment/<int:pk>/reschedule/', views.DoctorRescheduleView.as_view(), name='doctor_reschedule'),
    
    # Admin Dashboard & Actions
    path('admin/dashboard/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin/doctor/add/', views.AdminAddDoctorView.as_view(), name='admin_add_doctor'),
    path('admin/doctor/<int:pk>/edit/', views.AdminEditDoctorView.as_view(), name='admin_edit_doctor'),
    path('admin/doctor/<int:pk>/delete/', views.AdminDeleteDoctorView.as_view(), name='admin_delete_doctor'),
    path('admin/doctor/<int:pk>/toggle/', views.AdminToggleDoctorActiveView.as_view(), name='admin_toggle_doctor'),
    path('admin/appointment/<int:pk>/confirm/', views.AdminConfirmView.as_view(), name='admin_confirm'),
    path('admin/appointment/<int:pk>/cancel/', views.AdminCancelView.as_view(), name='admin_cancel'),
    path('admin/appointment/<int:pk>/complete/', views.AdminCompleteView.as_view(), name='admin_complete'),
]

