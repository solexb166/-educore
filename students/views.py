from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Avg
from django.utils import timezone
from .models import Student, Lecturer
from accounts.models import CustomUser
from courses.models import Enrollment, Course, ModuleSelection
from fees.models import FeePayment, PaymentSubmission
from results.models import Result
from notifications.models import Notification
from universities.models import Department, Programme

def notify(user, type, title, message, link=''):
    Notification.objects.create(user=user, type=type, title=title, message=message, link=link)

@login_required
def students_list(request):
    if request.user.role not in ['uni_admin', 'registry', 'super_admin']:
        return redirect('dashboard')
    uni = request.user.university
    search = request.GET.get('search', '')
    students = Student.objects.filter(university=uni).select_related('department', 'programme')
    if search:
        students = students.filter(full_name__icontains=search) | students.filter(student_id__icontains=search)
    return render(request, 'students/list.html', {
        'students': students, 'search': search,
        'unread_notifications': 0, 'pending_count': 0
    })

@login_required
def student_register(request):
    if request.user.role not in ['uni_admin', 'registry', 'super_admin']:
        return redirect('dashboard')
    uni = request.user.university
    departments = Department.objects.filter(university=uni)
    programmes = Programme.objects.filter(university=uni)
    otp_info = None
    if request.method == 'POST':
        username = request.POST.get('username')
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'students/register.html', {'departments': departments, 'programmes': programmes})
        user = CustomUser.objects.create_user(
            username=username, password='temp123',
            email=request.POST.get('email', ''),
            first_name=request.POST.get('first_name', ''),
            last_name=request.POST.get('last_name', ''),
            role='student', university=uni,
        )
        otp = user.generate_otp()
        dept = Department.objects.filter(id=request.POST.get('department')).first()
        prog = Programme.objects.filter(id=request.POST.get('programme')).first()
        student = Student.objects.create(
            user=user, university=uni, department=dept, programme=prog,
            student_id=request.POST.get('student_id'),
            full_name=request.POST.get('full_name'),
            gender=request.POST.get('gender', ''),
            phone=request.POST.get('phone', ''),
            student_type=request.POST.get('student_type', 'local'),
            mode_of_study=request.POST.get('mode_of_study', 'full_time'),
            semester_in_programme=int(request.POST.get('semester_in_programme', 1)),
            tuition_amount=request.POST.get('tuition_amount', 0),
            currency=request.POST.get('currency', uni.currency),
            scholarship_percentage=int(request.POST.get('scholarship_percentage', 0)),
            nationality=request.POST.get('nationality', ''),
        )
        notify(user, 'general', 'Welcome to EduCore!', f'Your account has been created. Use your username and OTP to login for the first time.', '/login/')
        otp_info = {'student_name': student.full_name, 'username': username, 'otp': otp, 'student_id': student.student_id}
        return render(request, 'students/register.html', {'departments': departments, 'programmes': programmes, 'otp_info': otp_info})
    return render(request, 'students/register.html', {'departments': departments, 'programmes': programmes})

@login_required
def student_detail(request, pk):
    if request.user.role not in ['uni_admin', 'registry', 'super_admin']:
        return redirect('dashboard')
    student = get_object_or_404(Student, pk=pk)
    return render(request, 'students/detail.html', {
        'student': student,
        'enrollments': Enrollment.objects.filter(student=student).select_related('course'),
        'results': Result.objects.filter(student=student).select_related('course'),
        'payments': FeePayment.objects.filter(student=student).order_by('-payment_date'),
        'unread_notifications': 0, 'pending_count': 0
    })

