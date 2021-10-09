from django.urls import path
from . import views

app_name = 'search_engine'

urlpatterns = [
  path('search/', views.SearchView.as_view(), name='search'),
  path('crawler_settings/', views.CrawlerSettingsView.as_view(), name='crawler_settings'),
  path('crawler_settings/start_crawling/', views.start_crawling, name='start_crawling'),
]
