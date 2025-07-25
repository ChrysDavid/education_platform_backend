# Generated by Django 5.2 on 2025-05-07 19:43

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_user_verification_completed_date_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='teacher',
            options={'ordering': ['-user__date_joined'], 'verbose_name': 'enseignant', 'verbose_name_plural': 'enseignants'},
        ),
        migrations.AddField(
            model_name='teacher',
            name='approval_date',
            field=models.DateField(blank=True, help_text='Date à laquelle le profil a été approuvé', null=True, verbose_name="date d'approbation"),
        ),
        migrations.AddField(
            model_name='teacher',
            name='hourly_rate',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Tarif horaire pour les cours particuliers', max_digits=6, null=True, verbose_name='tarif horaire'),
        ),
        migrations.AddField(
            model_name='teacher',
            name='is_approved',
            field=models.BooleanField(default=False, help_text="Indique si le profil a été approuvé par l'administration", verbose_name='approuvé'),
        ),
        migrations.AddField(
            model_name='teacher',
            name='teaching_philosophy',
            field=models.TextField(blank=True, help_text="Description de l'approche pédagogique", verbose_name="philosophie d'enseignement"),
        ),
        migrations.AlterField(
            model_name='teacher',
            name='availability',
            field=models.JSONField(blank=True, default=dict, help_text='Disponibilités hebdomadaires pour les cours', verbose_name='disponibilités horaires'),
        ),
        migrations.AlterField(
            model_name='teacher',
            name='continuous_education',
            field=models.JSONField(blank=True, default=list, help_text='Liste des formations continues ou certifications récentes', verbose_name='formations continues suivies'),
        ),
        migrations.AlterField(
            model_name='teacher',
            name='cv',
            field=models.FileField(blank=True, help_text='Curriculum Vitae du professeur', null=True, upload_to='teacher_cvs/%Y/%m/%d/', validators=[django.core.validators.FileExtensionValidator(['pdf', 'doc', 'docx'])], verbose_name='CV complet'),
        ),
        migrations.AlterField(
            model_name='teacher',
            name='degree_document',
            field=models.FileField(blank=True, help_text='Document scanné du diplôme (PDF ou image)', null=True, upload_to='teacher_degrees/%Y/%m/%d/', validators=[django.core.validators.FileExtensionValidator(['pdf', 'png', 'jpg', 'jpeg'])], verbose_name='document du diplôme'),
        ),
        migrations.AlterField(
            model_name='teacher',
            name='expertise_areas',
            field=models.JSONField(blank=True, default=list, help_text='Domaines de spécialisation ou expertises particulières', verbose_name="domaines d'expertise"),
        ),
        migrations.AlterField(
            model_name='teacher',
            name='highest_degree',
            field=models.CharField(help_text='Dernier diplôme académique obtenu', max_length=255, verbose_name='diplôme le plus élevé obtenu'),
        ),
        migrations.AlterField(
            model_name='teacher',
            name='institution_name',
            field=models.CharField(help_text="Nom de l'établissement d'enseignement", max_length=255, verbose_name='établissement où il enseigne'),
        ),
        migrations.AlterField(
            model_name='teacher',
            name='professional_license',
            field=models.CharField(blank=True, help_text="Numéro d'agrément ou licence d'enseignement", max_length=100, verbose_name='numéro de licence professionnelle'),
        ),
        migrations.AlterField(
            model_name='teacher',
            name='professional_references',
            field=models.TextField(blank=True, help_text='Contacts ou références professionnelles', verbose_name='références professionnelles'),
        ),
        migrations.AlterField(
            model_name='teacher',
            name='qualifications',
            field=models.CharField(help_text='Qualifications pédagogiques spécifiques', max_length=255, verbose_name='qualifications'),
        ),
        migrations.AlterField(
            model_name='teacher',
            name='school_id',
            field=models.PositiveIntegerField(blank=True, help_text="ID de l'établissement scolaire dans le système", null=True, verbose_name="ID de l'école"),
        ),
        migrations.AlterField(
            model_name='teacher',
            name='subjects',
            field=models.JSONField(default=list, help_text='Liste des matières enseignées par le professeur', verbose_name='matières enseignées'),
        ),
        migrations.AlterField(
            model_name='teacher',
            name='teaching_type',
            field=models.JSONField(default=list, help_text="Types d'enseignement proposés (présentiel, en ligne, hybride)", verbose_name="type d'enseignement"),
        ),
        migrations.AlterField(
            model_name='teacher',
            name='years_of_experience',
            field=models.PositiveIntegerField(default=0, help_text="Nombre d'années d'expérience dans l'enseignement", validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(70)], verbose_name="années d'expérience en enseignement"),
        ),
        migrations.AddIndex(
            model_name='teacher',
            index=models.Index(fields=['institution_name'], name='accounts_te_institu_fc381a_idx'),
        ),
        migrations.AddIndex(
            model_name='teacher',
            index=models.Index(fields=['highest_degree'], name='accounts_te_highest_df8a4c_idx'),
        ),
    ]
