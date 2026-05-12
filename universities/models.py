from django.db import models

class University(models.Model):
    CURRENCIES = [('USD','USD'),('UGX','UGX'),('KES','KES'),('TZS','TZS'),
                  ('GHS','GHS'),('NGN','NGN'),('ZAR','ZAR'),('EUR','EUR'),('GBP','GBP')]
    STATUS = [('active','Active'),('trial','Trial'),('suspended','Suspended')]

    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=50, blank=True)
    logo = models.ImageField(upload_to='university_logos/', null=True, blank=True)
    primary_color = models.CharField(max_length=7, default='#0D1B5E')
    secondary_color = models.CharField(max_length=7, default='#C9A84C')
    country = models.CharField(max_length=100, default='Uganda')
    city = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    currency = models.CharField(max_length=5, choices=CURRENCIES, default='UGX')
    motto = models.CharField(max_length=200, blank=True)
    academic_year = models.CharField(max_length=20, default='2025/2026')
    enrollment_threshold = models.IntegerField(default=30, help_text="% to enroll")
    cat1_threshold = models.IntegerField(default=50, help_text="% for CAT 1")
    cat2_threshold = models.IntegerField(default=75, help_text="% for CAT 2")
    exam_threshold = models.IntegerField(default=100, help_text="% for exams")
    grading_scale = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='trial')
    subscription_plan = models.CharField(max_length=20, default='trial')
    created_at = models.DateTimeField(auto_now_add=True)
    trial_ends = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)

    def get_default_grading(self):
        return {'A': 80, 'B': 70, 'C': 60, 'D': 50, 'F': 0}

    def calculate_grade(self, marks):
        scale = self.grading_scale or self.get_default_grading()
        if marks >= scale.get('A', 80): return 'A'
        elif marks >= scale.get('B', 70): return 'B'
        elif marks >= scale.get('C', 60): return 'C'
        elif marks >= scale.get('D', 50): return 'D'
        return 'F'

    def __str__(self):
        return self.name

class Department(models.Model):
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    head = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.university.short_name} - {self.name}"

class Programme(models.Model):
    LEVELS = [('certificate','Certificate'),('diploma','Diploma'),
              ('bachelor','Bachelor'),('master','Master'),('phd','PhD')]
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='programmes')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20)
    level = models.CharField(max_length=20, choices=LEVELS, default='bachelor')
    duration_years = models.IntegerField(default=3)
    total_semesters = models.IntegerField(default=6)

    def __str__(self):
        return f"{self.code} - {self.name}"
