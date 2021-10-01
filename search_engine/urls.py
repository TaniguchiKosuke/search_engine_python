from django.urls import path
from . import views

app_name = 'search_engine'

urlpatterns = [
  path('', views.SearchView.as_view(), name='search'),
]
