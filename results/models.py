from django.db import models
from students.models import Student
from courses.models import Course

class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='results')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='results')
    marks = models.FloatField(default=0)
    grade = models.CharField(max_length=5, blank=True)
    academic_year = models.CharField(max_length=20)
    semester_in_programme = models.IntegerField(default=1)
    remarks = models.TextField(blank=True)
    recorded_by = models.CharField(max_length=100, blank=True)
    is_published = models.BooleanField(default=False)
    date_recorded = models.DateTimeField(auto_now_add=True)
    date_published = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'course', 'academic_year')

    def save(self, *args, **kwargs):
        self.grade = self.student.university.calculate_grade(self.marks)
        super().save(*args, **kwargs)

    @property
    def gpa_points(self):
        mapping = {'A': 4.0, 'B': 3.0, 'C': 2.0, 'D': 1.0, 'F': 0.0}
        return mapping.get(self.grade, 0)

    def __str__(self):
        return f"{self.student} - {self.course} - {self.grade}"
