from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('student/<int:student_id>/', views.student_detail, name='student_detail'),
    path('schedule/', views.schedule_page, name='schedule'),
    
    # Добавляем недостающие пути, чтобы убрать 404 ошибку
    # ВАЖНО: используй дефис '-', если в браузере переходишь по /mark-grades/
    path('mark-grades/', views.mark_grades, name='mark_grades'),
    path('mark-attendance/', views.attendance_report, name='attendance'),
]