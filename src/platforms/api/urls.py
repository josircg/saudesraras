from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'geographicextend', views.GeographicExtendViewSet)
router.register(r'platforms', views.PlatformViewSet)
urlpatterns = router.urls
