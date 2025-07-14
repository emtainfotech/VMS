from django.contrib import admin
from django.urls import path
from django.http import HttpResponseNotFound

def fallback_view(request):
    return HttpResponseNotFound("Invalid subdomain or route.")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', fallback_view),  # Acts as a fallback if no subdomain matched
]
