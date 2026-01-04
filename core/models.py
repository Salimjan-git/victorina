# core/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Админ'),
        ('teacher', 'Муаллим'),
        ('student', 'Талаба'),
        ('group_leader', 'Сарвари гурӯҳ'),
    )
    
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Истифодабаранда'
        verbose_name_plural = 'Истифодабарандагон'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def save(self, *args, **kwargs):
        """
        Ҳангоми захира кардани корбар, санҷед ки профил вуҷуд дорад ё не
        """
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            from .models import Profile 
            Profile.objects.get_or_create(
                user=self,
                defaults={
                    'level_type': 'school' if self.role == 'student' else 'university',
                    'current_level': 1
                }
            )
    
    def get_or_create_profile(self):
        
        from .models import Profile  # Import дар дохили функсия
        profile, created = Profile.objects.get_or_create(
            user=self,
            defaults={
                'level_type': 'school' if self.role == 'student' else 'university',
                'current_level': 1
            }
        )
        return profile


class Profile(models.Model):
    LEVEL_TYPE_CHOICES = (
        ('school', 'Мактаб'),
        ('university', 'Донишгоҳ'),
    )
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile',
        verbose_name="Корбар"
    )
    level_type = models.CharField(
        max_length=20, 
        choices=LEVEL_TYPE_CHOICES,
        default='school',
        verbose_name="Навъи таҳсил"
    )
    current_level = models.IntegerField(
        default=1,
        help_text="Синф (1-11) ё курс (1-4)",
        verbose_name="Синф/Курс"
    )
    
    class Meta:
        verbose_name = 'Профил'
        verbose_name_plural = 'Профилҳо'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_level_type_display()} {self.current_level}"
    
    @property
    def level_display(self):
        
        if self.level_type == 'school':
            return f"Синфи {self.current_level}"
        else:
            return f"Курси {self.current_level}"
        
        
class Subject(models.Model):
    LEVEL_TYPE_CHOICES = (
        ('school', 'Мактаб'),
        ('university', 'Донишгоҳ'),
    )
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True, null=True)
    grade_level = models.CharField(max_length=20, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=7, default="#4361ee")
    icon = models.CharField(max_length=50, default="fas fa-book")
    is_public = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=False)
    max_students = models.PositiveIntegerField(default=0)
    pass_percentage = models.PositiveIntegerField(default=60)
    prerequisites = models.TextField(blank=True, null=True)
    level_type = models.CharField(max_length=20, choices=LEVEL_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Фан'
        verbose_name_plural = 'Фанҳо'
        unique_together = ['name', 'level_type']
    
    def __str__(self):
        return f"{self.name} ({self.get_level_type_display()})"
    


class Group(models.Model):
    name = models.CharField(max_length=100)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='groups')
    leader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='led_groups')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Гурӯҳ'
        verbose_name_plural = 'Гурӯҳҳо'
    
    def __str__(self):
        return f"{self.name} ({self.subject.name})"


class GroupMember(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_memberships')
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Аъзои гурӯҳ'
        verbose_name_plural = 'Аъзои гурӯҳҳо'
        unique_together = ['group', 'user']
    
    def __str__(self):
        return f"{self.user.username} in {self.group.name}"


# core/models.py - обновите класс Quiz
class Quiz(models.Model):
    MODE_CHOICES = (
        ('individual', 'Индивидуалӣ'),
        ('group', 'Гурӯҳӣ'),
    )
    
    LEVEL_TYPE_CHOICES = (
        ('school', 'Мактаб'),
        ('university', 'Донишгоҳ'),
    )
    
    STATUS_CHOICES = (
        ('draft', 'Навишта'),
        ('published', 'Нашршуда'),
        ('active', 'Фаъол'),
        ('finished', 'Анҷомёфта'),
    )
    
    title = models.CharField(max_length=200, verbose_name="Сарлавҳа")
    description = models.TextField(blank=True, verbose_name="Тавсиф")
    # Делаем subject необязательным
    subject = models.ForeignKey(
        Subject, 
        on_delete=models.SET_NULL,  # Изменяем на SET_NULL
        related_name='quizzes', 
        verbose_name="Фан",
        null=True,  # Добавляем null
        blank=True  # Добавляем blank
    )
    quiz_mode = models.CharField(max_length=20, choices=MODE_CHOICES, verbose_name="Реҷаи викторина")
    level_type = models.CharField(max_length=20, choices=LEVEL_TYPE_CHOICES, verbose_name="Навъи сатҳ")
    start_level = models.IntegerField(verbose_name="Сатҳи оғоз")
    end_level = models.IntegerField(verbose_name="Сатҳи анҷом")
    start_time = models.DateTimeField(verbose_name="Вақти оғоз")
    end_time = models.DateTimeField(verbose_name="Вақти анҷом")
    is_online = models.BooleanField(default=True, verbose_name="Онлайн")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="Статус")
    
    time_limit = models.IntegerField(default=30, verbose_name="Мӯҳлати вақт (дақиқа)", help_text="Дақиқаҳо")
    max_attempts = models.IntegerField(default=1, verbose_name="Максимум кӯшишҳо", help_text="Максимум кӯшишҳо")
    pass_percentage = models.IntegerField(default=60, verbose_name="Фоиз барои гузарондан", help_text="Фоизи гузарондан")
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_quizzes', verbose_name="Эҷодкунанда")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Санаи эҷод")
    
    class Meta:
        verbose_name = 'Викторина'
        verbose_name_plural = 'Викторинаҳо'
        ordering = ['-created_at']
    
    def __str__(self):
        subject_name = self.subject.name if self.subject else "Без предмета"
        return f"{self.title} ({subject_name})"
    
    def is_active(self):
        now = timezone.now()
        return self.status == 'active' and self.start_time <= now <= self.end_time


