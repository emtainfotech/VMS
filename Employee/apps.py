from django.apps import AppConfig

class EmployeeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Employee'

    def ready(self):
        # This line imports and connects the signals when the app is ready.
        import Employee.signals
