from django.apps import AppConfig
import threading
import os


class ContentConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "content"
  

    def ready(self):
        if os.environ.get("RUN_MAIN") != "true":
            # Avoid running twice during Django dev autoreload
            return

        from .functions import run_drive_sync

        threading.Thread(target=run_drive_sync, daemon=True).start()