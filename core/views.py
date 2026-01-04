from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse
from django.http import JsonResponse
from django.utils.dateparse import parse_datetime
from django.utils import timezone
import traceback
import datetime
from django.db.models import Q, Avg, Max, Min, Count
import json
from django import forms
from django import template

register = template.Library()


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
    return user.is_authenticated and user.role in ['teacher', 'admin']


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
            
            # Создаем профиль если нет
            try:
                profile = request.user.profile
            except Profile.DoesNotExist:
                profile = Profile.objects.create(user=request.user, level_type='school', current_level=1)
            
            # Активные викторины
            active_quizzes = Quiz.objects.filter(
                status='active',
                start_time__lte=now,
                end_time__gte=now
            )
            
            # Доступные викторины для уровня студента
            available_quizzes = active_quizzes.filter(
                level_type=profile.level_type,
                start_level__lte=profile.current_level,
                end_level__gte=profile.current_level
            )
            
            # Завершенные сессии
            completed_sessions = QuizSession.objects.filter(
                user=request.user,
                finished_at__isnull=False
            )
            
            # Группы студента
            my_groups = Group.objects.filter(
                Q(leader=request.user) | Q(members__user=request.user)
            ).distinct()
            
            # Последние результаты
            my_results = Result.objects.filter(user=request.user).order_by('-completed_at')[:5]
            
            context.update({
                'profile': profile,
                'available_quizzes': available_quizzes[:5],
                'available_quizzes_count': available_quizzes.count(),
                'completed_sessions': completed_sessions[:3],
                'total_completed': completed_sessions.count(),
                'my_groups': my_groups[:3],
                'my_groups_count': my_groups.count(),
                'my_results': my_results,
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
    
    # Статистика
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
    try:
        # Все предметы без сортировки по created_at
        subjects = Subject.objects.all()
        
        # Фильтры
        search_query = request.GET.get('search', '')
        level_type = request.GET.get('level_type', '')
        
        if search_query:
            subjects = subjects.filter(
                Q(name__icontains=search_query) |
                Q(code__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        if level_type:
            subjects = subjects.filter(level_type=level_type)
        
        # Статистика
        stats = {
            'total_subjects': subjects.count(),
            'total_quizzes': Quiz.objects.count(),
            'total_questions': Question.objects.count(),
            'active_students': User.objects.filter(role='student', is_active=True).count(),
        }
        
        # Подготовка данных для шаблона
        subject_data = []
        for subject in subjects:
            subject_info = {
                'id': subject.id,
                'name': subject.name,
                'code': subject.code,
                'grade_level': subject.grade_level,
                'description': subject.description,
                'color': subject.color,
                'icon': subject.icon,
                'is_public': subject.is_public,
                'requires_approval': subject.requires_approval,
                'max_students': subject.max_students,
                'pass_percentage': subject.pass_percentage,
                'prerequisites': subject.prerequisites,
                'level_type': subject.level_type,
                'level_type_display': subject.get_level_type_display(),
            }
            
            # Количество викторин
            try:
                quiz_count = Quiz.objects.filter(subject=subject).count()
                subject_info['quiz_count'] = quiz_count
            except Exception as e:
                subject_info['quiz_count'] = 0
            
            # Количество вопросов
            try:
                question_count = Question.objects.filter(quiz__subject=subject).count()
                subject_info['question_count'] = question_count
            except Exception as e:
                subject_info['question_count'] = 0
            
            # Процент завершения для студентов
            if request.user.is_authenticated and request.user.role == 'student':
                try:
                    completed_quizzes = QuizSession.objects.filter(
                        user=request.user,
                        quiz__subject=subject,
                        finished_at__isnull=False
                    ).count()
                    subject_info['completion_rate'] = int((completed_quizzes / subject_info['quiz_count']) * 100) if subject_info['quiz_count'] > 0 else 0
                except Exception as e:
                    subject_info['completion_rate'] = 0
            else:
                subject_info['completion_rate'] = 0
            
            subject_data.append(subject_info)
        
        # Популярные предметы
        popular_subjects = sorted(
            subject_data, 
            key=lambda x: x['quiz_count'], 
            reverse=True
        )[:4]
        
        context = {
            'subjects': subject_data,
            'stats': stats,
            'popular_subjects': popular_subjects,
            'search_query': search_query,
            'selected_level_type': level_type,
        }
        
        return render(request, 'subjects/list.html', context)
        
    except Exception as e:
        messages.error(request, f'Хатогӣ дар намоиши фанҳо: {str(e)}')
        return redirect('dashboard')


@user_passes_test(is_teacher)
def subject_create_view(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save()
            messages.success(request, f'Фан "{subject.name}" бомуваффақият эҷод шуд.')
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
    """Упрощенная версия для отладки"""
    try:
        print("=== НАЧАЛО quiz_list_view ===")
        
        # 1. Получаем базовый QuerySet
        if request.user.role in ['admin', 'teacher']:
            quizzes = Quiz.objects.all()
            print(f"Админ/учитель: {quizzes.count()} викторин")
        else:
            # Для студентов - только активные
            now = timezone.now()
            print(f"Текущее время: {now}")
            
            # Получаем профиль безопасно
            try:
                profile = Profile.objects.get(user=request.user)
                print(f"Найден профиль: {profile}")
            except Profile.DoesNotExist:
                profile = Profile.objects.create(
                    user=request.user,
                    level_type='school',
                    current_level=1
                )
                print(f"Создан новый профиль: {profile}")
            
            quizzes = Quiz.objects.filter(
                status='active',
                start_time__lte=now,
                end_time__gte=now,
                level_type=profile.level_type,
                start_level__lte=profile.current_level,
                end_level__gte=profile.current_level
            )
            print(f"Студент: {quizzes.count()} доступных викторин")
        
        # 2. Применяем простые фильтры
        search_query = request.GET.get('search', '')
        subject_id = request.GET.get('subject')
        
        if search_query:
            quizzes = quizzes.filter(title__icontains=search_query)
            print(f"После поиска '{search_query}': {quizzes.count()}")
        
        if subject_id:
            quizzes = quizzes.filter(subject_id=subject_id)
            print(f"После фильтра по предмету {subject_id}: {quizzes.count()}")
        
        # 3. Берем только первые 10 для отладки
        quizzes = quizzes[:10]
        
        # 4. Минимальная обработка
        processed_quizzes = []
        for quiz in quizzes:
            quiz_data = {
                'id': quiz.id,
                'title': quiz.title,
                'description': quiz.description[:100] if quiz.description else '',
                'subject_name': quiz.subject.name if quiz.subject else 'Без предмета',
                'question_count': quiz.questions.count(),
                'time_limit': quiz.time_limit,
                'max_attempts': quiz.max_attempts,
                'pass_percentage': quiz.pass_percentage,
                'start_level': quiz.start_level,
                'end_level': quiz.end_level,
                'status': quiz.status,
                'quiz_mode': quiz.quiz_mode,
                'level_type': quiz.level_type,
                'start_time': quiz.start_time,
                'end_time': quiz.end_time,
                'created_at': quiz.created_at,
            }
            processed_quizzes.append(quiz_data)
        
        # 5. Собираем простой контекст
        subjects = Subject.objects.all()[:5] if request.user.role in ['admin', 'teacher'] else []
        
        context = {
            'quizzes': processed_quizzes,  # Используем список словарей вместо QuerySet
            'subjects': subjects,
            'search_query': search_query,
            'stats': {
                'available_quizzes': len(processed_quizzes),
                'active_quizzes_count': len(processed_quizzes),
                'completed_quizzes_count': 0,
                'total_participants': 0,
            }
        }
        
        print("=== УСПЕШНО ЗАВЕРШЕНО ===")
        return render(request, 'quizzes/list_simple.html', context)
        
    except Exception as e:
        print(f"=== ОШИБКА: {str(e)} ===")
        print(traceback.format_exc())
        
        # Создаем минимальную страницу с ошибкой
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Ошибка</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; }}
                .error {{ background: #ffe6e6; border: 1px solid #ff9999; padding: 20px; border-radius: 5px; }}
                pre {{ background: #f5f5f5; padding: 10px; overflow: auto; }}
            </style>
        </head>
        <body>
            <h1>Ошибка в отображении викторин</h1>
            <div class="error">
                <h3>Тип ошибки: {type(e).__name__}</h3>
                <p><strong>Сообщение:</strong> {str(e)}</p>
                <h4>Traceback:</h4>
                <pre>{traceback.format_exc()}</pre>
            </div>
            <p><a href="/">Вернуться на главную</a></p>
        </body>
        </html>
        """
        return HttpResponse(error_html)


@register.filter
def filter_active(quizzes):
    now = timezone.now()
    return [q for q in quizzes if q.time_status == 'active']

@register.filter
def filter_upcoming(quizzes):
    now = timezone.now()
    return [q for q in quizzes if q.time_status == 'soon']

@register.filter
def filter_ended(quizzes):
    now = timezone.now()
    return [q for q in quizzes if q.time_status == 'ended']


@user_passes_test(is_teacher)
def quiz_create_view(request):
    """View for creating a new quiz - UPDATED FOR QUIZ MODEL"""
    try:
        print("=== DEBUG: quiz_create_view called ===")
        
        # Get subjects for dropdown
        subjects = Subject.objects.all()
        
        if request.method == 'POST':
            print("=== DEBUG: POST Data ===")
            for key, value in request.POST.items():
                print(f"{key}: {value}")
            
            # Get form data
            title = request.POST.get('title', '').strip()
            subject_id = request.POST.get('subject', '')
            description = request.POST.get('description', '').strip()
            quiz_mode = request.POST.get('quiz_mode', 'individual')
            level_type = request.POST.get('level_type', 'school')
            start_level = request.POST.get('start_level', '1')
            end_level = request.POST.get('end_level', '10')
            time_limit = request.POST.get('duration', '30')  # Note: field name is 'duration' in form
            max_attempts = request.POST.get('max_attempts', '1')
            pass_percentage = request.POST.get('pass_percentage', '60')
            
            # Get time values
            start_time_str = request.POST.get('start_time', '')
            end_time_str = request.POST.get('end_time', '')
            
            # Basic validation
            if not title:
                messages.error(request, 'Унвони викторинаро ворид кунед.')
                return render(request, 'quizzes/create.html', {
                    'subjects': subjects,
                    'error': 'Унвони викторинаро ворид кунед.'
                })
            
            # Parse subject - now optional
            subject = None
            if subject_id:
                try:
                    subject = Subject.objects.get(id=subject_id)
                except Subject.DoesNotExist:
                    messages.warning(request, 'Фан ёфт нашуд. Викторина бе фан эҷод карда мешавад.')
            
            # Parse datetime
            start_time = timezone.now()
            end_time = start_time + datetime.timedelta(days=7)
            
            if start_time_str:
                try:
                    start_time = timezone.make_aware(
                        datetime.datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M')
                    )
                except Exception as e:
                    print(f"Error parsing start_time: {str(e)}")
                    messages.warning(request, 'Формати вақти оғоз нодуруст аст. Вақти ҷорӣ истифода мешавад.')
            
            if end_time_str:
                try:
                    end_time = timezone.make_aware(
                        datetime.datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')
                    )
                except Exception as e:
                    print(f"Error parsing end_time: {str(e)}")
                    end_time = start_time + datetime.timedelta(days=7)
                    messages.warning(request, 'Формати вақти анҷом нодуруст аст. Вақти пешфарз истифода мешавад.')
            
            # Validate levels
            try:
                start_level_int = int(start_level)
                end_level_int = int(end_level)
                
                if start_level_int > end_level_int:
                    messages.error(request, 'Сатҳи оғоз набояд аз сатҳи анҷом зиёд бошад.')
                    return render(request, 'quizzes/create.html', {
                        'subjects': subjects,
                        'error': 'Сатҳи оғоз набояд аз сатҳи анҷом зиёд бошад.'
                    })
            except ValueError:
                messages.error(request, 'Сатҳҳо бояд адад бошанд.')
                return render(request, 'quizzes/create.html', {
                    'subjects': subjects,
                    'error': 'Сатҳҳо бояд адад бошанд.'
                })
            
            # Validate times
            if start_time >= end_time:
                messages.error(request, 'Вақти анҷом бояд баъд аз вақти оғоз бошад.')
                return render(request, 'quizzes/create.html', {
                    'subjects': subjects,
                    'error': 'Вақти анҷом бояд баъд аз вақти оғоз бошад.'
                })
            
            # Create quiz
            quiz = Quiz.objects.create(
                title=title,
                subject=subject,  # Can be None
                description=description,
                quiz_mode=quiz_mode,
                level_type=level_type,
                start_level=start_level_int,
                end_level=end_level_int,
                start_time=start_time,
                end_time=end_time,
                time_limit=int(time_limit),
                max_attempts=int(max_attempts),
                pass_percentage=int(pass_percentage),
                is_online=True,  # Default to online
                status='draft',  # Default to draft
                created_by=request.user
            )
            
            print(f"=== DEBUG: Quiz created: {quiz.id} ===")
            
            # Check if we should publish or save as draft
            if 'publish' in request.POST:
                quiz.status = 'active'
                quiz.save()
                messages.success(request, f'Викторина "{title}" бомуваффақият эҷод ва нашр шуд!')
            else:
                messages.success(request, f'Викторина "{title}" бомуваффақият дар ҳолати нопурра захира шуд!')
            
            # Process questions if provided in form
            process_questions_from_form(request, quiz)
            
            return redirect('quiz_detail', pk=quiz.pk)
        
        # GET request - show form
        print("=== DEBUG: GET request - showing form ===")
        return render(request, 'quizzes/create.html', {
            'subjects': subjects,
            'title': 'Эҷоди викторинаи нав'
        })
        
    except Exception as e:
        print(f"=== DEBUG: ERROR: {str(e)} ===")
        import traceback
        traceback.print_exc()
        messages.error(request, f'Хатогӣ дар эҷоди викторина: {str(e)}')
        return render(request, 'quizzes/create.html', {
            'subjects': Subject.objects.all(),
            'error': str(e)
        })


def process_questions_from_form(request, quiz):
    """Process questions from the complex form format"""
    try:
        question_count = 0
        i = 0
        
        while True:
            # Check for question in different formats
            question_text = request.POST.get(f'questions[{i}][text]', '').strip()
            if not question_text:
                # Try alternative format
                question_text = request.POST.get(f'question_text_{i}', '').strip()
            
            if not question_text:
                break
            
            question_points = request.POST.get(f'questions[{i}][points]', '10')
            if not question_points:
                question_points = request.POST.get(f'question_points_{i}', '10')
            
            # Create question
            question = Question.objects.create(
                quiz=quiz,
                text=question_text,
                question_type='single_choice',  # Default
                points=int(question_points),
                order=i+1
            )
            
            # Process answers for this question
            j = 0
            while True:
                # Try different answer formats
                answer_text = request.POST.get(f'questions[{i}][options][{j}][text]', '').strip()
                if not answer_text:
                    answer_text = request.POST.get(f'answer_text_{i}_{j}', '').strip()
                
                if not answer_text:
                    break
                
                # Check if answer is correct
                is_correct = False
                correct_key = f'questions[{i}][options][{j}][correct]'
                if correct_key in request.POST:
                    is_correct = request.POST.get(correct_key) == 'on'
                else:
                    # Try alternative format
                    correct_key = f'correct_{i}_{j}'
                    if correct_key in request.POST:
                        is_correct = request.POST.get(correct_key) == 'on'
                
                Answer.objects.create(
                    question=question,
                    text=answer_text,
                    is_correct=is_correct,
                    order=j+1
                )
                j += 1
            
            question_count += 1
            i += 1
        
        print(f"=== DEBUG: Processed {question_count} questions ===")
        return question_count
        
    except Exception as e:
        print(f"=== DEBUG: Error processing questions: {str(e)} ===")
        return 0
    

@login_required
def quiz_detail_view(request, pk):
    try:
        quiz = get_object_or_404(Quiz, pk=pk)
        questions = quiz.questions.all()
        
        # Проверка доступа
        can_access = True
        if request.user.role == 'student':
            try:
                profile = request.user.profile
            except Profile.DoesNotExist:
                profile = Profile.objects.create(user=request.user, level_type='school', current_level=1)
            
            can_access = (
                quiz.level_type == profile.level_type and
                quiz.start_level <= profile.current_level <= quiz.end_level and
                quiz.status == 'active'
            )
        
        # Проверка, проходил ли студент викторину
        has_attempted = QuizSession.objects.filter(
            quiz=quiz,
            user=request.user,
            finished_at__isnull=False
        ).exists()
        
        # Оставшиеся попытки
        attempts_remaining = quiz.max_attempts
        if request.user.is_authenticated:
            attempts_made = QuizSession.objects.filter(
                quiz=quiz,
                user=request.user,
                finished_at__isnull=False
            ).count()
            attempts_remaining = max(0, quiz.max_attempts - attempts_made)
        
        # Статистика викторины
        total_participants = QuizSession.objects.filter(
            quiz=quiz,
            finished_at__isnull=False
        ).count()
        
        avg_score = Result.objects.filter(quiz=quiz).aggregate(avg=Avg('score'))['avg'] or 0
        
        context = {
            'quiz': quiz,
            'questions': questions,
            'can_access': can_access,
            'has_attempted': has_attempted,
            'attempts_remaining': attempts_remaining,
            'is_active': quiz.is_active(),
            'total_participants': total_participants,
            'avg_score': avg_score,
        }
        
        return render(request, 'quizzes/detail.html', context)
        
    except Exception as e:
        messages.error(request, f'Хатогӣ дар намоиши викторина: {str(e)}')
        return redirect('quiz_list')


@user_passes_test(is_teacher)
def quiz_edit_view(request, pk):
    try:
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
        
    except Exception as e:
        messages.error(request, f'Хатогӣ дар таҳрири викторина: {str(e)}')
        return redirect('quiz_list')


@login_required
def quiz_start_view(request, pk):
    try:
        quiz = get_object_or_404(Quiz, pk=pk)
        
        if not quiz.is_active():
            messages.error(request, 'Ин викторина фаъол нест.')
            return redirect('quiz_detail', pk=pk)
        
        # Проверка доступа для студентов
        if request.user.role == 'student':
            try:
                profile = request.user.profile
            except Profile.DoesNotExist:
                profile = Profile.objects.create(user=request.user, level_type='school', current_level=1)
            
            if not (quiz.level_type == profile.level_type and 
                    quiz.start_level <= profile.current_level <= quiz.end_level):
                messages.error(request, 'Шумо иҷозати иштирок дар ин викторинаро надоред.')
                return redirect('quiz_list')
        
        # Проверка количества попыток
        attempts_made = QuizSession.objects.filter(
            quiz=quiz,
            user=request.user,
            finished_at__isnull=False
        ).count()
        
        if attempts_made >= quiz.max_attempts:
            messages.error(request, f'Шумо ҳамаи {quiz.max_attempts} кӯшишҳои худро истифода кардед.')
            return redirect('quiz_detail', pk=pk)
        
        # Поиск активной сессии или создание новой
        active_session = QuizSession.objects.filter(
            quiz=quiz,
            user=request.user,
            finished_at__isnull=True
        ).first()
        
        if active_session:
            return redirect('quiz_take', session_pk=active_session.pk)
        
        # Создание новой сессии
        session = QuizSession.objects.create(
            quiz=quiz,
            user=request.user,
            started_at=timezone.now()
        )
        
        messages.info(request, f'Викторина оғоз шуд. Шумо {quiz.time_limit} дақиқа вақт доред.')
        return redirect('quiz_take', session_pk=session.pk)
        
    except Exception as e:
        messages.error(request, f'Хатогӣ дар оғози викторина: {str(e)}')
        return redirect('quiz_detail', pk=pk)


@login_required
def quiz_take_view(request, session_pk):
    try:
        session = get_object_or_404(QuizSession, pk=session_pk, user=request.user)
        
        if session.finished_at:
            messages.info(request, 'Шумо ин викторинаро аллакай анҷом додаед.')
            return redirect('quiz_result', session_pk=session.pk)
        
        # Проверка времени
        quiz = session.quiz
        time_elapsed = timezone.now() - session.started_at
        time_limit_seconds = quiz.time_limit * 60
        time_remaining = max(0, time_limit_seconds - time_elapsed.total_seconds())
        
        if time_remaining <= 0:
            messages.error(request, 'Вақти викторина ба охир расид.')
            return redirect('quiz_finish', session_pk=session.pk)
        
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
                    if next_question < len(questions):
                        return redirect(f'{request.path}?question={next_question}')
                    else:
                        return redirect('quiz_finish', session_pk=session.pk)
                
                except Answer.DoesNotExist:
                    messages.error(request, 'Ҷавоби интихобшуда нодуруст аст.')
        
        context = {
            'session': session,
            'quiz': quiz,
            'question': current_question,
            'question_index': current_question_index,
            'total_questions': len(questions),
            'previous_answer': previous_answer,
            'time_remaining': int(time_remaining),
            'time_limit': quiz.time_limit,
            'progress': int((current_question_index / len(questions)) * 100) if len(questions) > 0 else 0,
        }
        
        return render(request, 'quizzes/take.html', context)
        
    except Exception as e:
        messages.error(request, f'Хатогӣ дар иҷрои викторина: {str(e)}')
        return redirect('quiz_list')


@login_required
def quiz_finish_view(request, session_pk):
    try:
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
        
        # Создание результата
        result = Result.objects.create(
            quiz=session.quiz,
            user=session.user,
            score=score,
            total_questions=total_questions,
            correct_answers=correct_answers,
            completed_at=timezone.now()
        )
        
        # Завершение сессии
        session.finished_at = timezone.now()
        session.save()
        
        messages.success(request, f'Викторина бомуваффақият анҷом ёфт! Натиҷа: {score}/{total_questions}')
        return redirect('quiz_result', session_pk=session.pk)
        
    except Exception as e:
        messages.error(request, f'Хатогӣ дар анҷоми викторина: {str(e)}')
        return redirect('quiz_take', session_pk=session_pk)


@login_required
def quiz_result_view(request, session_pk):
    try:
        session = get_object_or_404(QuizSession, pk=session_pk, user=request.user)
        
        if not session.finished_at:
            messages.warning(request, 'Шумо ин викторинаро анҷом надодаед.')
            return redirect('quiz_take', session_pk=session.pk)
        
        # Поиск результата
        result = Result.objects.filter(
            quiz=session.quiz,
            user=request.user
        ).order_by('-completed_at').first()
        
        if not result:
            messages.error(request, 'Натиҷа ёфт нашуд.')
            return redirect('quiz_list')
        
        # Расчет процента и статуса прохождения
        percentage = (result.score / result.total_questions) * 100 if result.total_questions > 0 else 0
        is_passed = percentage >= session.quiz.pass_percentage
        
        # Получение ответов пользователя
        user_answers = session.user_answers.select_related('question', 'answer').all()
        
        # Дополнительная информация
        total_participants = QuizSession.objects.filter(
            quiz=session.quiz,
            finished_at__isnull=False
        ).count()
        
        user_rank = None
        if total_participants > 0:
            user_results = Result.objects.filter(quiz=session.quiz).order_by('-score')
            for i, res in enumerate(user_results, 1):
                if res.id == result.id:
                    user_rank = i
                    break
        
        context = {
            'session': session,
            'result': result,
            'user_answers': user_answers,
            'percentage': percentage,
            'is_passed': is_passed,
            'total_participants': total_participants,
            'user_rank': user_rank,
        }
        
        return render(request, 'quizzes/result.html', context)
        
    except Exception as e:
        messages.error(request, f'Хатогӣ дар намоиши натиҷа: {str(e)}')
        return redirect('quiz_list')


@login_required
def my_results_view(request):
    try:
        results = Result.objects.filter(user=request.user).order_by('-completed_at')
        
        # Статистика
        total_quizzes = results.count()
        total_score = sum([r.score for r in results])
        avg_score = total_score / total_quizzes if total_quizzes > 0 else 0
        
        passed_quizzes = 0
        total_percentage = 0
        
        for result in results:
            result_percentage = (result.score / result.total_questions) * 100 if result.total_questions > 0 else 0
            total_percentage += result_percentage
            
            quiz_pass_percentage = result.quiz.pass_percentage if hasattr(result.quiz, 'pass_percentage') else 60
            if result_percentage >= quiz_pass_percentage:
                passed_quizzes += 1
        
        avg_percentage = total_percentage / total_quizzes if total_quizzes > 0 else 0
        best_result = max(results, key=lambda x: x.score) if results else None
        
        # Группировка по предметам
        by_subject = {}
        for result in results:
            if hasattr(result.quiz, 'subject') and result.quiz.subject:
                subject_name = result.quiz.subject.name
                if subject_name not in by_subject:
                    by_subject[subject_name] = {
                        'count': 0,
                        'total_score': 0,
                        'passed': 0
                    }
                by_subject[subject_name]['count'] += 1
                by_subject[subject_name]['total_score'] += result.score
                
                result_percentage = (result.score / result.total_questions) * 100 if result.total_questions > 0 else 0
                quiz_pass_percentage = result.quiz.pass_percentage if hasattr(result.quiz, 'pass_percentage') else 60
                
                if result_percentage >= quiz_pass_percentage:
                    by_subject[subject_name]['passed'] += 1
        
        # Расчет средних значений
        for subject_name, data in by_subject.items():
            if data['count'] > 0:
                data['avg_score'] = data['total_score'] / data['count']
                data['pass_rate'] = (data['passed'] / data['count']) * 100 if data['count'] > 0 else 0
        
        context = {
            'results': results,
            'total_quizzes': total_quizzes,
            'avg_score': avg_score,
            'avg_percentage': avg_percentage,
            'passed_quizzes': passed_quizzes,
            'best_result': best_result,
            'by_subject': by_subject,
        }
        
        return render(request, 'results/my_results.html', context)
        
    except Exception as e:
        messages.error(request, f'Хатогӣ дар намоиши натиҷаҳо: {str(e)}')
        return redirect('dashboard')


@user_passes_test(is_teacher)
def quiz_results_view(request, quiz_pk):
    """View for displaying quiz results"""
    try:
        quiz = get_object_or_404(Quiz, pk=quiz_pk)
        
        if request.user != quiz.created_by and request.user.role != 'admin':
            messages.error(request, 'Шумо иҷозати дидани натиҷаҳои ин викторинаро надоред.')
            return redirect('quiz_list')
        
        # Get all results for this quiz
        results = Result.objects.filter(quiz=quiz).order_by('-score')
        
        # Calculate statistics
        total_participants = results.count()
        
        if total_participants > 0:
            avg_score = results.aggregate(avg=Avg('score'))['avg'] or 0
            max_score = results.aggregate(max=Max('score'))['max'] or 0
            min_score = results.aggregate(min=Min('score'))['min'] or 0
            
            # Calculate average score percentage
            total_questions = quiz.questions.count()
            avg_percentage = (avg_score / total_questions * 100) if total_questions > 0 else 0
            
            # Calculate passed/failed counts
            passed_count = 0
            for result in results:
                result_percentage = (result.score / total_questions * 100) if total_questions > 0 else 0
                if result_percentage >= quiz.pass_percentage:
                    passed_count += 1
            failed_count = total_participants - passed_count
            
            # Get top results (limit to 5)
            top_results = results[:5]
            
            # Get recent results
            recent_results = results.order_by('-completed_at')[:5]
            
            # Calculate average time (if available)
            try:
                avg_time = results.aggregate(avg=Avg('time_taken'))['avg'] or 0
            except:
                avg_time = 0
                
            # Calculate average attempts
            try:
                avg_attempts = results.aggregate(avg=Avg('attempt_number'))['avg'] or 1
            except:
                avg_attempts = 1
            
            # Add percentage to each result for template
            for result in results:
                result.score_percentage = (result.score / total_questions * 100) if total_questions > 0 else 0
        else:
            avg_score = 0
            max_score = 0
            min_score = 0
            avg_percentage = 0
            passed_count = 0
            failed_count = 0
            top_results = []
            recent_results = []
            avg_time = 0
            avg_attempts = 1
        
        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(results, 20)  # 20 results per page
        try:
            results_page = paginator.page(page)
        except PageNotAnInteger:
            results_page = paginator.page(1)
        except EmptyPage:
            results_page = paginator.page(paginator.num_pages)
        
        context = {
            'quiz': quiz,
            'results': results_page,
            'total_participants': total_participants,
            'avg_score': avg_percentage,
            'max_score': max_score,
            'min_score': min_score,
            'passed_count': passed_count,
            'failed_count': failed_count,
            'top_results': top_results,
            'recent_results': recent_results,
            'avg_time': avg_time,
            'avg_attempts': avg_attempts,
        }
        
        return render(request, 'results/quiz_results.html', context)
        
    except Exception as e:
        messages.error(request, f'Хатогӣ дар намоиши натиҷаҳои викторина: {str(e)}')
        return redirect('quiz_list')

@login_required
def check_quiz_time_view(request, pk):
    try:
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
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'is_active': False,
            'time_left_seconds': 0,
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
    """View for creating a question - SIMPLE WORKING VERSION"""
    try:
        quiz = get_object_or_404(Quiz, pk=quiz_pk)
        
        if request.user != quiz.created_by and request.user.role != 'admin':
            messages.error(request, 'Шумо иҷозати илова кардани саволро надоред.')
            return redirect('quiz_detail', pk=quiz_pk)
        
        if request.method == 'POST':
            print("=== DEBUG: POST Data ===")
            for key, value in request.POST.items():
                print(f"{key}: {value}")
            
            # Get basic question data
            text = request.POST.get('text', '').strip()
            question_type = request.POST.get('question_type', 'single_choice')
            points = request.POST.get('points', '1')
            hint = request.POST.get('hint', '').strip()
            explanation = request.POST.get('explanation', '').strip()
            
            # Basic validation
            if not text:
                messages.error(request, 'Матни саволро ворид кунед.')
                return render(request, 'questions/create.html', {
                    'quiz': quiz,
                    'error': 'Матни саволро ворид кунед.'
                })
            
            try:
                # Create question
                question = Question.objects.create(
                    quiz=quiz,
                    text=text,
                    question_type=question_type,
                    points=int(points),
                    hint=hint if hint else None,
                    explanation=explanation if explanation else None
                )
                print(f"=== DEBUG: Question created with ID {question.id} ===")
                
                # Process answers - look for answer_text_1, answer_text_2, etc.
                answers_data = []
                i = 1
                while True:
                    answer_text = request.POST.get(f'answer_text_{i}', '').strip()
                    if not answer_text:
                        # Also check for answer_text[i] format
                        answer_text = request.POST.get(f'answer_text[{i}]', '').strip()
                    
                    if not answer_text:
                        break
                    
                    is_correct = request.POST.get(f'correct_{i}', 'off') == 'on'
                    # Also check for correct[i] format
                    if not is_correct:
                        is_correct = request.POST.get(f'correct[{i}]', 'off') == 'on'
                    
                    answers_data.append({
                        'text': answer_text,
                        'is_correct': is_correct,
                        'order': i
                    })
                    i += 1
                
                print(f"=== DEBUG: Found {len(answers_data)} answers ===")
                
                # If no answers found in numbered format, try alternative approach
                if not answers_data:
                    # Look for answers in other formats
                    for key, value in request.POST.items():
                        if 'answer' in key.lower() and key != 'answers':
                            print(f"Found alternative answer key: {key} = {value}")
                
                # Create answers
                correct_count = 0
                for answer_data in answers_data:
                    Answer.objects.create(
                        question=question,
                        text=answer_data['text'],
                        is_correct=answer_data['is_correct'],
                        order=answer_data['order']
                    )
                    if answer_data['is_correct']:
                        correct_count += 1
                
                # Validate at least one correct answer
                if correct_count == 0:
                    # Try to auto-select first answer as correct if none selected
                    if answers_data:
                        first_answer = Answer.objects.filter(question=question).first()
                        if first_answer:
                            first_answer.is_correct = True
                            first_answer.save()
                            correct_count = 1
                            messages.warning(request, 'Аввалин ҷавоб ба суръати дуруст таъин карда шуд.')
                
                if correct_count == 0:
                    question.delete()
                    messages.error(request, 'Ҳадди ақал як ҷавоби дурустро интихоб кунед.')
                    return render(request, 'questions/create.html', {
                        'quiz': quiz,
                        'error': 'Ҳадди ақал як ҷавоби дурустро интихоб кунед.'
                    })
                
                messages.success(request, f'Савол "{text[:50]}{"..." if len(text) > 50 else ""}" бомуваффақият илова шуд!')
                
                # Redirect based on button pressed
                if 'save_and_add' in request.POST:
                    return redirect('question_create', quiz_pk=quiz.pk)
                else:
                    return redirect('quiz_detail', pk=quiz.pk)
                    
            except Exception as e:
                print(f"=== DEBUG: Error creating question/answers: {str(e)} ===")
                messages.error(request, f'Хатогӣ дар эҷоди савол: {str(e)}')
                return render(request, 'questions/create.html', {
                    'quiz': quiz,
                    'error': str(e)
                })
        
        else:
            # GET request - show empty form
            print(f"=== DEBUG: GET request for quiz {quiz_pk} ===")
            return render(request, 'questions/create.html', {
                'quiz': quiz
            })
        
    except Exception as e:
        print(f"=== DEBUG: Error in question_create_view: {str(e)} ===")
        import traceback
        traceback.print_exc()
        messages.error(request, f'Хатогӣ дар эҷоди савол: {str(e)}')
        return redirect('quiz_detail', pk=quiz_pk)

@user_passes_test(is_teacher)
def question_edit_view(request, pk):
    try:
        question = get_object_or_404(Question, pk=pk)
        quiz = question.quiz
        
        if request.user != quiz.created_by and request.user.role != 'admin':
            messages.error(request, 'Шумо иҷозати таҳрир кардани ин саволро надоред.')
            return redirect('quiz_detail', pk=quiz.pk)
        
        AnswerFormSet = forms.inlineformset_factory(
            Question, Answer, 
            form=AnswerForm,
            formset=AnswerInlineFormSet,
            extra=4,
            can_delete=True
        )
        
        if request.method == 'POST':
            form = QuestionForm(request.POST, instance=question)
            answer_formset = AnswerFormSet(request.POST, instance=question)
            
            if form.is_valid() and answer_formset.is_valid():
                form.save()
                answer_formset.save()
                messages.success(request, 'Савол ва ҷавобҳо бомуваффақият навсозӣ шуданд.')
                return redirect('quiz_detail', pk=quiz.pk)
        else:
            form = QuestionForm(instance=question)
            answer_formset = AnswerFormSet(instance=question)
        
        context = {
            'form': form,
            'answer_formset': answer_formset,
            'question': question,
            'quiz': quiz,
            'title': 'Таҳрири савол',
        }
        
        return render(request, 'questions/edit.html', context)
        
    except Exception as e:
        messages.error(request, f'Хатогӣ дар таҳрири савол: {str(e)}')
        return redirect('quiz_detail', pk=quiz.pk)


# Форма для редактирования вопросов с ответами
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
        
        
        
def debug_quiz_create(request):
    """Debug view to test quiz creation"""
    if request.method == 'POST':
        print("=== DEBUG POST ===")
        print(f"User: {request.user}")
        print(f"POST data: {dict(request.POST)}")
        
        try:
            # Try to create minimal quiz
            from django.utils import timezone
            import datetime
            
            quiz = Quiz.objects.create(
                title=request.POST.get('title', 'Test Quiz'),
                subject=None,  # No subject
                quiz_mode='individual',
                level_type='school',
                start_level=1,
                end_level=10,
                start_time=timezone.now(),
                end_time=timezone.now() + datetime.timedelta(days=7),
                time_limit=30,
                max_attempts=1,
                pass_percentage=60,
                created_by=request.user,
                status='draft'
            )
            
            return HttpResponse(f"SUCCESS! Quiz created with ID: {quiz.id}")
            
        except Exception as e:
            import traceback
            error_msg = f"ERROR: {str(e)}\n\n{traceback.format_exc()}"
            return HttpResponse(error_msg)
    
    return HttpResponse("""
    <form method="post">
        <input type="text" name="title" value="Test Quiz">
        <button type="submit">Test Create</button>
    </form>
    """)