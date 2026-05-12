from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Result
from students.models import Student
from courses.models import Course, Enrollment
from notifications.models import Notification

@login_required
def results_list(request):
    if request.user.role not in ['uni_admin', 'lecturer']: return redirect('dashboard')
    uni = request.user.university
    if request.user.role == 'lecturer':
        try:
            courses = Course.objects.filter(lecturer=request.user.lecturer_profile, is_active=True)
        except: courses = Course.objects.none()
    else:
        courses = Course.objects.filter(university=uni, is_active=True)
    return render(request, 'results/list.html', {'courses': courses, 'unread_notifications': 0, 'pending_count': 0})

@login_required
def record_result(request):
    if request.method == 'POST':
        student = get_object_or_404(Student, id=request.POST.get('student'))
        course = get_object_or_404(Course, id=request.POST.get('course'))
        marks = float(request.POST.get('marks', 0))
        Result.objects.update_or_create(
            student=student, course=course, academic_year=student.university.academic_year,
            defaults={'marks': marks, 'semester_in_programme': student.semester_in_programme,
                     'remarks': request.POST.get('remarks', ''),
                     'recorded_by': request.user.get_full_name() or request.user.username}
        )
        messages.success(request, f'Result recorded for {student.full_name}.')
        return redirect('course_students', course_id=course.id)
    return redirect('results_list')

@login_required
def publish_results(request, course_id):
    if request.user.role not in ['uni_admin', 'lecturer']: return redirect('dashboard')
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        results = Result.objects.filter(course=course, is_published=False)
        count = results.count()
        results.update(is_published=True, date_published=timezone.now())
        for r in Result.objects.filter(course=course, is_published=True):
            Notification.objects.create(user=r.student.user, type='result', title='Results Published!',
                message=f'Your {course.name} result has been published. Grade: {r.grade}', link='/my/results/')
        messages.success(request, f'{count} results published for {course.name}.')
        return redirect('course_students', course_id=course_id)
    return redirect('course_students', course_id=course_id)

@login_required
def course_students(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    enrollments = Enrollment.objects.filter(course=course, status='enrolled').select_related('student')
    results = {r.student_id: r for r in Result.objects.filter(course=course)}
    return render(request, 'results/course_students.html', {
        'course': course, 'enrollments': enrollments, 'results': results,
        'unread_notifications': 0, 'pending_count': 0
    })
