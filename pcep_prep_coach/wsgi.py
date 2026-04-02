"""WSGI config for pcep_prep_coach."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pcep_prep_coach.settings")

application = get_wsgi_application()
