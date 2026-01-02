from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    path('profile/', views.profile_view, name='profile'),
    
    path('users/', views.user_list_view, name='user_list'),
    path('users/create/', views.user_create_view, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit_view, name='user_edit'),
    
    path('subjects/', views.subject_list_view, name='subject_list'),
    path('subjects/create/', views.subject_create_view, name='subject_create'),
    
    path('groups/', views.group_list_view, name='group_list'),
    path('groups/create/', views.group_create_view, name='group_create'),
    path('groups/<int:pk>/', views.group_detail_view, name='group_detail'),
    path('groups/<int:pk>/join/', views.group_join_view, name='group_join'),
    
    path('quizzes/', views.quiz_list_view, name='quiz_list'),
    path('quizzes/create/', views.quiz_create_view, name='quiz_create'),
    path('quizzes/<int:pk>/', views.quiz_detail_view, name='quiz_detail'),
    path('quizzes/<int:pk>/edit/', views.quiz_edit_view, name='quiz_edit'),
    path('quizzes/<int:pk>/start/', views.quiz_start_view, name='quiz_start'),
    path('quizzes/<int:quiz_pk>/results/', views.quiz_results_view, name='quiz_results'),
    
    path('quiz-sessions/<int:session_pk>/take/', views.quiz_take_view, name='quiz_take'),
    path('quiz-sessions/<int:session_pk>/finish/', views.quiz_finish_view, name='quiz_finish'),
    path('quiz-sessions/<int:session_pk>/result/', views.quiz_result_view, name='quiz_result'),
    
    path('quizzes/<int:quiz_pk>/questions/create/', views.question_create_view, name='question_create'),
    path('questions/<int:pk>/edit/', views.question_edit_view, name='question_edit'),
    
    path('my-results/', views.my_results_view, name='my_results'),
    
    path('ajax/quizzes/<int:pk>/check-time/', views.check_quiz_time_view, name='check_quiz_time'),
    path('ajax/save-answer/', views.save_answer_ajax_view, name='save_answer_ajax'),
]