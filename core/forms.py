from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import *

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем классы для полей паролей
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = self.cleaned_data['role']
        user.username = self.cleaned_data.get('username') or user.email

        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['level_type', 'current_level']
        widgets = {
            'level_type': forms.Select(attrs={'class': 'form-control'}),
            'current_level': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = [
            'name', 'code', 'grade_level', 'description', 
            'color', 'icon', 'is_public', 'requires_approval',
            'max_students', 'pass_percentage', 'prerequisites', 'level_type'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'grade_level': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'icon': forms.TextInput(attrs={'class': 'form-control'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_approval': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_students': forms.NumberInput(attrs={'class': 'form-control'}),
            'pass_percentage': forms.NumberInput(attrs={'class': 'form-control'}),
            'prerequisites': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'level_type': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Номи фан',
            'code': 'Рамзи фан',
            'grade_level': 'Синф/Сатҳ',
            'description': 'Тавсиф',
            'color': 'Ранг',
            'icon': 'Икона',
            'is_public': 'Оммавӣ',
            'requires_approval': 'Иҷозаи омӯзгор лозим аст',
            'max_students': 'Максимум донишҷӯён (0=беҳад)',
            'pass_percentage': 'Фоиз барои гузарондан',
            'prerequisites': 'Шартҳои пешакӣ',
            'level_type': 'Навъи сатҳ',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        # Дополнительные проверки если нужно
        return cleaned_data


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'subject', 'leader']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'leader': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Номи гурӯҳ',
            'subject': 'Фан',
            'leader': 'Роҳбар',
        }

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = [
            'title', 'description', 'subject', 'quiz_mode',
            'level_type', 'start_level', 'end_level',
            'start_time', 'end_time', 'is_online', 'status',
            'time_limit', 'max_attempts', 'pass_percentage'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'quiz_mode': forms.Select(attrs={'class': 'form-control'}),
            'level_type': forms.Select(attrs={'class': 'form-control'}),
            'start_level': forms.NumberInput(attrs={'class': 'form-control'}),
            'end_level': forms.NumberInput(attrs={'class': 'form-control'}),
            'start_time': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'}
            ),
            'end_time': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'}
            ),
            'is_online': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'time_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_attempts': forms.NumberInput(attrs={'class': 'form-control'}),
            'pass_percentage': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'title': 'Сарлавҳа',
            'description': 'Тавсиф',
            'subject': 'Фан (ихтиёрӣ)',
            'quiz_mode': 'Реҷаи викторина',
            'level_type': 'Навъи сатҳ',
            'start_level': 'Сатҳи оғоз',
            'end_level': 'Сатҳи анҷом',
            'start_time': 'Вақти оғоз',
            'end_time': 'Вақти анҷом',
            'is_online': 'Онлайн',
            'status': 'Статус',
            'time_limit': 'Мӯҳлати вақт (дақиқа)',
            'max_attempts': 'Максимум кӯшишҳо',
            'pass_percentage': 'Фоиз барои гузарондан',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Делаем поле subject необязательным
        self.fields['subject'].required = False
        # Добавляем пустой выбор
        self.fields['subject'].empty_label = "---- Интихоб накунед ----"
    
    def clean(self):
        cleaned_data = super().clean()
        
        start_level = cleaned_data.get('start_level')
        end_level = cleaned_data.get('end_level')
        
        if start_level and end_level:
            if start_level > end_level:
                raise forms.ValidationError("Сатҳи оғоз аз сатҳи анҷом зиёд буда наметавонад")
        
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time:
            if start_time >= end_time:
                raise forms.ValidationError("Вақти оғоз бояд пеш аз вақти анҷом бошад")
        
        time_limit = cleaned_data.get('time_limit')
        if time_limit and time_limit <= 0:
            raise forms.ValidationError("Мӯҳлати вақт бояд мусбат бошад")
        
        max_attempts = cleaned_data.get('max_attempts')
        if max_attempts and max_attempts <= 0:
            raise forms.ValidationError("Шумораи кӯшишҳо бояд мусбат бошад")
        
        pass_percentage = cleaned_data.get('pass_percentage')
        if pass_percentage and (pass_percentage < 0 or pass_percentage > 100):
            raise forms.ValidationError("Фоизи гузарондан бояд дар байни 0 ва 100 бошад")
        
        return cleaned_data


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'question_type', 'points', 'order']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'question_type': forms.Select(attrs={'class': 'form-control'}),
            'points': forms.NumberInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'text': 'Матни савол',
            'question_type': 'Навъи савол',
            'points': 'Ҳисса',
            'order': 'Тартиб',
        }


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text', 'is_correct']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control'}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'text': 'Матни ҷавоб',
            'is_correct': 'Дуруст',
        }


class AnswerInlineFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        
        correct_answers = 0
        for form in self.forms:
            if not form.cleaned_data.get('DELETE', False):
                if form.cleaned_data.get('is_correct', False):
                    correct_answers += 1
        
        if correct_answers == 0:
            raise forms.ValidationError("Ҳадди ақал як ҷавоби дуруст лозим аст.")


class QuizSessionForm(forms.ModelForm):
    class Meta:
        model = QuizSession
        fields = ['quiz', 'user', 'group']
        widgets = {
            'quiz': forms.Select(attrs={'class': 'form-control'}),
            'user': forms.Select(attrs={'class': 'form-control'}),
            'group': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'quiz': 'Викторина',
            'user': 'Истифодабар',
            'group': 'Гурӯҳ',
        }


class UserAnswerForm(forms.ModelForm):
    class Meta:
        model = UserAnswer
        fields = ['question', 'answer']
        widgets = {
            'question': forms.HiddenInput(),
            'answer': forms.RadioSelect(),  # Барои single choice
        }
        labels = {
            'answer': 'Ҷавоб',
        }


class ResultForm(forms.ModelForm):
    class Meta:
        model = Result
        fields = ['quiz', 'user', 'group', 'score', 'total_questions', 'correct_answers']
        widgets = {
            'quiz': forms.Select(attrs={'class': 'form-control'}),
            'user': forms.Select(attrs={'class': 'form-control'}),
            'group': forms.Select(attrs={'class': 'form-control'}),
            'score': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_questions': forms.NumberInput(attrs={'class': 'form-control'}),
            'correct_answers': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'quiz': 'Викторина',
            'user': 'Истифодабар',
            'group': 'Гурӯҳ',
            'score': 'Ҳисса',
            'total_questions': 'Ҳамаи саволҳо',
            'correct_answers': 'Ҷавобҳои дуруст',
        }


# Дополнительные формы для фильтров
class SubjectFilterForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ҷустуҷӯ...'
        }),
        label=''
    )
    level_type = forms.ChoiceField(
        required=False,
        choices=Subject.LEVEL_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Навъи сатҳ'
    )


class QuizFilterForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ҷустуҷӯ...'
        }),
        label=''
    )
    subject = forms.ModelChoiceField(
        required=False,
        queryset=Subject.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Фан'
    )
    status = forms.ChoiceField(
        required=False,
        choices=Quiz.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Статус'
    )
    quiz_mode = forms.ChoiceField(
        required=False,
        choices=Quiz.MODE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Реҷа'
    )