from django.urls import path
from . import views
urlpatterns = [
    path('new_<slug:page_slug>/', views.new_section_generic, name='new_section_generic'),
    path('edit_page/<slug:page_slug>/', views.edit_page_generic, name='edit_page_generic'),
    path('<slug:page_slug>/section/<int:section_id>/new_article/', views.new_article_generic, name='new_article_generic'),
    path('<slug:page_slug>/section/<int:section_id>/edit_article/<int:article_id>/', views.edit_article_generic, name='edit_article_generic'),
    path('<slug:page_slug>/section/<int:section_id>/article/<int:article_id>/', views.article_detail, name='article_detail'),
    path('<slug:page_slug>/edit/<int:section_id>/', views.edit_section_generic, name='edit_section_generic'),
    path('<slug:page_slug>/detail/<int:section_id>/', views.section_detail, name='section_detail'),
    path('depoimentos/', views.DepoimentosListView.as_view(), name='depoimentos'),
    path('<slug:slug>/', views.PageDetailView.as_view(), name='page_detail'),
    
]