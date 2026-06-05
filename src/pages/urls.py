from django.urls import path

from . import views

urlpatterns = [
    path('<slug:slug>/', views.PageDetailView.as_view(), name='page_detail'),
]
