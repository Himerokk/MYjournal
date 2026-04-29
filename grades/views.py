from django.db.models import Avg
from django.shortcuts import render, get_object_or_404, redirect  
from .models import Student, Subject, Record
from django.utils import timezone
# ВАЖНО: Импортируем нашу функцию из созданного файла services.py
from .services import get_schedule 

def schedule_page(request):
    schedule_data = get_schedule()
    # Берем, например, первые 10 найденных элементов, чтобы не перегружать страницу
    return render(request, 'grades/schedule.html', {
        'schedule': schedule_data[:10],
    })

def index(request):
    # Получаем дату из календаря или сегодня
    date_str = request.GET.get('date')
    if date_str:
        try:
            target_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            target_date = timezone.now().date()
    else:
        target_date = timezone.now().date()

    students = Student.objects.all()
    data = []

    for student in students:
        # 1. Находим ВСЕ записи этого студента за конкретный день
        records_today = Record.objects.filter(
            student=student, 
            date=target_date
        ).order_by('id')[:5] # Берем первые 5 созданных записей за день
        
        indicators = []
        is_any_present = False
        
        # 2. Заполняем индикаторы на основе существующих записей
        for record in records_today:
            if record.is_present:
                indicators.append('present')
                is_any_present = True
            else:
                indicators.append('absent')
        
        # 3. Добиваем список до 5 элементов "пустыми" (серыми) точками
        while len(indicators) < 5:
            indicators.append('none')

        data.append({
            'student': student,
            'is_present': is_any_present,
            'indicators': indicators
        })
    
    return render(request, 'grades/index.html', {
        'data': data,
        'today': target_date
    })

def student_detail(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    selected_date = request.GET.get('date')
    
    # 1. Получаем ВСЕ записи для статистики
    all_records = Record.objects.filter(student=student)
    
    # Расчет статистики (всегда по полной истории)
    avg_grade = all_records.filter(grade__isnull=False).aggregate(Avg('grade'))['grade__avg']
    avg_grade = round(avg_grade, 1) if avg_grade else "—"
    
    total_recs = all_records.count()
    attendance_percent = round((all_records.filter(is_present=True).count() / total_recs) * 100) if total_recs > 0 else 0

    # 2. Фильтруем записи для отображения в списке
    if selected_date and selected_date != "":
        display_records = all_records.filter(date=selected_date)
    else:
        display_records = all_records.order_by('-date')
        selected_date = None # Сбрасываем в None для корректной работы шаблона

    # 3. Группировка (по ВСЕМ предметам, чтобы они не исчезали)
    all_subjects = Subject.objects.all() 
    performance = {subj: display_records.filter(subject=subj) for subj in all_subjects}

    return render(request, 'grades/student_detail.html', {
        'student': student,
        'performance': performance,
        'selected_date': selected_date,
        'avg_grade': avg_grade,
        'attendance_percent': attendance_percent,
    })

def mark_grades(request): # Или как называется твоя функция для этого шаблона
    subjects = Subject.objects.all()
    students = Student.objects.all()
    
    # Получаем дату и предмет из запроса
    date_str = request.POST.get('date') or request.GET.get('date')
    subject_id = request.POST.get('subject') or request.GET.get('subject')
    
    # Логика определения даты (как делали раньше)
    if date_str:
        try:
            selected_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()

    if request.method == 'POST':
        subject_obj = get_object_or_404(Subject, id=subject_id)
        
        for student in students:
            # Получаем оценку из инпута
            grade_val = request.POST.get(f'grade_{student.id}')
            
            # Сохраняем в модель Record
            # Если поле пустое, записываем None (или 0)
            Record.objects.update_or_create(
                student=student,
                subject=subject_obj,
                date=selected_date,
                defaults={
                    'grade': int(grade_val) if grade_val and grade_val.isdigit() else None,
                    # Можно автоматически ставить «Присутствовал», если поставлена оценка
                    'is_present': True if grade_val else True 
                }
            )
        return redirect(f"{request.path}?subject={subject_id}&date={selected_date}")

    # --- САМОЕ ВАЖНОЕ: ПОЛУЧЕНИЕ ДАННЫХ ДЛЯ ОТОБРАЖЕНИЯ ---
    # Создаем словарь {student_id: grade}, чтобы подставить в инпуты
    existing_grades = {}
    if subject_id:
        records = Record.objects.filter(subject_id=subject_id, date=selected_date)
        for r in records:
            existing_grades[r.student_id] = r.grade

    # Привязываем оценку напрямую к каждому студенту для простоты в шаблоне
    for student in students:
        student.current_grade = existing_grades.get(student.id, "")

    return render(request, 'admin/mark_grades.html', {
        'subjects': subjects,
        'students': students,
        'selected_date': selected_date,
        'current_subject_id': int(subject_id) if subject_id and str(subject_id).isdigit() else None,
        # 'existing_grades' теперь можно даже не передавать, если используешь student.current_grade
    })

def attendance_report(request):
    subjects = Subject.objects.all()
    students = Student.objects.all()
    
    # 1. Сначала пытаемся взять дату из POST (сохранение), 
    # потом из GET (переключение фильтра), если везде пусто — сегодня.
    date_str = request.POST.get('date') or request.GET.get('date')
    
    if date_str:
        try:
            # Превращаем строку в объект даты для корректной работы фильтров Django
            if isinstance(date_str, str):
                selected_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                selected_date = date_str
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()

    # Достаем ID предмета из GET-запроса для фильтрации (чтобы он не сбрасывался на первый в списке)
    current_subject_id = request.GET.get('subject')

    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        subject_obj = get_object_or_404(Subject, id=subject_id)
        
        for student in students:
            status = request.POST.get(f'attendance_{student.id}')
            Record.objects.update_or_create(
                student=student,
                subject=subject_obj,
                date=selected_date,
                defaults={'is_present': True if status else False}
            )
        
        # После сохранения возвращаем на ту же дату и тот же предмет
        return redirect(f"{request.path}?subject={subject_id}&date={selected_date}")

    # Важно: передаем именно 'selected_date', так как он используется в value="{{ selected_date|date:'Y-m-d' }}"
    return render(request, 'admin/mark_attendance.html', {
        'subjects': subjects,
        'students': students,
        'selected_date': selected_date,
        'current_subject': int(current_subject_id) if current_subject_id else None
    })