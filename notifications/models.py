from django.db import models
from accounts.models import CustomUser

class Notification(models.Model):
    TYPES = [('payment','Payment'),('enrollment','Enrollment'),('result','Result'),
             ('docket','Exam Docket'),('clearance','Clearance'),('general','General')]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=TYPES, default='general')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.title}"
