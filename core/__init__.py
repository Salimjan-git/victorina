import django

if django.apps.apps.ready:
    from . import signals
    

default_app_config = 'core.apps.CoreConfig'