from django.db import models
from universities.models import University, Department
from students.models import Student, Lecturer

class Course(models.Model):
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='courses')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    lecturer = models.ForeignKey(Lecturer, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses')
    course_code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    credits = models.IntegerField(default=3)
    semester_in_programme = models.IntegerField(default=1)
    max_enrollment = models.IntegerField(default=50)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_elective = models.BooleanField(default=False)

    class Meta:
        unique_together = ('university', 'course_code')

    @property
    def enrolled_count(self):
        return self.enrollments.filter(status='enrolled').count()

    def __str__(self):
        return f"{self.course_code} - {self.name}"

class ModuleSelection(models.Model):
    STATUS = [('pending','Pending Payment'),('enrolled','Enrolled'),('dropped','Dropped')]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='module_selections')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='selections')
    academic_year = models.CharField(max_length=20)
    semester_in_programme = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    date_selected = models.DateTimeField(auto_now_add=True)
    date_enrolled = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'course', 'academic_year')

class Enrollment(models.Model):
    STATUS = [('enrolled','Enrolled'),('dropped','Dropped'),('completed','Completed')]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    academic_year = models.CharField(max_length=20)
    semester_in_programme = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS, default='enrolled')
    date_enrolled = models.DateTimeField(auto_now_add=True)
    attendance_percentage = models.FloatField(default=0)

    class Meta:
        unique_together = ('student', 'course', 'academic_year')

class ExamDocket(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_dockets')
    academic_year = models.CharField(max_length=20)
    semester_in_programme = models.IntegerField(default=1)
    date_generated = models.DateTimeField(auto_now_add=True)
    generated_by = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, default='generated')
