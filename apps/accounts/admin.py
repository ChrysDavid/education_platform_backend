from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Student, Teacher, Pupil, Advisor, Administrator

class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'type', 'verification_status', 'is_active', 'is_staff')
    list_filter = ('type', 'verification_status', 'is_active', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'verification_requested_date', 'verification_completed_date')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'phone_number', 'date_of_birth', 'profile_picture')}),
        (_('Address'), {'fields': ('address', 'city', 'postal_code', 'country')}),
        (_('Documents'), {'fields': ('identity_document',)}),
        (_('Preferences'), {'fields': ('communication_preferences', 'languages')}),
        (_('Emergency contact'), {'fields': ('emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relation')}),
        (_('Permissions'), {
            'fields': ('type', 'verification_status', 'verification_notes', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('date_joined', 'verification_requested_date', 'verification_completed_date')}),
        (_('Consents'), {'fields': ('data_processing_consent', 'image_rights_consent')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'type', 'password1', 'password2'),
        }),
    )

    actions = ['approve_users', 'reject_users']

    def approve_users(self, request, queryset):
        updated = queryset.update(verification_status='verified', is_active=True)
        self.message_user(request, f"{updated} utilisateurs ont été approuvés avec succès.")
    approve_users.short_description = _("Approuver les utilisateurs sélectionnés")

    def reject_users(self, request, queryset):
        updated = queryset.update(verification_status='rejected', is_active=False)
        self.message_user(request, f"{updated} utilisateurs ont été rejetés.")
    reject_users.short_description = _("Rejeter les utilisateurs sélectionnés")

class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'institution_name', 'current_level', 'school_id')
    list_filter = ('user__verification_status', 'current_level', 'scholarship')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'institution_name', 'student_id')
    raw_id_fields = ('user',)
    
    fieldsets = (
        (None, {'fields': ('user',)}),
        (_('Academic information'), {'fields': ('school_id', 'institution_name', 'current_level', 'major', 'academic_year', 'student_id', 'average_grade')}),
        (_('Scholarship and housing'), {'fields': ('scholarship', 'scholarship_type', 'housing_needs')}),
        (_('Internship and skills'), {'fields': ('internship_search', 'computer_skills', 'extracurricular_activities')}),
        (_('Interests'), {'fields': ('interests',)}),
    )

class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'institution_name', 'highest_degree', 'years_of_experience')
    list_filter = ('user__verification_status', 'years_of_experience', 'institution_name')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'institution_name', 'professional_license')
    raw_id_fields = ('user',)
    
    fieldsets = (
        (None, {'fields': ('user',)}),
        (_('Professional information'), {'fields': ('school_id', 'institution_name', 'subjects', 'highest_degree', 'degree_document', 'years_of_experience')}),
        (_('Teaching details'), {'fields': ('teaching_type', 'qualifications', 'professional_license', 'expertise_areas')}),
        (_('Documents'), {'fields': ('cv',)}),
        (_('Availability'), {'fields': ('availability',)}),
        (_('Professional development'), {'fields': ('continuous_education', 'professional_references')}),
    )

class PupilAdmin(admin.ModelAdmin):
    list_display = ('user', 'school_name', 'current_level')
    list_filter = ('user__verification_status', 'current_level', 'cafeteria', 'school_transport')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'school_name')
    raw_id_fields = ('user',)
    
    fieldsets = (
        (None, {'fields': ('user',)}),
        (_('School information'), {'fields': ('school_name', 'current_level', 'specialization')}),
        (_('Legal guardians'), {'fields': ('legal_guardian_name', 'legal_guardian_phone', 'second_guardian_name', 'second_guardian_phone')}),
        (_('School services'), {'fields': ('cafeteria', 'dietary_restrictions', 'school_transport', 'transport_details')}),
        (_('Medical information'), {'fields': ('medical_information', 'school_insurance')}),
        (_('Permissions and activities'), {'fields': ('exit_permissions', 'siblings_at_school', 'desired_activities')}),
    )

class AdvisorAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'specialization', 'years_of_experience')
    list_filter = ('user__verification_status', 'years_of_experience', 'organization')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'organization', 'professional_license')
    raw_id_fields = ('user',)
    
    fieldsets = (
        (None, {'fields': ('user',)}),
        (_('Professional information'), {'fields': ('organization', 'specialization', 'years_of_experience', 'professional_license')}),
        (_('Certifications'), {'fields': ('certifications', 'certification_documents')}),
        (_('Working areas'), {'fields': ('geographical_areas', 'rates')}),
        (_('Portfolio'), {'fields': ('portfolio', 'portfolio_link', 'publications')}),
        (_('Availability'), {'fields': ('availability',)}),
    )

class AdministratorAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'department')
    list_filter = ('user__verification_status', 'department', 'administrative_level')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'role')
    raw_id_fields = ('user',)
    
    fieldsets = (
        (None, {'fields': ('user',)}),
        (_('Administrative information'), {'fields': ('role', 'department', 'administrative_level')}),
        (_('Responsibilities'), {'fields': ('responsibilities',)}),
    )

# Enregistrement des modèles
admin.site.register(User, UserAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Teacher, TeacherAdmin)
admin.site.register(Pupil, PupilAdmin)
admin.site.register(Advisor, AdvisorAdmin)
admin.site.register(Administrator, AdministratorAdmin)