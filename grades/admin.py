from django.contrib import admin
from django.urls import path
from django.template.response import TemplateResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.contrib import messages

# Импортируем модели
from .models import Student, Subject, Record

# Настройка заголовков
admin.site.site_header = "Панель ITHub"
admin.site.index_title = "Управление обучением"

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name',)
    search_fields = ('full_name',)

@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'is_present', 'grade')
    list_filter = ('date', 'subject', 'is_present')
    search_fields = ('student__full_name',)
    date_hierarchy = 'date'
    ordering = ('-date',)

    # --- РЕГИСТРАЦИЯ URL ДЛЯ НОВЫХ ВКЛАДОК ---
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('mark-grades/', self.admin_site.admin_view(self.mark_grades_view), name='mark-grades'),
            path('mark-attendance/', self.admin_site.admin_view(self.mark_attendance_view), name='mark-attendance'),
        ]
        return custom_urls + urls

    # --- ЖУРНАЛ ОЦЕНОК ---
    def mark_grades_view(self, request):
        subject_id = request.GET.get('subject') or request.POST.get('subject')
        date_val = request.GET.get('date') or request.POST.get('date') or str(timezone.now().date())

        if request.method == 'POST':
            subject = Subject.objects.get(id=subject_id)
            for key, value in request.POST.items():
                if key.startswith('grade_') and value:
                    student_id = key.replace('grade_', '')
                    Record.objects.update_or_create(
                        student_id=student_id,
                        subject=subject,
                        date=date_val,
                        defaults={'grade': value, 'is_present': True}
                    )
            messages.success(request, f"Оценки на {date_val} сохранены!")
            return redirect(f"{request.path}?subject={subject_id}&date={date_val}")

        students_data = []
        for student in Student.objects.all().order_by('full_name'):
            rec = Record.objects.filter(student=student, subject_id=subject_id, date=date_val).first()
            students_data.append({
                'id': student.id,
                'full_name': student.full_name,
                'grade': rec.grade if rec else ""
            })

        context = {
            **self.admin_site.each_context(request),
            'students': students_data,
            'subjects': Subject.objects.all(),
            'current_subject': int(subject_id) if subject_id else None,
            'current_date': date_val,
            'title': 'Электронный журнал оценок',
        }
        return TemplateResponse(request, "admin/mark_grades.html", context)

    # --- ЖУРНАЛ ПОСЕЩАЕМОСТИ ---
    def mark_attendance_view(self, request):
        subject_id = request.GET.get('subject') or request.POST.get('subject')
        date_val = request.GET.get('date') or request.POST.get('date') or str(timezone.now().date())

        if request.method == 'POST':
            subject = Subject.objects.get(id=subject_id)
            present_student_ids = request.POST.getlist('is_present')
            
            for student in Student.objects.all():
                is_present = str(student.id) in present_student_ids
                # update_or_create предотвращает дубликаты на один день
                Record.objects.update_or_create(
                    student=student,
                    subject=subject,
                    date=date_val,
                    defaults={'is_present': is_present}
                )
            messages.success(request, f"Посещаемость на {date_val} сохранена!")
            return redirect(f"{request.path}?subject={subject_id}&date={date_val}")

        students_data = []
        for student in Student.objects.all().order_by('full_name'):
            rec = Record.objects.filter(student=student, subject_id=subject_id, date=date_val).first()
            students_data.append({
                'id': student.id,
                'full_name': student.full_name,
                'is_present': rec.is_present if rec else False
            })

        context = {
            **self.admin_site.each_context(request),
            'students': students_data,
            'subjects': Subject.objects.all(),
            'current_subject': int(subject_id) if subject_id else None,
            'current_date': date_val,
            'title': 'Журнал присутствия',
        }
        return TemplateResponse(request, "admin/mark_attendance.html", context)