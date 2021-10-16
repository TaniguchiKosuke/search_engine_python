from django.db import models
from django.db.models.base import ModelState
from django.utils import timezone

# Create your models here.

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(verbose_name='作成日時', default=timezone.now)
    modified_at = models.DateTimeField(verbose_name='更新日時', auto_now=True)
    deleted_at = models.DateTimeField(verbose_name='削除日時', default=timezone.now)

    class Meta:
        abstract = True


class Index(TimeStampedModel):
    keyword = models.TextField()
    # url = models.CharField(max_length=2048)
    index_json = models.JSONField()

    def __str__(self):
        return f'{self.keyword}: {self.index_json}'


class Article(TimeStampedModel):
    title = models.CharField(max_length=1024)
    url = models.URLField()
    content = models.TextField(max_length=1024, null=True, blank=True)

    def __str__(self):
        return f'{self.title}: {self.url}: {self.content}'