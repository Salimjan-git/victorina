from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Avg, Max, Min, Count
import json
from django import forms

from .models import *
from .forms import *

def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    try:
        context = {
            'total_users': User.objects.count(),
            'total_quizzes': Quiz.objects.count(),
            'active_quizzes': Quiz.objects.filter(status='active').count(),
            'total_groups': Group.objects.count(),
        }
    except:
        context = {
            'total_users': 0,
            'total_quizzes': 0,
            'active_quizzes': 0,
            'total_groups': 0,
        }
    
    return render(request, 'home.html', context)

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

def is_teacher(user):
    return user.is_authenticated and user.role == 'teacher'

def is_student(user):
    return user.is_authenticated and user.role == 'student'

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Шумо бомуваффақият ба система ворид шудед!')
            return redirect('dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'auth/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Хуш омадед, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Номуваффақ! Номи истифодабаранда ё парол нодуруст аст.')
    
    return render(request, 'auth/login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'Шумо аз система баромадед.')
    return redirect('home')

@login_required
def dashboard_view(request):
    context = {}
    
    try:
        if request.user.role == 'admin':
            context.update({
                'total_users': User.objects.count(),
                'total_quizzes': Quiz.objects.count(),
                'total_groups': Group.objects.count(),
                'active_quizzes': Quiz.objects.filter(status='active').count(),
                'recent_logs': AuditLog.objects.all()[:10],
            })
        
        elif request.user.role == 'teacher':
            my_quizzes = Quiz.objects.filter(created_by=request.user)
            context.update({
                'my_quizzes_count': my_quizzes.count(),
                'active_quizzes_count': my_quizzes.filter(status='active').count(),
                'total_students': User.objects.filter(role='student').count(),
                'recent_results': Result.objects.filter(
                    quiz__created_by=request.user
                ).order_by('-completed_at')[:10],
            })
        
        elif request.user.role == 'student':
            now = timezone.now()
            
            # Озод кардани профил
            try:
                profile = request.user.profile
            except:
                profile = Profile.objects.create(user=request.user, level_type='school', current_level=1)
            
            active_quizzes = Quiz.objects.filter(
                status='active',
                start_time__lte=now,
                end_time__gte=now
            )
            
            available_quizzes = active_quizzes.filter(
                level_type=profile.level_type,
                start_level__lte=profile.current_level,
                end_level__gte=profile.current_level
            )
            
            completed_sessions = QuizSession.objects.filter(
                user=request.user,
                finished_at__isnull=False
            )
            
            # Гурӯҳҳо
            my_groups = Group.objects.filter(
                Q(leader=request.user) | Q(members__user=request.user)
            ).distinct()
            
            context.update({
                'profile': profile,
                'available_quizzes': available_quizzes[:5],
                'available_quizzes_count': available_quizzes.count(),
                'completed_sessions': completed_sessions[:3],
                'total_completed': completed_sessions.count(),
                'my_groups': my_groups[:3],
                'my_groups_count': my_groups.count(),
                'my_results': Result.objects.filter(user=request.user).order_by('-completed_at')[:5],
            })
    except Exception as e:
        messages.error(request, f'Хатогӣ дар дашборд: {str(e)}')
    
    return render(request, 'dashboard.html', context)

@user_passes_test(is_admin)
def user_list_view(request):
    users = User.objects.all()
    return render(request, 'users/list.html', {'users': users})

@user_passes_test(is_admin)
def user_create_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Истифодабаранда {user.username} бомуваффақият эҷод шуд.')
            return redirect('user_list')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/create.html', {'form': form})

@user_passes_test(is_admin)
def user_edit_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Истифодабаранда бомуваффақият навсозӣ шуд.')
            return redirect('user_list')
    else:
        form = CustomUserCreationForm(instance=user)
    
    return render(request, 'users/edit.html', {'form': form, 'user': user})

@login_required
def profile_view(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user, level_type='school', current_level=1)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профили шумо бомуваффақият навсозӣ шуд.')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)
    
    # Ҳисобкунии омор
    completed_quizzes = QuizSession.objects.filter(
        user=request.user,
        finished_at__isnull=False
    ).count()
    
    total_quizzes = QuizSession.objects.filter(user=request.user).count()
    
    context = {
        'form': form,
        'profile': profile,
        'completed_quizzes': completed_quizzes,
        'total_quizzes': total_quizzes,
    }
    
    return render(request, 'profile/view.html', context)

@login_required
def subject_list_view(request):
    subjects = Subject.objects.all()
    return render(request, 'subjects/list.html', {'subjects': subjects})

@user_passes_test(is_teacher)
def subject_create_view(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save()
            messages.success(request, f'Фан {subject.name} эҷод шуд.')
            return redirect('subject_list')
    else:
        form = SubjectForm()
    
    return render(request, 'subjects/create.html', {'form': form})

@login_required
def group_list_view(request):
    if request.user.role in ['admin', 'teacher']:
        groups = Group.objects.all()
    else:
        groups = Group.objects.filter(
            Q(leader=request.user) | Q(members__user=request.user)
        ).distinct()
    
    return render(request, 'groups/list.html', {'groups': groups})

@login_required
def group_create_view(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.leader = request.user
            group.save()
            
            GroupMember.objects.create(group=group, user=request.user)
            
            messages.success(request, f'Гурӯҳ {group.name} эҷод шуд.')
            return redirect('group_list')
    else:
        form = GroupForm(initial={'leader': request.user})
    
    return render(request, 'groups/create.html', {'form': form})

@login_required
def group_detail_view(request, pk):
    group = get_object_or_404(Group, pk=pk)
    members = group.members.all()
    is_member = members.filter(user=request.user).exists()
    
    context = {
        'group': group,
        'members': members,
        'is_member': is_member,
        'is_leader': group.leader == request.user,
    }
    
    return render(request, 'groups/detail.html', context)

@login_required
def group_join_view(request, pk):
    group = get_object_or_404(Group, pk=pk)
    
    if GroupMember.objects.filter(group=group, user=request.user).exists():
        messages.warning(request, 'Шумо аллакай аъзои ин гурӯҳ ҳастед.')
    else:
        GroupMember.objects.create(group=group, user=request.user)
        messages.success(request, f'Шумо ба гурӯҳ {group.name} ҳамроҳ шудед.')
    
    return redirect('group_detail', pk=pk)

@login_required
def quiz_list_view(request):
    if request.user.role in ['admin', 'teacher']:
        quizzes = Quiz.objects.all()
    else:
        now = timezone.now()
        try:
            profile = request.user.profile
        except:
            profile = Profile.objects.create(user=request.user, level_type='school', current_level=1)
        
        quizzes = Quiz.objects.filter(
            status='active',
            start_time__lte=now,
            end_time__gte=now,
            level_type=profile.level_type,
            start_level__lte=profile.current_level,
            end_level__gte=profile.current_level
        )
    
    status_filter = request.GET.get('status')
    mode_filter = request.GET.get('mode')
    
    if status_filter:
        quizzes = quizzes.filter(status=status_filter)
    if mode_filter:
        quizzes = quizzes.filter(quiz_mode=mode_filter)
    
    context = {
        'quizzes': quizzes,
        'status_choices': Quiz.STATUS_CHOICES,
        'mode_choices': Quiz.MODE_CHOICES,
    }
    
    return render(request, 'quizzes/list.html', context)

@user_passes_test(is_teacher)
def quiz_create_view(request):
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.created_by = request.user
            quiz.save()
            
            messages.success(request, f'Викторина {quiz.title} эҷод шуд.')
            return redirect('quiz_detail', pk=quiz.pk)
    else:
        form = QuizForm()
    
    return render(request, 'quizzes/create.html', {'form': form})

@login_required
def quiz_detail_view(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    questions = quiz.questions.all()
    
    can_access = True
    if request.user.role == 'student':
        try:
            profile = request.user.profile
        except:
            profile = Profile.objects.create(user=request.user, level_type='school', current_level=1)
        
        can_access = (
            quiz.level_type == profile.level_type and
            quiz.start_level <= profile.current_level <= quiz.end_level and
            quiz.status == 'active'
        )
    
    has_attempted = QuizSession.objects.filter(
        quiz=quiz,
        user=request.user,
        finished_at__isnull=False
    ).exists()
    
    context = {
        'quiz': quiz,
        'questions': questions,
        'can_access': can_access,
        'has_attempted': has_attempted,
        'is_active': quiz.is_active(),
    }
    
    return render(request, 'quizzes/detail.html', context)

@user_passes_test(is_teacher)
def quiz_edit_view(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    
    if request.user != quiz.created_by and request.user.role != 'admin':
        messages.error(request, 'Шумо иҷозати таҳрир кардани ин викторинаро надоред.')
        return redirect('quiz_detail', pk=pk)
    
    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            form.save()
            messages.success(request, 'Викторина бомуваффақият навсозӣ шуд.')
            return redirect('quiz_detail', pk=pk)
    else:
        form = QuizForm(instance=quiz)
    
    return render(request, 'quizzes/edit.html', {'form': form, 'quiz': quiz})

@login_required
def quiz_start_view(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    
    if not quiz.is_active():
        messages.error(request, 'Ин викторина фаъол нест.')
        return redirect('quiz_detail', pk=pk)
    
    if request.user.role == 'student':
        try:
            profile = request.user.profile
        except:
            profile = Profile.objects.create(user=request.user, level_type='school', current_level=1)
        
        if not (quiz.level_type == profile.level_type and 
                quiz.start_level <= profile.current_level <= quiz.end_level):
            messages.error(request, 'Шумо иҷозати иштирок дар ин викторинаро надоред.')
            return redirect('quiz_list')
    
    active_session = QuizSession.objects.filter(
        quiz=quiz,
        user=request.user,
        finished_at__isnull=True
    ).first()
    
    if active_session:
        return redirect('quiz_take', session_pk=active_session.pk)
    
    session = QuizSession.objects.create(
        quiz=quiz,
        user=request.user
    )
    
    return redirect('quiz_take', session_pk=session.pk)

@login_required
def quiz_take_view(request, session_pk):
    session = get_object_or_404(QuizSession, pk=session_pk, user=request.user)
    
    if session.finished_at:
        messages.info(request, 'Шумо ин викторинаро аллакай анҷом додаед.')
        return redirect('quiz_result', session_pk=session.pk)
    
    quiz = session.quiz
    questions = quiz.questions.all().order_by('order')
    
    current_question_index = int(request.GET.get('question', 0))
    
    if current_question_index >= len(questions):
        return redirect('quiz_finish', session_pk=session.pk)
    
    current_question = questions[current_question_index]
    
    previous_answer = UserAnswer.objects.filter(
        session=session,
        question=current_question
    ).first()
    
    if request.method == 'POST':
        answer_id = request.POST.get('answer')
        
        if answer_id:
            try:
                answer = Answer.objects.get(pk=answer_id, question=current_question)
                
                if previous_answer:
                    previous_answer.answer = answer
                    previous_answer.save()
                else:
                    UserAnswer.objects.create(
                        session=session,
                        question=current_question,
                        answer=answer
                    )
                
                next_question = current_question_index + 1
                return redirect(f'{request.path}?question={next_question}')
            
            except Answer.DoesNotExist:
                messages.error(request, 'Ҷавоби интихобшуда нодуруст аст.')
    
    context = {
        'session': session,
        'quiz': quiz,
        'question': current_question,
        'question_index': current_question_index,
        'total_questions': len(questions),
        'previous_answer': previous_answer,
        'progress': int((current_question_index / len(questions)) * 100) if len(questions) > 0 else 0,
    }
    
    return render(request, 'quizzes/take.html', context)

@login_required
def quiz_finish_view(request, session_pk):
    session = get_object_or_404(QuizSession, pk=session_pk, user=request.user)
    
    if session.finished_at:
        messages.info(request, 'Ин викторина аллакай анҷом ёфтааст.')
        return redirect('quiz_result', session_pk=session.pk)
    
    user_answers = session.user_answers.all()
    total_questions = session.quiz.questions.count()
    correct_answers = 0
    score = 0
    
    for user_answer in user_answers:
        if user_answer.answer.is_correct:
            correct_answers += 1
            score += user_answer.question.points
    
    result = Result.objects.create(
        quiz=session.quiz,
        user=session.user,
        score=score,
        total_questions=total_questions,
        correct_answers=correct_answers
    )
    
    session.finished_at = timezone.now()
    session.save()
    
    messages.success(request, 'Викторина бомуваффақият анҷом ёфт!')
    return redirect('quiz_result', session_pk=session.pk)

@login_required
def quiz_result_view(request, session_pk):
    session = get_object_or_404(QuizSession, pk=session_pk, user=request.user)
    
    if not session.finished_at:
        messages.warning(request, 'Шумо ин викторинаро анҷом надодаед.')
        return redirect('quiz_take', session_pk=session.pk)
    
    result = Result.objects.filter(
        quiz=session.quiz,
        user=request.user
    ).order_by('-completed_at').first()
    
    user_answers = session.user_answers.select_related('question', 'answer').all()
    
    percentage = 0
    if result and result.total_questions > 0:
        percentage = (result.score / result.total_questions) * 100
    
    context = {
        'session': session,
        'result': result,
        'user_answers': user_answers,
        'percentage': percentage,
    }
    
    return render(request, 'quizzes/result.html', context)

@login_required
def my_results_view(request):
    results = Result.objects.filter(user=request.user).order_by('-completed_at')
    
    total_quizzes = results.count()
    avg_score = results.aggregate(avg=Avg('score'))['avg'] or 0
    best_result = results.order_by('-score').first()
    
    context = {
        'results': results,
        'total_quizzes': total_quizzes,
        'avg_score': avg_score,
        'best_result': best_result,
    }
    
    return render(request, 'results/my_results.html', context)

@user_passes_test(is_teacher)
def quiz_results_view(request, quiz_pk):
    quiz = get_object_or_404(Quiz, pk=quiz_pk)
    
    if request.user != quiz.created_by and request.user.role != 'admin':
        messages.error(request, 'Шумо иҷозати дидани натиҷаҳои ин викторинаро надоред.')
        return redirect('quiz_list')
    
    results = Result.objects.filter(quiz=quiz).order_by('-score')
    
    total_participants = results.count()
    avg_score = results.aggregate(avg=Avg('score'))['avg'] or 0
    max_score = results.aggregate(max=Max('score'))['max'] or 0
    min_score = results.aggregate(min=Min('score'))['min'] or 0
    
    context = {
        'quiz': quiz,
        'results': results,
        'total_participants': total_participants,
        'avg_score': avg_score,
        'max_score': max_score,
        'min_score': min_score,
    }
    
    return render(request, 'results/quiz_results.html', context)

@login_required
def check_quiz_time_view(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    
    now = timezone.now()
    is_active = quiz.is_active()
    time_left = None
    
    if quiz.start_time > now:
        time_left = quiz.start_time - now
    elif quiz.end_time > now:
        time_left = quiz.end_time - now
    
    return JsonResponse({
        'is_active': is_active,
        'time_left_seconds': time_left.total_seconds() if time_left else 0,
        'status': quiz.status,
    })

@login_required
def save_answer_ajax_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            session_id = data.get('session_id')
            question_id = data.get('question_id')
            answer_id = data.get('answer_id')
            
            session = QuizSession.objects.get(pk=session_id, user=request.user)
            question = Question.objects.get(pk=question_id, quiz=session.quiz)
            answer = Answer.objects.get(pk=answer_id, question=question)
            
            user_answer, created = UserAnswer.objects.update_or_create(
                session=session,
                question=question,
                defaults={'answer': answer}
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Ҷавоб нигоҳ дошта шуд.',
            })
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e),
            })
    
    return JsonResponse({'success': False, 'message': 'Методи нодуруст.'})


@user_passes_test(is_teacher)
def question_create_view(request, quiz_pk):
    quiz = get_object_or_404(Quiz, pk=quiz_pk)
    
    if request.user != quiz.created_by and request.user.role != 'admin':
        messages.error(request, 'Шумо иҷозати илова кардани саволро надоред.')
        return redirect('quiz_detail', pk=quiz_pk)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz
            
            if not question.order:
                last_question = quiz.questions.order_by('-order').first()
                question.order = (last_question.order + 1) if last_question else 1
            
            question.save()
            messages.success(request, 'Савол бомуваффақият илова шуд.')
            return redirect('quiz_detail', pk=quiz_pk)
    else:
        form = QuestionForm(initial={'quiz': quiz})
    
    context = {
        'form': form,
        'quiz': quiz,
        'title': 'Иловаи саволи нав',
    }
    
    return render(request, 'questions/create.html', context)


@user_passes_test(is_teacher)
def question_edit_view(request, pk):
    
    question = get_object_or_404(Question, pk=pk)
    quiz = question.quiz
    
    if request.user != quiz.created_by and request.user.role != 'admin':
        messages.error(request, 'Шумо иҷозати таҳрир кардани ин саволро надоред.')
        return redirect('quiz_detail', pk=quiz.pk)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, 'Савол бомуваффақият навсозӣ шуд.')
            return redirect('quiz_detail', pk=quiz.pk)
    else:
        form = QuestionForm(instance=question)
    
    AnswerFormSet = forms.inlineformset_factory(
        Question, Answer, 
        form=AnswerForm,
        formset=AnswerInlineFormSet,
        extra=4,
        can_delete=True
    )
    
    if request.method == 'POST':
        answer_formset = AnswerFormSet(request.POST, instance=question)
        if answer_formset.is_valid():
            answer_formset.save()
            return redirect('question_edit', pk=pk)
    else:
        answer_formset = AnswerFormSet(instance=question)
    
    context = {
        'form': form,
        'answer_formset': answer_formset,
        'question': question,
        'quiz': quiz,
        'title': 'Таҳрири савол',
    }
    
    return render(request, 'questions/edit.html', context)


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
