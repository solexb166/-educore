from django.db import models
from universities.models import University, Department, Programme

class Student(models.Model):
    STUDENT_TYPES = [('local','Local'),('international','International'),('exchange','Exchange')]
    MODES = [('full_time','Full Time'),('part_time','Part Time'),('distance','Distance Learning'),('online','Online')]
    STATUS = [('active','Active'),('deferred','Deferred'),('graduated','Graduated'),('expelled','Expelled'),('suspended','Suspended')]

    user = models.OneToOneField('accounts.CustomUser', on_delete=models.CASCADE, related_name='student_profile')
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='students')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    programme = models.ForeignKey(Programme, on_delete=models.SET_NULL, null=True, blank=True)
    student_id = models.CharField(max_length=30)
    full_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    next_of_kin = models.CharField(max_length=100, blank=True)
    next_of_kin_phone = models.CharField(max_length=20, blank=True)
    student_type = models.CharField(max_length=20, choices=STUDENT_TYPES, default='local')
    mode_of_study = models.CharField(max_length=20, choices=MODES, default='full_time')
    semester_in_programme = models.IntegerField(default=1)
    tuition_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=5, default='UGX')
    admission_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS, default='active')
    photo = models.ImageField(upload_to='student_photos/', null=True, blank=True)
    sponsorship = models.CharField(max_length=100, blank=True)
    scholarship_percentage = models.IntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('university', 'student_id')

    @property
    def effective_tuition(self):
        discount = self.scholarship_percentage / 100
        return float(self.tuition_amount) * (1 - discount)

    @property
    def total_paid(self):
        from django.db.models import Sum
        # Only sum payments in the same currency as the student's tuition
        return float(self.payments.filter(currency=self.currency).aggregate(t=Sum('amount_paid'))['t'] or 0)

    @property
    def payment_percentage(self):
        if self.effective_tuition == 0: return 0
        return min((self.total_paid / self.effective_tuition) * 100, 100)

    @property
    def year_of_study(self):
        return (self.semester_in_programme + 1) // 2

    def get_clearance_status(self):
        u = self.university
        pct = self.payment_percentage
        if pct >= u.exam_threshold: return 'Exam Cleared', 'success'
        elif pct >= u.cat2_threshold: return f'CAT 2 Cleared', 'info'
        elif pct >= u.cat1_threshold: return f'CAT 1 Cleared', 'warning'
        elif pct >= u.enrollment_threshold: return 'Enrolled', 'primary'
        return 'Not Enrolled', 'danger'

    def __str__(self):
        return f"{self.student_id} - {self.full_name}"

class Lecturer(models.Model):
    user = models.OneToOneField('accounts.CustomUser', on_delete=models.CASCADE, related_name='lecturer_profile')
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='lecturers')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    lecturer_id = models.CharField(max_length=30)
    full_name = models.CharField(max_length=100)
    qualification = models.CharField(max_length=100, blank=True)
    specialization = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.lecturer_id} - {self.full_name}"
