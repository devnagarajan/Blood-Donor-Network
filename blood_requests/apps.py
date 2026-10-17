from django.apps import AppConfig


class BloodRequestsConfig(AppConfig):
    name = 'blood_requests'
    default_auto_field = 'django.db.models.BigAutoField'
    
    def ready(self):
        """Import signals when app is ready"""
        import blood_requests.signals
