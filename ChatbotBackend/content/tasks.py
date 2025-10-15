from celery import shared_task
from .functions import store_pdf_metadata_bulk

@shared_task
def sync_drive_data():
    store_pdf_metadata_bulk()