@login_required
def my_dashboard(request):
    if request.user.role != 'student':
        return redirect('dashboard')
    try:
        student = request.user.student_profile
        enrollments = Enrollment.objects.filter(student=student, status='enrolled').select_related('course')
        results = Result.objects.filter(student=student, is_published=True)
        avg = results.aggregate(a=Avg('marks'))['a'] or 0
        payments = FeePayment.objects.filter(student=student).order_by('-payment_date')
        latest = payments.first()
        balance = max(0, float(student.effective_tuition) - student.total_paid)
        pending_subs = PaymentSubmission.objects.filter(student=student, status='pending').count()
        unread = Notification.objects.filter(user=request.user, is_read=False).count()
    except:
        student = enrollments = results = None
        avg = balance = pending_subs = unread = 0
        payments = []
    return render(request, 'students/my_dashboard.html', {
        'student': student, 'enrollments': enrollments, 'results': results,
        'avg_marks': round(avg, 1), 'balance': balance, 'pending_subs': pending_subs,
        'unread_notifications': unread, 'pending_count': 0,
    })

@login_required
def upload_photo(request):
    if request.user.role != 'student': return redirect('dashboard')
    try:
        student = request.user.student_profile
        if request.method == 'POST' and request.FILES.get('photo'):
            student.photo = request.FILES['photo']
            student.save()
            messages.success(request, 'Profile photo updated.')
    except: messages.error(request, 'Error updating photo.')
    return redirect('my_dashboard')

@login_required
def select_modules(request):
    if request.user.role != 'student': return redirect('dashboard')
    try:
        student = request.user.student_profile
    except:
        messages.error(request, 'Student profile not found.')
        return redirect('dashboard')
    uni = student.university
    sem = student.semester_in_programme
    available = Course.objects.filter(university=uni, semester_in_programme=sem, is_active=True).select_related('lecturer', 'department')
    selected_ids = list(ModuleSelection.objects.filter(student=student, academic_year=uni.academic_year, semester_in_programme=sem).values_list('course_id', flat=True))
    enrolled_ids = list(Enrollment.objects.filter(student=student, academic_year=uni.academic_year, semester_in_programme=sem).values_list('course_id', flat=True))
    if request.method == 'POST':
        course_ids = request.POST.getlist('courses')
        if not course_ids:
            messages.error(request, 'Please select at least one module.')
        else:
            ModuleSelection.objects.filter(student=student, academic_year=uni.academic_year, semester_in_programme=sem, status='pending').delete()
            for cid in course_ids:
                c = Course.objects.filter(id=cid, university=uni).first()
                if c and int(cid) not in enrolled_ids:
                    ModuleSelection.objects.get_or_create(student=student, course=c, academic_year=uni.academic_year, defaults={'semester_in_programme': sem, 'status': 'pending'})
            messages.success(request, f'{len(course_ids)} module(s) selected. Pay {uni.enrollment_threshold}% of your tuition to confirm enrollment.')
            return redirect('my_courses')
    return render(request, 'students/select_modules.html', {
        'available_courses': available, 'selected_ids': selected_ids, 'enrolled_ids': enrolled_ids,
        'student': student, 'sem': sem, 'unread_notifications': 0, 'pending_count': 0
    })

@login_required
def my_courses(request):
    if request.user.role != 'student': return redirect('dashboard')
    try:
        student = request.user.student_profile
        enrollments = Enrollment.objects.filter(student=student, status='enrolled').select_related('course')
        selections = ModuleSelection.objects.filter(student=student, status='pending').select_related('course')
    except: student = enrollments = selections = None
    return render(request, 'students/my_courses.html', {
        'enrollments': enrollments, 'selections': selections, 'student': student,
        'unread_notifications': 0, 'pending_count': 0
    })

@login_required
def my_results(request):
    if request.user.role != 'student': return redirect('dashboard')
    try:
        student = request.user.student_profile
        results = Result.objects.filter(student=student, is_published=True).select_related('course')
        avg = results.aggregate(a=Avg('marks'))['a'] or 0
    except: results = []; avg = 0; student = None
    return render(request, 'students/my_results.html', {
        'results': results, 'average': round(avg, 1), 'student': student,
        'unread_notifications': 0, 'pending_count': 0
    })

