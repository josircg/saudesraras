from django.urls import path

from . import views
urlpatterns = [
    path('depoimentos/', views.DepoimentosListView.as_view(), name='depoimentos'),
    path('<slug:slug>/', views.PageDetailView.as_view(), name='page_detail'),
]
