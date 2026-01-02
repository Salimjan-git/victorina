from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *
from .forms import CustomUserCreationForm

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    list_display = ['username', 'email', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'email']
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Маълумоти шахсӣ', {'fields': ('first_name', 'last_name', 'email')}),
        ('Ҳуқуқҳо', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Таърихҳои воридшавӣ', {'fields': ('last_login', 'date_joined', 'created_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )
    readonly_fields = ['created_at']

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Профил'

class GroupMemberInline(admin.TabularInline):
    model = GroupMember
    extra = 1

class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'leader', 'created_at']
    list_filter = ['subject', 'created_at']
    search_fields = ['name', 'leader__username']
    inlines = [GroupMemberInline]

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ['text', 'question_type', 'points', 'order']

class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'quiz_mode', 'status', 'start_time', 'end_time', 'created_by']
    list_filter = ['quiz_mode', 'status', 'level_type', 'created_at']
    search_fields = ['title', 'description', 'created_by__username']
    inlines = [QuestionInline]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(created_by=request.user)

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 4

class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'quiz', 'question_type', 'points', 'order']
    list_filter = ['question_type', 'quiz']
    search_fields = ['text']
    inlines = [AnswerInline]

class ResultAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'user', 'score', 'total_questions', 'correct_answers', 'percentage', 'completed_at']
    list_filter = ['quiz', 'completed_at']
    search_fields = ['user__username', 'quiz__title']
    
    def percentage(self, obj):
        return f"{obj.percentage():.1f}%"

# Register models
admin.site.register(User, CustomUserAdmin)
admin.site.register(Profile)
admin.site.register(Subject)
admin.site.register(Group, GroupAdmin)
admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer)
admin.site.register(QuizSession)
admin.site.register(UserAnswer)
admin.site.register(Result, ResultAdmin)
admin.site.register(Rating)
admin.site.register(Permission)
admin.site.register(AuditLog)