from platforms.models import GeographicExtend, Platform
from rest_framework.viewsets import ReadOnlyModelViewSet

from .serializers import GeographicExtendSerializer, PlatformSerializer


class GeographicExtendViewSet(ReadOnlyModelViewSet):
    serializer_class = GeographicExtendSerializer
    queryset = GeographicExtend.objects.all()


class PlatformViewSet(ReadOnlyModelViewSet):
    serializer_class = PlatformSerializer
    queryset = Platform.objects.all()
