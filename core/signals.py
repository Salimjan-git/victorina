from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Profile, Quiz, AuditLog

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):

    if created:
        Profile.objects.create(
            user=instance,
            level_type='school' if instance.role == 'student' else 'university',
            current_level=1
        )
        AuditLog.objects.create(
            user=instance,
            action='create',
            model='User',
            object_id=str(instance.id),
            details={'username': instance.username, 'role': instance.role}
        )

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):

    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(
            user=instance,
            level_type='school' if instance.role == 'student' else 'university',
            current_level=1
        )

@receiver(pre_save, sender=Quiz)
def update_quiz_status(sender, instance, **kwargs):

    now = timezone.now()
    
    if instance.start_time <= now <= instance.end_time:
        instance.status = 'active'
    elif now > instance.end_time and instance.status != 'finished':
        instance.status = 'finished'
    elif now < instance.start_time and instance.status == 'draft':
        instance.status = 'published'

@receiver(post_save, sender=Quiz)
def log_quiz_changes(sender, instance, created, **kwargs):

    action = 'create' if created else 'update'
    AuditLog.objects.create(
        user=instance.created_by,
        action=action,
        model='Quiz',
        object_id=str(instance.id),
        details={
            'title': instance.title,
            'status': instance.status,
            'quiz_mode': instance.quiz_mode
        }
    )