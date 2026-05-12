from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Avg, Count
from students.models import Student, Lecturer
from courses.models import Course, Enrollment
from fees.models import FeePayment, PaymentSubmission
from results.models import Result
from notifications.models import Notification
from universities.models import University

def landing(request):
    stats = {
        'universities': University.objects.filter(status='active').count() or 12,
        'students': Student.objects.count() or 45000,
        'countries': 8,
    }
    return render(request, 'landing.html', {'stats': stats})

@login_required
def dashboard(request):
    user = request.user
    if user.must_change_password:
        return redirect('change_password')
    if user.role == 'student':
        return redirect('my_dashboard')
    if user.role == 'exam_office':
        return redirect('exam_office_dashboard')

    uni = user.university
    context = {
        'pending_count': PaymentSubmission.objects.filter(student__university=uni, status='pending').count() if uni else 0,
        'unread_notifications': Notification.objects.filter(user=user, is_read=False).count(),
    }

    if user.role in ['uni_admin', 'super_admin']:
        students = Student.objects.filter(university=uni)
        context.update({
            'total_students': students.count(),
            'total_courses': Course.objects.filter(university=uni, is_active=True).count(),
            'total_enrollments': Enrollment.objects.filter(student__university=uni, status='enrolled').count(),
            'ugx_fees': float(FeePayment.objects.filter(student__university=uni, currency='UGX').aggregate(t=Sum('amount_paid'))['t'] or 0),
            'usd_fees': float(FeePayment.objects.filter(student__university=uni, currency='USD').aggregate(t=Sum('amount_paid'))['t'] or 0),
            'other_fees': float(FeePayment.objects.filter(student__university=uni).exclude(currency__in=['UGX','USD']).aggregate(t=Sum('amount_paid'))['t'] or 0),
            'exam_cleared': sum(1 for s in students if s.payment_percentage >= uni.exam_threshold),
            'not_enrolled': sum(1 for s in students if s.payment_percentage < uni.enrollment_threshold),
            'recent_payments': PaymentSubmission.objects.filter(student__university=uni).order_by('-date_submitted')[:5],
        })
        # Chart data
        from django.utils import timezone
        import json
        months = []
        for i in range(6, 0, -1):
            from datetime import date
            import calendar
            today = date.today()
            month = (today.month - i) % 12 + 1
            year = today.year if today.month - i > 0 else today.year - 1
            amt = float(FeePayment.objects.filter(student__university=uni, payment_date__month=month, payment_date__year=year).aggregate(t=Sum('amount_paid'))['t'] or 0)
            months.append({'month': calendar.month_abbr[month], 'amount': amt})
        context['chart_data'] = json.dumps(months)
        context['enrollment_data'] = json.dumps([
            {'label': 'Exam Cleared', 'value': context['exam_cleared'], 'color': '#10B981'},
            {'label': 'CAT 2', 'value': sum(1 for s in students if s.payment_percentage >= uni.cat2_threshold and s.payment_percentage < uni.exam_threshold), 'color': '#3B82F6'},
            {'label': 'CAT 1', 'value': sum(1 for s in students if s.payment_percentage >= uni.cat1_threshold and s.payment_percentage < uni.cat2_threshold), 'color': '#F59E0B'},
            {'label': 'Enrolled', 'value': sum(1 for s in students if s.payment_percentage >= uni.enrollment_threshold and s.payment_percentage < uni.cat1_threshold), 'color': '#8B5CF6'},
            {'label': 'Not Enrolled', 'value': context['not_enrolled'], 'color': '#EF4444'},
        ])

    elif user.role == 'finance':
        students = Student.objects.filter(university=uni)
        context.update({
            'exam_cleared': sum(1 for s in students if s.payment_percentage >= uni.exam_threshold),
            'cat2_cleared': sum(1 for s in students if s.payment_percentage >= uni.cat2_threshold),
            'cat1_cleared': sum(1 for s in students if s.payment_percentage >= uni.cat1_threshold),
            'enrolled': sum(1 for s in students if s.payment_percentage >= uni.enrollment_threshold),
            'not_enrolled': sum(1 for s in students if s.payment_percentage < uni.enrollment_threshold),
            'ugx_fees': float(FeePayment.objects.filter(student__university=uni, currency='UGX').aggregate(t=Sum('amount_paid'))['t'] or 0),
            'usd_fees': float(FeePayment.objects.filter(student__university=uni, currency='USD').aggregate(t=Sum('amount_paid'))['t'] or 0),
        })

    elif user.role == 'lecturer':
        try:
            lecturer = user.lecturer_profile
            my_courses = Course.objects.filter(lecturer=lecturer, is_active=True)
            context.update({
                'my_courses': my_courses,
                'total_courses': my_courses.count(),
                'total_students': Enrollment.objects.filter(course__in=my_courses, status='enrolled').values('student').distinct().count(),
                'results_entered': Result.objects.filter(course__in=my_courses).count(),
                'results_published': Result.objects.filter(course__in=my_courses, is_published=True).count(),
            })
        except: pass

    elif user.role == 'registry':
        context.update({
            'total_students': Student.objects.filter(university=uni).count(),
            'total_courses': Course.objects.filter(university=uni).count(),
            'total_enrollments': Enrollment.objects.filter(student__university=uni, status='enrolled').count(),
        })

    return render(request, 'dashboard/dashboard.html', context)

