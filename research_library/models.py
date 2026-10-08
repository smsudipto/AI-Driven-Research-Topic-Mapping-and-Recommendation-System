from django.db import models

class ThesisPaper(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    abstract = models.TextField()
    authors = models.CharField(max_length=255)
    supervisor_name = models.CharField(max_length=150)
    domain = models.CharField(max_length=100)
    publication_year = models.IntegerField()
    pdf_file = models.FileField(upload_to='thesis_papers/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.publication_year})"