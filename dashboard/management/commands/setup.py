from django.core.management.base import BaseCommand
from accounts.models import CustomUser
from universities.models import University

class Command(BaseCommand):
    help = 'Create initial EduCore super admin and demo university'

    def handle(self, *args, **kwargs):
        # Create demo university
        if not University.objects.filter(name='Demo University').exists():
            uni = University.objects.create(
                name='Demo University',
                short_name='DU',
                country='Uganda',
                city='Kampala',
                currency='UGX',
                status='active',
                academic_year='2025/2026',
                enrollment_threshold=30,
                cat1_threshold=50,
                cat2_threshold=75,
                exam_threshold=100,
            )
            self.stdout.write('Demo University created')
        else:
            uni = University.objects.get(name='Demo University')
            self.stdout.write('Demo University already exists')

        # Create super admin
        if not CustomUser.objects.filter(username='superadmin').exists():
            CustomUser.objects.create_superuser(
                'superadmin', 'solomonbitrus166@gmail.com', 'EduCore2026!',
                role='super_admin', must_change_password=False
            )
            self.stdout.write('Super admin created: superadmin / EduCore2026!')
        else:
            self.stdout.write('Super admin already exists')

        # Create university admin
        if not CustomUser.objects.filter(username='admin').exists():
            CustomUser.objects.create_superuser(
                'admin', 'admin@demo.edu', 'admin1234',
                role='uni_admin', university=uni, must_change_password=False
            )
            self.stdout.write('University admin created: admin / admin1234')
        else:
            self.stdout.write('University admin already exists')

        self.stdout.write(self.style.SUCCESS('Setup complete!'))