@login_required
def analytics(request):
    if request.user.role not in ['uni_admin', 'super_admin']:
        return redirect('dashboard')
    uni = request.user.university
    import json
    students = Student.objects.filter(university=uni)
    context = {
        'total_students': students.count(),
        'total_enrolled': Enrollment.objects.filter(student__university=uni, status='enrolled').count(),
        'avg_marks': Result.objects.filter(student__university=uni).aggregate(a=Avg('marks'))['a'] or 0,
        'total_fees': float(FeePayment.objects.filter(student__university=uni).aggregate(t=Sum('amount_paid'))['t'] or 0),
        'unread_notifications': 0,
        'pending_count': 0,
    }
    # Grade distribution
    grades = Result.objects.filter(student__university=uni).values('grade').annotate(count=Count('grade'))
    context['grade_data'] = json.dumps([{'grade': g['grade'], 'count': g['count']} for g in grades])
    # Programme distribution
    prog_data = students.values('programme__name').annotate(count=Count('id')).order_by('-count')[:5]
    context['programme_data'] = json.dumps([{'name': p['programme__name'] or 'Unknown', 'count': p['count']} for p in prog_data])
    return render(request, 'dashboard/analytics.html', context)

@login_required
def reports(request):
    if request.user.role not in ['uni_admin', 'finance', 'super_admin']:
        return redirect('dashboard')
    uni = request.user.university
    context = {
        'total_students': Student.objects.filter(university=uni).count(),
        'total_courses': Course.objects.filter(university=uni).count(),
        'total_enrollments': Enrollment.objects.filter(student__university=uni, status='enrolled').count(),
        'ugx_fees': float(FeePayment.objects.filter(student__university=uni, currency='UGX').aggregate(t=Sum('amount_paid'))['t'] or 0),
        'usd_fees': float(FeePayment.objects.filter(student__university=uni, currency='USD').aggregate(t=Sum('amount_paid'))['t'] or 0),
        'total_results': Result.objects.filter(student__university=uni).count(),
        'avg_marks': round(float(Result.objects.filter(student__university=uni).aggregate(a=Avg('marks'))['a'] or 0), 1),
        'pending_submissions': PaymentSubmission.objects.filter(student__university=uni, status='pending').count(),
        'unread_notifications': 0,
        'pending_count': 0,
    }
    return render(request, 'dashboard/reports.html', context)
