from django.db import models
from research_library.models import ThesisPaper

class PaperEmbedding(models.Model):
    id = models.AutoField(primary_key=True)
    paper = models.OneToOneField(ThesisPaper, on_delete=models.CASCADE, related_name='embedding')
    sbert_embedding = models.JSONField(blank=True, null=True)
    umap_x_coord = models.FloatField(blank=True, null=True)
    umap_y_coord = models.FloatField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Embedding for: {self.paper.title}"