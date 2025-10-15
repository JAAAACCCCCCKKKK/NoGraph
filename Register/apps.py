from django.apps import AppConfig

def ready(self):
    import Register.signals

class RegisterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Register'


