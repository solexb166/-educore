from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomUser
import datetime

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if user.must_change_password:
                return redirect('change_password')
            if user.role == 'student':
                return redirect('my_dashboard')
            return redirect('dashboard')
        try:
            u = CustomUser.objects.get(username=username)
            if u.otp and u.otp == password:
                login(request, u)
                return redirect('change_password')
        except CustomUser.DoesNotExist:
            pass
        messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html', {'year': datetime.datetime.now().year})

def logout_view(request):
    logout(request)
    return redirect('/')

@login_required
def change_password(request):
    if request.method == 'POST':
        new_pass = request.POST.get('new_password')
        confirm = request.POST.get('confirm_password')
        if new_pass != confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/change_password.html')
        if len(new_pass) < 6:
            messages.error(request, 'Password must be at least 6 characters.')
            return render(request, 'accounts/change_password.html')
        request.user.set_password(new_pass)
        request.user.must_change_password = False
        request.user.otp = ''
        request.user.save()
        update_session_auth_hash(request, request.user)
        messages.success(request, 'Password updated successfully!')
        if request.user.role == 'student':
            return redirect('my_dashboard')
        return redirect('dashboard')
    return render(request, 'accounts/change_password.html')

@login_required
def users_list(request):
    if request.user.role not in ['uni_admin', 'super_admin']:
        return redirect('dashboard')
    university = request.user.university
    users = CustomUser.objects.filter(university=university).order_by('role')
    courses = []
    try:
        from courses.models import Course
        courses = Course.objects.filter(university=university, is_active=True)
    except: pass
    return render(request, 'accounts/users.html', {'users': users, 'courses': courses})

@login_required
def create_user(request):
    if request.user.role not in ['uni_admin', 'super_admin']:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('users_list')
        role = request.POST.get('role', 'registry')
        user = CustomUser.objects.create_user(
            username=username, password=request.POST.get('password'),
            email=request.POST.get('email', ''), first_name=request.POST.get('first_name', ''),
            last_name=request.POST.get('last_name', ''), role=role,
            university=request.user.university,
        )
        if role == 'lecturer':
            from students.models import Lecturer, Department
            from courses.models import Course
            dept = Department.objects.filter(id=request.POST.get('department')).first()
            lec = Lecturer.objects.create(user=user, university=request.user.university,
                department=dept, lecturer_id=f"LEC{user.id:04d}",
                full_name=f"{request.POST.get('first_name','')} {request.POST.get('last_name','')}".strip(),
                specialization=request.POST.get('specialization',''))
            for cid in request.POST.getlist('courses'):
                c = Course.objects.filter(id=cid).first()
                if c: c.lecturer = lec; c.save()
        messages.success(request, f'User {username} created.')
        return redirect('users_list')
    return redirect('users_list')

@login_required
def edit_user(request, pk):
    if request.user.role not in ['uni_admin', 'super_admin']:
        return redirect('dashboard')
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.role = request.POST.get('role', user.role)
        new_username = request.POST.get('username', '').strip()
        if new_username and new_username != user.username:
            if not CustomUser.objects.filter(username=new_username).exclude(pk=pk).exists():
                user.username = new_username
        new_pass = request.POST.get('new_password', '')
        if new_pass: user.set_password(new_pass)
        user.save()
        messages.success(request, 'User updated successfully.')
        return redirect('users_list')
    return render(request, 'accounts/edit_user.html', {'edit_user': user})

@login_required
def delete_user(request, pk):
    if request.user.role not in ['uni_admin', 'super_admin']:
        return redirect('dashboard')
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted.')
        return redirect('users_list')
    return render(request, 'accounts/delete_user.html', {'edit_user': user})