# models.py - дар Question model
class Question(models.Model):
    QUESTION_TYPE_CHOICES = (
        ('single_choice', 'Як интихоб'),
        ('multiple_choice', 'Чанд интихоб'),
        ('true_false', 'Дурст/Нодуруст'),
        ('short_answer', 'Ҷавоби кӯтоҳ'),
    )
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField(verbose_name="Матни савол")
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default='single_choice')
    points = models.IntegerField(default=1, verbose_name="Ҳаққҳо")
    order = models.IntegerField(default=0, verbose_name="Тартиб")
    hint = models.TextField(blank=True, null=True, verbose_name="Ишора")
    explanation = models.TextField(blank=True, null=True, verbose_name="Шарҳ")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Савол'
        verbose_name_plural = 'Саволҳо'
        ordering = ['order']
    
    def __str__(self):
        return f"{self.text[:50]}..."
    
    def get_correct_answers(self):
        return self.answers.filter(is_correct=True)
    
    def save(self, *args, **kwargs):
        if not self.order and self.quiz:
            last_question = Question.objects.filter(quiz=self.quiz).order_by('-order').first()
            self.order = (last_question.order + 1) if last_question else 1
        super().save(*args, **kwargs)


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Ҷавоб'
        verbose_name_plural = 'Ҷавобҳо'
    
    def __str__(self):
        return f"{self.text[:50]}... ({'✓' if self.is_correct else '✗'})"


class QuizSession(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='sessions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_sessions', null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='quiz_sessions', null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Сеанси викторина'
        verbose_name_plural = 'Сеансҳои викторина'
    
    def __str__(self):
        entity = self.user.username if self.user else self.group.name
        return f"{entity} - {self.quiz.title}"
    
    def is_finished(self):
        return self.finished_at is not None
    
    def duration(self):
        if self.finished_at:
            return self.finished_at - self.started_at
        return timezone.now() - self.started_at
    
    def get_score(self):
        user_answers = self.user_answers.all()
        score = 0
        
        for user_answer in user_answers:
            if user_answer.answer.is_correct:
                score += user_answer.question.points
        
        return score


class UserAnswer(models.Model):
    session = models.ForeignKey(QuizSession, on_delete=models.CASCADE, related_name='user_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    answered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Ҷавоби истифодабаранда'
        verbose_name_plural = 'Ҷавобҳои истифодабарандагон'
        unique_together = ['session', 'question']
    
    def __str__(self):
        return f"{self.session} - Q{self.question.id}"


class Result(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='results')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='results', null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='results', null=True, blank=True)
    score = models.FloatField()
    total_questions = models.IntegerField()
    correct_answers = models.IntegerField()
    completed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Натиҷа'
        verbose_name_plural = 'Натиҷаҳо'
        ordering = ['-score', 'completed_at']
    
    def __str__(self):
        entity = self.user.username if self.user else self.group.name
        return f"{entity} - {self.score}/{self.total_questions}"
    
    def percentage(self):
        return (self.score / self.total_questions * 100) if self.total_questions > 0 else 0


class Rating(models.Model):
    ENTITY_TYPE_CHOICES = (
        ('user', 'Истифодабаранда'),
        ('group', 'Гурӯҳ'),
    )
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='ratings')
    entity_type = models.CharField(max_length=10, choices=ENTITY_TYPE_CHOICES)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    rank = models.IntegerField()
    score = models.FloatField()
    
    class Meta:
        verbose_name = 'Рейтинг'
        verbose_name_plural = 'Рейтингҳо'
        ordering = ['quiz', 'rank']
    
    def __str__(self):
        entity = self.user.username if self.user else self.group.name
        return f"#{self.rank} - {entity} ({self.score})"


class Permission(models.Model):
    name = models.CharField(max_length=100)
    codename = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Иҷозат'
        verbose_name_plural = 'Иҷозатҳо'
    
    def __str__(self):
        return self.name


class AuditLog(models.Model):
    ACTION_CHOICES = (
        ('create', 'Эҷод'),
        ('update', 'Навсозӣ'),
        ('delete', 'Ҳазф'),
        ('login', 'Воридшавӣ'),
        ('logout', 'Баромад'),
        ('attempt', 'Иштирок'),
    )
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, null=True, blank=True)
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Логи аудит'
        verbose_name_plural = 'Логҳои аудит'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user} - {self.get_action_display()} - {self.model}"