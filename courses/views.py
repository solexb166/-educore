from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Course, Enrollment, ModuleSelection, ExamDocket
from students.models import Student
from universities.models import Department
from notifications.models import Notification

@login_required
def courses_list(request):
    uni = request.user.university
    if request.user.role == 'lecturer':
        try:
            courses = Course.objects.filter(lecturer=request.user.lecturer_profile, is_active=True)
        except: courses = Course.objects.none()
    else:
        courses = Course.objects.filter(university=uni, is_active=True).order_by('semester_in_programme', 'course_code')
    return render(request, 'courses/list.html', {'courses': courses, 'unread_notifications': 0, 'pending_count': 0})

@login_required
def course_create(request):
    if request.user.role not in ['uni_admin', 'registry']: return redirect('dashboard')
    uni = request.user.university
    departments = Department.objects.filter(university=uni)
    from students.models import Lecturer
    lecturers = Lecturer.objects.filter(university=uni)
    if request.method == 'POST':
        dept = Department.objects.filter(id=request.POST.get('department')).first()
        lec = Lecturer.objects.filter(id=request.POST.get('lecturer')).first() if request.POST.get('lecturer') else None
        Course.objects.create(
            university=uni, department=dept, lecturer=lec,
            course_code=request.POST.get('course_code'),
            name=request.POST.get('name'),
            credits=int(request.POST.get('credits', 3)),
            semester_in_programme=int(request.POST.get('semester_in_programme', 1)),
            max_enrollment=int(request.POST.get('max_enrollment', 50)),
            description=request.POST.get('description', ''),
            is_elective=request.POST.get('is_elective') == 'on',
        )
        messages.success(request, 'Course created successfully.')
        return redirect('courses_list')
    return render(request, 'courses/create.html', {'departments': departments, 'lecturers': lecturers, 'unread_notifications': 0, 'pending_count': 0})

@login_required
def enrollments_list(request):
    uni = request.user.university
    enrollments = Enrollment.objects.filter(student__university=uni).select_related('student', 'course').order_by('-date_enrolled')
    return render(request, 'courses/enrollments.html', {'enrollments': enrollments, 'unread_notifications': 0, 'pending_count': 0})

@login_required
def enroll_student(request):
    if request.method == 'POST':
        student = get_object_or_404(Student, id=request.POST.get('student'))
        course = get_object_or_404(Course, id=request.POST.get('course'))
        _, created = Enrollment.objects.get_or_create(student=student, course=course,
            academic_year=student.university.academic_year,
            defaults={'semester_in_programme': course.semester_in_programme, 'status': 'enrolled'})
        if created: messages.success(request, f'{student.full_name} enrolled in {course.name}.')
        else: messages.warning(request, 'Student already enrolled.')
        return redirect('enrollments_list')
    return redirect('enrollments_list')

@login_required
def exam_office_dashboard(request):
    uni = request.user.university
    students = Student.objects.filter(university=uni, status='active')
    cleared = [s for s in students if s.payment_percentage >= uni.exam_threshold]
    not_cleared = [s for s in students if s.payment_percentage < uni.exam_threshold]
    dockets = ExamDocket.objects.filter(student__university=uni, academic_year=uni.academic_year).count()
    return render(request, 'exam_office/dashboard.html', {
        'cleared_count': len(cleared), 'not_cleared_count': len(not_cleared),
        'dockets_generated': dockets, 'total_students': students.count(),
        'unread_notifications': 0, 'pending_count': 0
    })

@login_required
def generate_dockets(request):
    if request.method == 'POST':
        uni = request.user.university
        generated = 0
        for s in Student.objects.filter(university=uni, status='active'):
            if s.payment_percentage >= uni.exam_threshold:
                _, created = ExamDocket.objects.get_or_create(student=s, academic_year=uni.academic_year,
                    defaults={'semester_in_programme': s.semester_in_programme, 'generated_by': request.user.get_full_name() or request.user.username})
                if created:
                    generated += 1
                    Notification.objects.create(user=s.user, type='docket', title='Exam Docket Ready!',
                        message='Your exam entry docket has been generated. You can now print it from your portal.', link='/my/exam-docket/')
        messages.success(request, f'{generated} exam docket(s) generated.')
        return redirect('exam_office_dashboard')
    return redirect('exam_office_dashboard')

@login_required
def clearance_list(request):
    uni = request.user.university
    clearance_type = request.GET.get('type', 'enrollment')
    thresholds = {'enrollment': uni.enrollment_threshold, 'cat1': uni.cat1_threshold, 'cat2': uni.cat2_threshold, 'exam': uni.exam_threshold}
    labels = {'enrollment': f'Enrollment Clearance ({uni.enrollment_threshold}%)', 'cat1': f'CAT 1 Clearance ({uni.cat1_threshold}%)', 'cat2': f'CAT 2 Clearance ({uni.cat2_threshold}%)', 'exam': f'Final Exam Clearance ({uni.exam_threshold}%)'}
    threshold = thresholds.get(clearance_type, uni.enrollment_threshold)
    cleared, not_cleared = [], []
    for s in Student.objects.filter(university=uni, status='active'):
        pct = s.payment_percentage
        entry = {'student': s, 'percentage': round(pct, 1)}
        if pct >= threshold:
            cleared.append(entry)
        else:
            entry['shortfall'] = max(0, (threshold / 100 * float(s.effective_tuition)) - s.total_paid)
            not_cleared.append(entry)
    return render(request, 'exam_office/clearance_list.html', {
        'cleared': cleared, 'not_cleared': not_cleared, 'clearance_type': clearance_type,
        'label': labels.get(clearance_type, ''), 'threshold': threshold,
        'unread_notifications': 0, 'pending_count': 0
    })

@login_required
def course_students(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.user.role == 'lecturer':
        try:
            if course.lecturer != request.user.lecturer_profile:
                messages.error(request, 'Access denied.')
                return redirect('results_list')
        except: return redirect('dashboard')
    enrollments = Enrollment.objects.filter(course=course, status='enrolled').select_related('student')
    from results.models import Result
    results_dict = {r.student_id: r for r in Result.objects.filter(course=course)}
    return render(request, 'results/course_students.html', {
        'course': course, 'enrollments': enrollments, 'results_dict': results_dict,
        'unread_notifications': 0, 'pending_count': 0
    })
