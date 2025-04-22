from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Doctor
from .serializers import DoctorSerializer

class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Doctor.objects.all()
        specialty = self.request.query_params.get('specialty')
        if specialty:
            queryset = queryset.filter(specialty__icontains=specialty)
        available = self.request.query_params.get('available')
        if available:
            queryset = queryset.filter(is_available=available.lower() == 'true')
        return queryset
        
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
