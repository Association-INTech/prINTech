from django.apps import AppConfig
from django.db.models.signals import post_migrate

def create_default_printers(sender, **kwargs):
    from .models import Printer 
    
    # Add all printers to the database if they don't exist
    for printer_name in Printer.Name.values:
        Printer.objects.get_or_create(
            name=printer_name,
            defaults={'status': Printer.Status.DOWN} 
        )

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'back.apps.api'

    def ready(self):
            post_migrate.connect(create_default_printers, sender=self)