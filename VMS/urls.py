
from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path('', include('EVMS.urls')),
    path('hrms/', include('App.urls')),
    path('employee/', include('Employee.urls')),
    path('admin/', admin.site.urls),
]