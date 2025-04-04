from django.contrib import admin
from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

urlpatterns = [
    path('',vendor_signup,name = 'vendor_signup'),
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
    
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)