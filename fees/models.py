from django.db import models
from students.models import Student
from universities.models import University

class FeeType(models.Model):
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='fee_types')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_mandatory = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.university.short_name} - {self.name}"

class PaymentSubmission(models.Model):
    STATUS = [('pending','Pending'),('approved','Approved'),('rejected','Rejected')]
    METHODS = [('bank','Bank Transfer'),('mobile_money','Mobile Money'),
               ('card','Card Payment'),('cash','Cash'),('other','Other')]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payment_submissions')
    bank_name = models.CharField(max_length=100, blank=True)
    payment_method = models.CharField(max_length=20, choices=METHODS, default='bank')
    reference_number = models.CharField(max_length=100)
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=5, default='UGX')
    semester_in_programme = models.IntegerField(default=1)
    academic_year = models.CharField(max_length=20)
    date_submitted = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    verified_by = models.CharField(max_length=100, blank=True)
    date_verified = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    receipt_image = models.ImageField(upload_to='receipts/', null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.student} - {self.reference_number}"

class FeePayment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    submission = models.OneToOneField(PaymentSubmission, on_delete=models.SET_NULL, null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=5, default='UGX')
    payment_date = models.DateTimeField(auto_now_add=True)
    receipt_number = models.CharField(max_length=50, unique=True)
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    semester_in_programme = models.IntegerField(default=1)
    academic_year = models.CharField(max_length=20)
    recorded_by = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._auto_enroll()

    def _auto_enroll(self):
        from django.utils import timezone
        from courses.models import ModuleSelection, Enrollment
        student = self.student
        university = student.university
        if student.payment_percentage >= university.enrollment_threshold:
            pending = ModuleSelection.objects.filter(
                student=student, status='pending', academic_year=self.academic_year)
            for sel in pending:
                Enrollment.objects.get_or_create(
                    student=student, course=sel.course, academic_year=self.academic_year,
                    defaults={'semester_in_programme': sel.semester_in_programme, 'status': 'enrolled'})
                sel.status = 'enrolled'
                sel.date_enrolled = timezone.now()
                sel.save()

    def __str__(self):
        return f"{self.student} - {self.receipt_number}"
