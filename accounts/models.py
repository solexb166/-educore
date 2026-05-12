from django.contrib.auth.models import AbstractUser
from django.db import models
import random
import string

class CustomUser(AbstractUser):
    ROLES = [
        ('super_admin', 'EduCore Super Admin'),
        ('uni_admin', 'University Administrator'),
        ('registry', 'Registry Staff'),
        ('finance', 'Finance Staff'),
        ('lecturer', 'Lecturer'),
        ('exam_office', 'Exam Office'),
        ('student', 'Student'),
    ]
    role = models.CharField(max_length=20, choices=ROLES, default='student')
    university = models.ForeignKey('universities.University', on_delete=models.CASCADE, null=True, blank=True, related_name='users')
    phone = models.CharField(max_length=20, blank=True)
    otp = models.CharField(max_length=10, blank=True)
    must_change_password = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    profile_photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_role_display_name(self):
        return dict(self.ROLES).get(self.role, self.role)

    def generate_otp(self):
        otp = ''.join(random.choices(string.digits, k=6))
        self.otp = otp
        self.must_change_password = True
        self.save()
        return otp

    def __str__(self):
        return f"{self.username} ({self.role})"
