from django.contrib import admin
from .models import Article, Index, ToAnalyzePage


admin.site.register(Index)
admin.site.register(Article)
admin.site.register(ToAnalyzePage)