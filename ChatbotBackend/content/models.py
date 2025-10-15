from django.db import models


class PDFDocument(models.Model):
    name = models.CharField(max_length=255)
    drive_file_id = models.CharField(max_length=255, unique=True)  
    uploaded_at = models.DateTimeField(auto_now_add=True)
    local_path = models.TextField(null=True, blank=True) 
    is_downloaded = models.BooleanField(default=False) 
    is_parsed = models.BooleanField(default=False) 
    def __str__(self):
        return self.name

