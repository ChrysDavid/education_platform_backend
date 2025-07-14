from django.urls import path
from .. import views

app_name = 'orientation'

urlpatterns = [
    # Types d'évaluation
    path('assessment-types/', views.AssessmentTypeListView.as_view(), name='assessment_type_list'),
    path('assessment-types/<int:pk>/', views.AssessmentTypeDetailView.as_view(), name='assessment_type_detail'),
    path('assessment-types/create/', views.AssessmentTypeCreateView.as_view(), name='assessment_type_create'),
    path('assessment-types/<int:pk>/update/', views.AssessmentTypeUpdateView.as_view(), name='assessment_type_update'),
    path('assessment-types/<int:pk>/delete/', views.AssessmentTypeDeleteView.as_view(), name='assessment_type_delete'),
    
    # Questions d'évaluation
    path('assessment-types/<int:assessment_type_id>/questions/create/', views.AssessmentQuestionCreateView.as_view(), name='assessment_question_create'),
    path('questions/<int:pk>/update/', views.AssessmentQuestionUpdateView.as_view(), name='assessment_question_update'),
    path('questions/<int:pk>/delete/', views.AssessmentQuestionDeleteView.as_view(), name='assessment_question_delete'),
    
    # Sessions d'évaluation
    path('assessments/create/', views.AssessmentCreateView.as_view(), name='assessment_create'),
    path('assessments/<int:pk>/update/', views.AssessmentUpdateView.as_view(), name='assessment_update'),
    path('assessments/<int:pk>/delete/', views.AssessmentDeleteView.as_view(), name='assessment_delete'),
]