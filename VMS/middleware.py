from django.urls import resolve, set_urlconf
from django.urls import path, include
from django.http import HttpResponse

def get_urls_for_subdomain(subdomain):
    if subdomain in ["127", "localhost", "emtavms"]:  # ← handles dev/local/emtavms.com
        from EVMS import urls as evms_urls
        return evms_urls
    elif subdomain == "hrms":
        from App import urls as app_urls
        return app_urls
    elif subdomain == "employee":
        from Employee import urls as employee_urls
        return employee_urls
    elif subdomain == "crm":
        from CRM import urls as crm_urls
        return crm_urls
    else:
        return None



class SubdomainRoutingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0]  # removes port
        subdomain = host.split('.')[0]          # gets first part

        request.subdomain = subdomain

        urls_module = get_urls_for_subdomain(subdomain)
        if urls_module:
            set_urlconf(urls_module)  # ✅ set the module, not a list
        return self.get_response(request)


