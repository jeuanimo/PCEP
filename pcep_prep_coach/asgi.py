"""ASGI config for pcep_prep_coach."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pcep_prep_coach.settings")

application = get_asgi_application()
