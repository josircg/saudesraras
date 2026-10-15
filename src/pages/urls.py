from django.urls import path
from . import views

urlpatterns = [
    path('depoimentos/', views.DepoimentosListView.as_view(), name='depoimentos'),
    path('depoimentos/novo/', views.DepoimentoCreateView.as_view(), name='novo_depoimento'),
    path('depoimentos/editar/<int:pk>/', views.DepoimentoUpdateView.as_view(), name='editar_depoimento'),
    path('<slug:slug>/', views.PageDetailView.as_view(), name='page_detail'),
]