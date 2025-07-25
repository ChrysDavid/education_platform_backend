# Generated by Django 5.2 on 2025-04-21 12:29

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='nom')),
                ('slug', models.SlugField(max_length=100, unique=True, verbose_name='slug')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('icon', models.CharField(blank=True, max_length=50, verbose_name='icône')),
                ('color', models.CharField(blank=True, help_text='Code couleur hexadécimal', max_length=20, verbose_name='couleur')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='ordre')),
                ('is_active', models.BooleanField(default=True, verbose_name='active')),
                ('requires_verification', models.BooleanField(default=False, help_text='Si activé, seuls les utilisateurs vérifiés peuvent publier dans cette catégorie', verbose_name='nécessite une vérification')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='créée le')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='mise à jour le')),
                ('authorized_groups', models.ManyToManyField(blank=True, help_text='Si spécifié, seuls les membres de ces groupes peuvent voir cette catégorie', to='auth.group', verbose_name='groupes autorisés')),
            ],
            options={
                'verbose_name': 'catégorie',
                'verbose_name_plural': 'catégories',
                'ordering': ['order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(verbose_name='contenu')),
                ('is_hidden', models.BooleanField(default=False, verbose_name='caché')),
                ('is_edited', models.BooleanField(default=False, verbose_name='édité')),
                ('is_solution', models.BooleanField(default=False, help_text='Indique si ce message a été marqué comme solution au sujet', verbose_name='est une solution')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='créé le')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='mis à jour le')),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='forum_posts', to=settings.AUTH_USER_MODEL, verbose_name='auteur')),
            ],
            options={
                'verbose_name': 'message',
                'verbose_name_plural': 'messages',
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='PostReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.TextField(verbose_name='raison')),
                ('status', models.CharField(choices=[('pending', 'En attente'), ('reviewing', 'En cours de revue'), ('resolved', 'Résolu'), ('rejected', 'Rejeté')], default='pending', max_length=10, verbose_name='statut')),
                ('resolution_notes', models.TextField(blank=True, verbose_name='notes de résolution')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='créé le')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='mis à jour le')),
                ('handled_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='handled_forum_reports', to=settings.AUTH_USER_MODEL, verbose_name='traité par')),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reports', to='forum.post', verbose_name='message')),
                ('reporter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='forum_reports', to=settings.AUTH_USER_MODEL, verbose_name='signaleur')),
            ],
            options={
                'verbose_name': 'signalement',
                'verbose_name_plural': 'signalements',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='titre')),
                ('slug', models.SlugField(max_length=255, verbose_name='slug')),
                ('status', models.CharField(choices=[('open', 'Ouvert'), ('closed', 'Fermé'), ('pinned', 'Épinglé'), ('hidden', 'Caché')], default='open', max_length=10, verbose_name='statut')),
                ('tags', models.JSONField(blank=True, default=list, verbose_name='tags')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='créé le')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='mis à jour le')),
                ('last_activity_at', models.DateTimeField(auto_now_add=True, verbose_name='dernière activité le')),
                ('view_count', models.PositiveIntegerField(default=0, verbose_name='nombre de vues')),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='forum_topics', to=settings.AUTH_USER_MODEL, verbose_name='auteur')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='topics', to='forum.category', verbose_name='catégorie')),
            ],
            options={
                'verbose_name': 'sujet',
                'verbose_name_plural': 'sujets',
                'ordering': ['-last_activity_at'],
                'unique_together': {('category', 'slug')},
            },
        ),
        migrations.AddField(
            model_name='post',
            name='topic',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='forum.topic', verbose_name='sujet'),
        ),
        migrations.CreateModel(
            name='PostReaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reaction', models.CharField(max_length=50, verbose_name='réaction')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='créé le')),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reactions', to='forum.post', verbose_name='message')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='forum_reactions', to=settings.AUTH_USER_MODEL, verbose_name='utilisateur')),
            ],
            options={
                'verbose_name': 'réaction',
                'verbose_name_plural': 'réactions',
                'unique_together': {('post', 'user', 'reaction')},
            },
        ),
        migrations.CreateModel(
            name='TopicSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='créé le')),
                ('notify_on_new_post', models.BooleanField(default=True, verbose_name='notifier pour les nouveaux messages')),
                ('topic', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to='forum.topic', verbose_name='sujet')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='forum_subscriptions', to=settings.AUTH_USER_MODEL, verbose_name='utilisateur')),
            ],
            options={
                'verbose_name': 'abonnement',
                'verbose_name_plural': 'abonnements',
                'unique_together': {('topic', 'user')},
            },
        ),
        migrations.CreateModel(
            name='TopicView',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('viewed_at', models.DateTimeField(auto_now=True, verbose_name='consulté le')),
                ('topic', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='views', to='forum.topic', verbose_name='sujet')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='forum_views', to=settings.AUTH_USER_MODEL, verbose_name='utilisateur')),
            ],
            options={
                'verbose_name': 'vue de sujet',
                'verbose_name_plural': 'vues de sujets',
                'unique_together': {('topic', 'user')},
            },
        ),
    ]
