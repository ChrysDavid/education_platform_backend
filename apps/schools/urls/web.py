from django.urls import path
from ..views.web import (
    SchoolListView, SchoolTypeListView, CityListView,
    SchoolDetailView, DepartmentListView, DepartmentDetailView,
    ProgramListView, ProgramDetailView, FacilityListView,
    SchoolContactListView, SchoolMediaListView, SchoolEventListView,
    SchoolEventDetailView, SchoolReviewListView, SchoolReviewCreateView,
    SchoolReviewUpdateView, SchoolReviewDeleteView, SchoolSearchView,
    SchoolFilterByTypeView, SchoolFilterByCityView
)

app_name = 'schools'

urlpatterns = [
    # Routes pour les écoles
    path('', SchoolListView.as_view(), name='school_list'),
    path('types/', SchoolTypeListView.as_view(), name='school_type_list'),
    path('cities/', CityListView.as_view(), name='city_list'),
    path('<slug:slug>/', SchoolDetailView.as_view(), name='school_detail'),
    path('<slug:slug>/departments/', DepartmentListView.as_view(), name='department_list'),
    path('<slug:school_slug>/departments/<slug:slug>/', DepartmentDetailView.as_view(), name='department_detail'),
    path('<slug:slug>/programs/', ProgramListView.as_view(), name='program_list'),
    path('<slug:school_slug>/programs/<slug:slug>/', ProgramDetailView.as_view(), name='program_detail'),
    path('<slug:slug>/facilities/', FacilityListView.as_view(), name='facility_list'),
    path('<slug:slug>/contacts/', SchoolContactListView.as_view(), name='contact_list'),
    path('<slug:slug>/media/', SchoolMediaListView.as_view(), name='media_list'),
    path('<slug:slug>/events/', SchoolEventListView.as_view(), name='event_list'),
    path('<slug:school_slug>/events/<int:pk>/', SchoolEventDetailView.as_view(), name='event_detail'),

    # Routes pour les avis
    path('<slug:slug>/reviews/', SchoolReviewListView.as_view(), name='review_list'),
    path('<slug:slug>/reviews/add/', SchoolReviewCreateView.as_view(), name='add_review'),
    path('<slug:slug>/reviews/<int:pk>/edit/', SchoolReviewUpdateView.as_view(), name='edit_review'),
    path('<slug:slug>/reviews/<int:pk>/delete/', SchoolReviewDeleteView.as_view(), name='delete_review'),

    # Routes de recherche
    path('search/', SchoolSearchView.as_view(), name='school_search'),
    path('filter/by-type/<slug:type_slug>/', SchoolFilterByTypeView.as_view(), name='filter_by_type'),
    path('filter/by-city/<int:city_id>/', SchoolFilterByCityView.as_view(), name='filter_by_city'),
]