from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.contrib import admin
from .views import *

urlpatterns = [
    path('', resume,name='resume'),
    path('resume-cover-letter/', resume,name='resume_cover'),
    path('upload-resume/', upload_resume,name='upload_resume'),
    path('upload-cover/', upload_cover,name='upload_cover'),
    path('resume/', resume_list,name='resume_list'),
    path('cover/', cover_list,name='cover_list'),
    path('resume/details/<int:id>/', product_details, name='details'),
    path('cover/details/<int:id>/', cover_details, name='cover_details'),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
