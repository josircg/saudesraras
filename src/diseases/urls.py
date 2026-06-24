from django.urls import path
from . import views 

urlpatterns = [
    path('diseases/', views.disease_list, name='disease_list'),
    
    path('doencas/', views.disease_list, name='diseases'), 
    
    path('disease/<int:pk>/', views.disease_detail, name='disease_detail'),
]