@login_required
def my_transcript(request):
    if request.user.role != 'student': return redirect('dashboard')
    try:
        student = request.user.student_profile
        results = Result.objects.filter(student=student, is_published=True).select_related('course').order_by('semester_in_programme', 'course__course_code')
        total_credits = sum(r.course.credits for r in results)
        total_points = sum(r.gpa_points * r.course.credits for r in results)
        cgpa = round(total_points / total_credits, 2) if total_credits > 0 else 0
    except: student = results = None; cgpa = 0
    return render(request, 'students/transcript.html', {
        'student': student, 'results': results, 'cgpa': cgpa,
        'unread_notifications': 0, 'pending_count': 0
    })

@login_required
def my_fees(request):
    if request.user.role != 'student': return redirect('dashboard')
    try:
        student = request.user.student_profile
        payments = FeePayment.objects.filter(student=student).order_by('-payment_date')
        submissions = PaymentSubmission.objects.filter(student=student).order_by('-date_submitted')
        balance = max(0, float(student.effective_tuition) - student.total_paid)
    except: student = None; payments = submissions = []; balance = 0
    return render(request, 'students/my_fees.html', {
        'student': student, 'payments': payments, 'submissions': submissions, 'balance': balance,
        'unread_notifications': 0, 'pending_count': 0
    })

@login_required
def submit_payment(request):
    if request.user.role != 'student': return redirect('dashboard')
    try: student = request.user.student_profile
    except: messages.error(request, 'Student profile not found.'); return redirect('dashboard')
    if request.method == 'POST':
        sub = PaymentSubmission.objects.create(
            student=student, bank_name=request.POST.get('bank_name', ''),
            payment_method=request.POST.get('payment_method', 'bank'),
            reference_number=request.POST.get('reference_number'),
            amount_paid=request.POST.get('amount_paid'),
            currency=student.currency,
            semester_in_programme=student.semester_in_programme,
            academic_year=student.university.academic_year,
            notes=request.POST.get('notes', ''),
        )
        if request.FILES.get('receipt_image'):
            sub.receipt_image = request.FILES['receipt_image']
            sub.save()
        messages.success(request, 'Payment submitted successfully. Finance will verify it shortly.')
        notify(request.user, 'payment', 'Payment Submitted', f'Your payment of {student.currency} {sub.amount_paid} has been submitted for verification.', '/my/fees/')
        return redirect('my_fees')
    return render(request, 'students/submit_payment.html', {
        'student': student, 'unread_notifications': 0, 'pending_count': 0
    })

@login_required
def proof_of_registration(request):
    if request.user.role != 'student': return redirect('dashboard')
    try:
        student = request.user.student_profile
        uni = student.university
        if student.payment_percentage < uni.enrollment_threshold:
            messages.error(request, f'You need to pay at least {uni.enrollment_threshold}% of your tuition to print proof of registration.')
            return redirect('my_fees')
        enrollments = Enrollment.objects.filter(student=student, status='enrolled').select_related('course')
        balance = max(0, float(student.effective_tuition) - student.total_paid)
    except: messages.error(request, 'Student profile not found.'); return redirect('dashboard')
    return render(request, 'students/proof_of_registration.html', {
        'student': student, 'enrollments': enrollments, 'balance': balance,
        'today': timezone.now(), 'unread_notifications': 0, 'pending_count': 0
    })

@login_required
def my_exam_docket(request):
    if request.user.role != 'student': return redirect('dashboard')
    try:
        student = request.user.student_profile
        uni = student.university
        from courses.models import ExamDocket
        docket = ExamDocket.objects.filter(student=student, academic_year=uni.academic_year).first()
        if not docket:
            messages.error(request, 'Your exam docket has not been generated yet. Contact the Exam Office.')
            return redirect('my_courses')
        if student.payment_percentage < uni.exam_threshold:
            messages.error(request, f'You need to pay {uni.exam_threshold}% of your tuition to access your exam docket.')
            return redirect('my_fees')
        enrollments = Enrollment.objects.filter(student=student, status='enrolled').select_related('course')
    except Exception as e:
        messages.error(request, 'Exam docket not found.')
        return redirect('dashboard')
    return render(request, 'students/exam_docket.html', {
        'student': student, 'docket': docket, 'enrollments': enrollments,
        'today': timezone.now(), 'unread_notifications': 0, 'pending_count': 0
    })
