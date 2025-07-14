from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, filters
from ..models import SchoolType, City, School, SchoolReview
from ..serializers import (
    SchoolTypeSerializer, CitySerializer, 
    SchoolListSerializer, SchoolDetailSerializer,
    SchoolReviewSerializer
)


class SchoolAPIListView(generics.ListAPIView):
    serializer_class = SchoolListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'city__name', 'school_type__name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        queryset = School.objects.filter(is_active=True).select_related(
            'school_type', 'city'
        )
        
        school_type = self.request.query_params.get('type')
        if school_type:
            queryset = queryset.filter(school_type__slug=school_type)
        
        city = self.request.query_params.get('city')
        if city:
            queryset = queryset.filter(city__id=city)
        
        verified = self.request.query_params.get('verified')
        if verified:
            queryset = queryset.filter(is_verified=True)
        
        return queryset


class SchoolAPIDetailView(generics.RetrieveAPIView):
    queryset = School.objects.filter(is_active=True)
    serializer_class = SchoolDetailSerializer


class SchoolReviewAPIListView(generics.ListCreateAPIView):
    serializer_class = SchoolReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        school = get_object_or_404(School, pk=self.kwargs['pk'], is_active=True)
        return SchoolReview.objects.filter(
            school=school, is_public=True
        ).select_related('user').order_by('-created_at')
    
    def perform_create(self, serializer):
        school = get_object_or_404(School, pk=self.kwargs['pk'], is_active=True)
        serializer.save(user=self.request.user, school=school, is_public=True)


class CityAPIListView(generics.ListAPIView):
    queryset = City.objects.filter(is_active=True)
    serializer_class = CitySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'region']


class SchoolTypeAPIListView(generics.ListAPIView):
    queryset = SchoolType.objects.all()
    serializer_class = SchoolTypeSerializer