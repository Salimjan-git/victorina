from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Маълумоти шахсӣ', {'fields': ('first_name', 'last_name', 'email')}),
        ('Ҳуқуқҳо', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Давраҳои воридшавӣ', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'level_type', 'current_level']
    list_filter = ['level_type']
    search_fields = ['user__username', 'user__email']

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'level_type', 'is_public', 'created_at']
    list_filter = ['level_type', 'is_public']
    search_fields = ['name', 'code', 'description']
    filter_horizontal = []

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'leader', 'created_at']
    list_filter = ['subject', 'created_at']
    search_fields = ['name', 'subject__name']

@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ['group', 'user', 'joined_at']
    list_filter = ['joined_at']
    search_fields = ['group__name', 'user__username']

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'quiz_mode', 'status', 'start_time', 'end_time']
    list_filter = ['quiz_mode', 'status', 'level_type', 'created_at']
    search_fields = ['title', 'description', 'subject__name']
    date_hierarchy = 'created_at'

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'quiz', 'question_type', 'points', 'order']
    list_filter = ['question_type']
    search_fields = ['text', 'quiz__title']

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['text', 'question', 'is_correct']
    list_filter = ['is_correct']
    search_fields = ['text', 'question__text']

@admin.register(QuizSession)
class QuizSessionAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'user', 'group', 'started_at', 'finished_at']
    list_filter = ['started_at']
    search_fields = ['quiz__title', 'user__username', 'group__name']

@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ['session', 'question', 'answered_at']
    search_fields = ['session__quiz__title', 'question__text']

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'user', 'score', 'total_questions', 'percentage', 'completed_at']
    list_filter = ['completed_at']
    search_fields = ['quiz__title', 'user__username']
    
    def percentage(self, obj):
        return f"{obj.percentage():.1f}%"
    percentage.short_description = 'Фоиз'

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'entity_type', 'get_entity', 'rank', 'score']
    list_filter = ['entity_type', 'quiz']
    search_fields = ['quiz__title', 'user__username', 'group__name']
    
    def get_entity(self, obj):
        return obj.user.username if obj.user else obj.group.name
    get_entity.short_description = 'Ҷониб'

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'codename']
    search_fields = ['name', 'codename']

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'model', 'object_id', 'created_at']
    list_filter = ['action', 'model', 'created_at']
    search_fields = ['user__username', 'model', 'object_id']
    date_hierarchy = 'created_at'