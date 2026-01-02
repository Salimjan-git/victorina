from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import *

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = self.cleaned_data['role']
        
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
        fields = ['name', 'level_type']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'level_type': forms.Select(attrs={'class': 'form-control'}),
        }


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'subject', 'leader']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'leader': forms.Select(attrs={'class': 'form-control'}),
        }


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = [
            'title', 'description', 'subject', 'quiz_mode',
            'level_type', 'start_level', 'end_level',
            'start_time', 'end_time', 'is_online', 'status'
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
        }


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


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text', 'is_correct']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control'}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
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


class UserAnswerForm(forms.ModelForm):
    class Meta:
        model = UserAnswer
        fields = ['question', 'answer']
        widgets = {
            'question': forms.HiddenInput(),
            'answer': forms.RadioSelect(),  # Барои single choice
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