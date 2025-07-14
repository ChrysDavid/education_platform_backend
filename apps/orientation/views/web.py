from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseRedirect
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
import django.db.models as models

from ..models import (
    AssessmentType, AssessmentQuestion, Assessment, AssessmentAnswer,
    SkillCategory, Skill, CareerField, CareerPath, OrientationPath,
    OrientationCareerPath, StudentSkill
)
from ..forms import (
    AssessmentTypeForm, AssessmentQuestionForm, AssessmentForm, AssessmentAnswerForm,
    SkillCategoryForm, SkillForm, CareerFieldForm, CareerPathForm, OrientationPathForm,
    OrientationCareerPathForm, StudentSkillForm, TakeAssessmentForm
)


class IsAdvisorMixin(UserPassesTestMixin):
    """
    Mixin pour vérifier que l'utilisateur est un conseiller.
    """
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.type == 'advisor'
    
    def handle_no_permission(self):
        messages.error(self.request, _("Vous devez être conseiller d'orientation pour accéder à cette page."))
        return redirect('home')


class AssessmentTypeListView(LoginRequiredMixin, IsAdvisorMixin, ListView):
    """
    Liste des types d'évaluation d'orientation.
    """
    model = AssessmentType
    template_name = 'orientation/assessment_type_list.html'
    context_object_name = 'assessment_types'
    
    def get_queryset(self):
        return AssessmentType.objects.all().annotate(
            question_count=models.Count('questions'),
            assessment_count=models.Count('assessments')
        )


class AssessmentTypeDetailView(LoginRequiredMixin, IsAdvisorMixin, DetailView):
    """
    Détails d'un type d'évaluation.
    """
    model = AssessmentType
    template_name = 'orientation/assessment_type_detail.html'
    context_object_name = 'assessment_type'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['questions'] = AssessmentQuestion.objects.filter(
            assessment_type=self.object
        ).order_by('order')
        return context


class AssessmentTypeCreateView(LoginRequiredMixin, IsAdvisorMixin, CreateView):
    """
    Création d'un type d'évaluation.
    """
    model = AssessmentType
    form_class = AssessmentTypeForm
    template_name = 'orientation/assessment_type_form.html'
    success_url = reverse_lazy('orientation:assessment_type_list')
    
    def form_valid(self, form):
        messages.success(self.request, _("Le type d'évaluation a été créé avec succès."))
        return super().form_valid(form)


class AssessmentTypeUpdateView(LoginRequiredMixin, IsAdvisorMixin, UpdateView):
    """
    Modification d'un type d'évaluation.
    """
    model = AssessmentType
    form_class = AssessmentTypeForm
    template_name = 'orientation/assessment_type_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, _("Le type d'évaluation a été mis à jour avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('orientation:assessment_type_detail', kwargs={'pk': self.object.pk})


class AssessmentTypeDeleteView(LoginRequiredMixin, IsAdvisorMixin, DeleteView):
    """
    Suppression d'un type d'évaluation.
    """
    model = AssessmentType
    template_name = 'orientation/assessment_type_confirm_delete.html'
    success_url = reverse_lazy('orientation:assessment_type_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _("Le type d'évaluation a été supprimé avec succès."))
        return super().delete(request, *args, **kwargs)


class AssessmentQuestionCreateView(LoginRequiredMixin, IsAdvisorMixin, CreateView):
    """
    Création d'une question d'évaluation.
    """
    model = AssessmentQuestion
    form_class = AssessmentQuestionForm
    template_name = 'orientation/assessment_question_form.html'
    
    def get_initial(self):
        initial = super().get_initial()
        assessment_type_id = self.kwargs.get('assessment_type_id')
        if assessment_type_id:
            initial['assessment_type'] = assessment_type_id
            
            # Calculer l'ordre suivant
            last_question = AssessmentQuestion.objects.filter(
                assessment_type_id=assessment_type_id
            ).order_by('-order').first()
            
            if last_question:
                initial['order'] = last_question.order + 1
            else:
                initial['order'] = 0
        
        return initial
    
    def form_valid(self, form):
        messages.success(self.request, _("La question a été créée avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('orientation:assessment_type_detail', kwargs={'pk': self.object.assessment_type.pk})


class AssessmentQuestionUpdateView(LoginRequiredMixin, IsAdvisorMixin, UpdateView):
    """
    Modification d'une question d'évaluation.
    """
    model = AssessmentQuestion
    form_class = AssessmentQuestionForm
    template_name = 'orientation/assessment_question_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, _("La question a été mise à jour avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('orientation:assessment_type_detail', kwargs={'pk': self.object.assessment_type.pk})


class AssessmentQuestionDeleteView(LoginRequiredMixin, IsAdvisorMixin, DeleteView):
    """
    Suppression d'une question d'évaluation.
    """
    model = AssessmentQuestion
    template_name = 'orientation/assessment_question_confirm_delete.html'
    
    def get_success_url(self):
        return reverse('orientation:assessment_type_detail', kwargs={'pk': self.object.assessment_type.pk})
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _("La question a été supprimée avec succès."))
        return super().delete(request, *args, **kwargs)


class AssessmentCreateView(LoginRequiredMixin, IsAdvisorMixin, CreateView):
    """
    Création d'une évaluation.
    """
    model = Assessment
    form_class = AssessmentForm
    template_name = 'orientation/assessment_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request_user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, _("L'évaluation a été créée avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('orientation:assessment_detail', kwargs={'pk': self.object.pk})


class AssessmentUpdateView(LoginRequiredMixin, IsAdvisorMixin, UpdateView):
    """
    Modification d'une évaluation.
    """
    model = Assessment
    form_class = AssessmentForm
    template_name = 'orientation/assessment_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request_user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, _("L'évaluation a été mise à jour avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('orientation:assessment_detail', kwargs={'pk': self.object.pk})


class AssessmentDeleteView(LoginRequiredMixin, IsAdvisorMixin, DeleteView):
    """
    Suppression d'une évaluation.
    """
    model = Assessment
    template_name = 'orientation/assessment_confirm_delete.html'
    success_url = reverse_lazy('orientation:assessment_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _("L'évaluation a été supprimée avec succès."))
        return super().delete(request, *args, **kwargs)