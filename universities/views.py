from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import University, Department, Programme
from accounts.models import CustomUser

def university_create(request):
    if request.method == 'POST':
        uni = University.objects.create(
            name=request.POST.get('name'),
            short_name=request.POST.get('short_name', ''),
            country=request.POST.get('country', 'Uganda'),
            city=request.POST.get('city', ''),
            email=request.POST.get('email', ''),
            phone=request.POST.get('phone', ''),
            currency=request.POST.get('currency', 'UGX'),
            primary_color=request.POST.get('primary_color', '#1E3A8A'),
            secondary_color=request.POST.get('secondary_color', '#10B981'),
            status='trial',
        )
        if request.FILES.get('logo'):
            uni.logo = request.FILES['logo']
            uni.save()
        username = request.POST.get('admin_username')
        password = request.POST.get('admin_password')
        if username and password:
            admin = CustomUser.objects.create_user(
                username=username, password=password,
                email=request.POST.get('email', ''),
                first_name=request.POST.get('admin_name', ''),
                role='uni_admin', university=uni,
            )
        messages.success(request, f'Welcome to EduCore! {uni.name} is registered. Sign in with your admin credentials to get started.')
        return redirect('login')
    return render(request, 'universities/create.html')

@login_required
def universities_list(request):
    if request.user.role != 'super_admin':
        return redirect('dashboard')
    universities = University.objects.all().order_by('-created_at')
    return render(request, 'universities/list.html', {
        'universities': universities,
        'unread_notifications': 0, 'pending_count': 0
    })

@login_required
def university_settings(request, pk):
    uni = get_object_or_404(University, pk=pk)
    if request.user.role not in ['uni_admin', 'super_admin'] or (request.user.role == 'uni_admin' and request.user.university != uni):
        return redirect('dashboard')
    if request.method == 'POST':
        uni.name = request.POST.get('name', uni.name)
        uni.short_name = request.POST.get('short_name', uni.short_name)
        uni.currency = request.POST.get('currency', uni.currency)
        uni.primary_color = request.POST.get('primary_color', uni.primary_color)
        uni.secondary_color = request.POST.get('secondary_color', uni.secondary_color)
        uni.academic_year = request.POST.get('academic_year', uni.academic_year)
        uni.enrollment_threshold = int(request.POST.get('enrollment_threshold', uni.enrollment_threshold))
        uni.cat1_threshold = int(request.POST.get('cat1_threshold', uni.cat1_threshold))
        uni.cat2_threshold = int(request.POST.get('cat2_threshold', uni.cat2_threshold))
        uni.exam_threshold = int(request.POST.get('exam_threshold', uni.exam_threshold))
        uni.motto = request.POST.get('motto', uni.motto)
        uni.address = request.POST.get('address', uni.address)
        uni.email = request.POST.get('email', uni.email)
        uni.phone = request.POST.get('phone', uni.phone)
        uni.website = request.POST.get('website', uni.website)
        if request.FILES.get('logo'):
            uni.logo = request.FILES['logo']
        uni.save()
        messages.success(request, 'University settings updated successfully.')
        return redirect('university_settings', pk=pk)
    return render(request, 'universities/settings.html', {
        'uni': uni, 'unread_notifications': 0, 'pending_count': 0
    })

@login_required
def university_onboard(request, pk):
    uni = get_object_or_404(University, pk=pk)
    return render(request, 'universities/onboard.html', {'uni': uni, 'unread_notifications': 0, 'pending_count': 0})

@login_required
def super_analytics(request):
    if request.user.role != 'super_admin':
        return redirect('dashboard')
    import json
    universities = University.objects.all()
    context = {
        'total_universities': universities.count(),
        'active_universities': universities.filter(status='active').count(),
        'trial_universities': universities.filter(status='trial').count(),
        'total_students': __import__('students').models.Student.objects.count(),
        'universities': universities,
        'unread_notifications': 0, 'pending_count': 0,
    }
    return render(request, 'universities/super_analytics.html', context)

@login_required
def departments_list(request):
    uni = request.user.university
    departments = Department.objects.filter(university=uni)
    if request.method == 'POST':
        Department.objects.create(university=uni, name=request.POST.get('name'), code=request.POST.get('code'), head=request.POST.get('head', ''))
        messages.success(request, 'Department created.')
        return redirect('departments_list')
    return render(request, 'universities/departments.html', {'departments': departments, 'unread_notifications': 0, 'pending_count': 0})

@login_required
def programmes_list(request):
    uni = request.user.university
    programmes = Programme.objects.filter(university=uni)
    departments = Department.objects.filter(university=uni)
    if request.method == 'POST':
        dept = Department.objects.filter(id=request.POST.get('department')).first()
        Programme.objects.create(university=uni, department=dept, name=request.POST.get('name'),
            code=request.POST.get('code'), level=request.POST.get('level', 'bachelor'),
            duration_years=int(request.POST.get('duration_years', 3)))
        messages.success(request, 'Programme created.')
        return redirect('programmes_list')
    return render(request, 'universities/programmes.html', {'programmes': programmes, 'departments': departments, 'unread_notifications': 0, 'pending_count': 0})
