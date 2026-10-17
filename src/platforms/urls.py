from django.urls import path, include

from . import views

urlpatterns = [
    path('newPlatform/', views.newPlatform, name='newPlatform'),
    path('savePlatformAjax/', views.savePlatformAjax, name='savePlatformAjax'),
    path('platform/<int:pk>', views.platform, name='platform'),
    path('platforms', views.platforms, name='platforms'),
    path('editPlatform/<int:pk>', views.editPlatform, name='editPlatform'),
    path('deletePlatformAjax/<int:pk>', views.deletePlatformAjax, name='deletePlatformAjax'),
    path('platformsAutocompleteSearch/', views.platformsAutocompleteSearch, name='platformsAutocompleteSearch'),
    path('api/', include('platforms.api.urls')),
]
