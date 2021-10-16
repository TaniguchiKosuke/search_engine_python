from django.contrib import admin
from .models import Article, Index


admin.site.register(Index)
admin.site.register(Article)