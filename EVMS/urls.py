from django.contrib import admin
from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

urlpatterns = [
    path('',home_view,name = 'home_view'),
    path('vendor-signup/',vendor_signup,name = 'vendor_signup'),
    path('vendor-login/',vendor_login,name = 'vendor_login'),
    path('vendor-logout/', vendor_logout, name='vendor_logout'),
    path('vendor-dashboard/',vendor_dashboard,name = 'vendor_dashboard'),
    path('vendor-profile/<int:id>/',vendor_profile,name = 'vendor_profile'),
    path('candidateform/', candidate_form, name='candidate_form'),
    path("bulk-upload/", bulk_upload_candidates, name="bulk_upload_candidates"),
    path("download-sample/", download_sample_excel, name="download_sample_excel"),
    path('term-and-conditions/', term_and_conditions, name='term_and_conditions'),
    path('thankyou/', thankyou, name='thankyou'),
    path('api/revenue-data/', revenue_data, name='revenue_data'),
    path('candidate-profile/<int:id>/', candidate_profile_details, name='candidate_profile_details'),
    path('selected-candidates/', vendor_selected_candidate, name='vendor_selected_candidate'),
    path('transaction-history/', vendor_transaction_history, name = 'vendor_transaction_history'),
    path('resend-otp/', resend_otp, name='resend_otp'),
    path('vendor/invoice/<int:candidate_id>/', generate_vendor_invoice, name='vendor_invoice'),
    path('notifications/mark-read/<int:pk>/', mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', mark_all_notifications_read, name='mark_all_notifications_read'),
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('reset-password-otp/', reset_password_otp, name='reset_password_otp'),
    path('reset-password/', reset_password_form, name='reset_password_form'),
    path('resend-reset-otp/', resend_reset_otp, name='resend_reset_otp'),
    
    
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)