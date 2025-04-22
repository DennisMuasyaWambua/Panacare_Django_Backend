from rest_framework import viewsets, permissions
from .models import HealthCare
from .serializers import HealthCareSerializer

class HealthCareViewSet(viewsets.ModelViewSet):
    queryset = HealthCare.objects.all()
    serializer_class = HealthCareSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = HealthCare.objects.all()
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)
        active = self.request.query_params.get('active')
        if active:
            queryset = queryset.filter(is_active=active.lower() == 'true')
        return queryset
