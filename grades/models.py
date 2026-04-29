from django.db import models

class Student(models.Model):
    full_name = models.CharField("ФИО ученика", max_length=200)

    class Meta:
        verbose_name = "Ученик"
        verbose_name_plural = "Ученики"

    def __str__(self):
        return self.full_name

class Subject(models.Model):
    name = models.CharField("Название предмета", max_length=100)

    class Meta:
        verbose_name = "Предмет"
        verbose_name_plural = "Предметы"

    def __str__(self):
        return self.name

class Record(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="Ученик")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name="Предмет", null=True)
    date = models.DateField("Дата")
    is_present = models.BooleanField("Присутствие", default=True)
    grade = models.IntegerField("Оценка", choices=[(i, i) for i in range(1, 6)], null=True, blank=True)

    class Meta:
        verbose_name = "Запись"
        verbose_name_plural = "Записи"