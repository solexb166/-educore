from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from .models import FeePayment, PaymentSubmission
from students.models import Student
from notifications.models import Notification
import uuid

@login_required
def fees_list(request):
    if request.user.role not in ['uni_admin', 'finance']: return redirect('dashboard')
    uni = request.user.university
    search = request.GET.get('search', '')
    filter_status = request.GET.get('status', 'all')
    students = Student.objects.filter(university=uni, status='active').select_related('department', 'programme')
    data = []
    for s in students:
        if search and search.lower() not in s.full_name.lower() and search.lower() not in s.student_id.lower(): continue
        pct = s.payment_percentage
        status, badge = s.get_clearance_status()
        if filter_status != 'all' and status != filter_status: continue
        data.append({'student': s, 'total_paid': s.total_paid, 'balance': max(0, float(s.effective_tuition) - s.total_paid), 'percentage': round(pct, 1), 'status': status, 'badge': badge})
    pending_count = PaymentSubmission.objects.filter(student__university=uni, status='pending').count()
    return render(request, 'fees/list.html', {'student_data': data, 'search': search, 'filter_status': filter_status, 'pending_count': pending_count, 'unread_notifications': 0})

@login_required
def pending_payments(request):
    if request.user.role not in ['uni_admin', 'finance']: return redirect('dashboard')
    uni = request.user.university
    submissions = PaymentSubmission.objects.filter(student__university=uni, status='pending').select_related('student').order_by('-date_submitted')
    pending_count = submissions.count()
    return render(request, 'fees/pending_payments.html', {'submissions': submissions, 'pending_count': pending_count, 'unread_notifications': 0})

@login_required
def approve_payment(request, pk):
    if request.user.role not in ['uni_admin', 'finance']: return redirect('dashboard')
    submission = get_object_or_404(PaymentSubmission, pk=pk)
    if request.method == 'POST':
        receipt = f"RCP-{uuid.uuid4().hex[:8].upper()}"
        student = submission.student
        balance = max(0, float(student.effective_tuition) - (student.total_paid + float(submission.amount_paid)))
        FeePayment.objects.create(
            student=student, submission=submission,
            amount_paid=submission.amount_paid, currency=submission.currency,
            payment_method=submission.payment_method, receipt_number=receipt,
            semester_in_programme=submission.semester_in_programme,
            academic_year=submission.academic_year, balance=balance,
            recorded_by=request.user.get_full_name() or request.user.username,
        )
        submission.status = 'approved'
        submission.verified_by = request.user.get_full_name() or request.user.username
        submission.date_verified = timezone.now()
        submission.save()
        pct = student.payment_percentage
        uni = student.university
        msg = f'Payment of {submission.currency} {submission.amount_paid} approved. {round(pct,1)}% paid.'
        if pct >= uni.enrollment_threshold:
            msg += f' You are now enrolled!'
        Notification.objects.create(user=student.user, type='payment', title='Payment Approved!', message=msg, link='/my/fees/')
        messages.success(request, f'Payment approved for {student.full_name}. {round(pct,1)}% paid.')
        return redirect('pending_payments')
    return render(request, 'fees/approve_payment.html', {'submission': submission, 'unread_notifications': 0, 'pending_count': 0})

@login_required
def reject_payment(request, pk):
    if request.user.role not in ['uni_admin', 'finance']: return redirect('dashboard')
    submission = get_object_or_404(PaymentSubmission, pk=pk)
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        submission.status = 'rejected'
        submission.verified_by = request.user.get_full_name() or request.user.username
        submission.date_verified = timezone.now()
        submission.rejection_reason = reason
        submission.save()
        Notification.objects.create(user=submission.student.user, type='payment', title='Payment Rejected', message=f'Your payment submission was rejected. Reason: {reason}', link='/my/fees/')
        messages.warning(request, f'Payment rejected for {submission.student.full_name}.')
        return redirect('pending_payments')
    return render(request, 'fees/approve_payment.html', {'submission': submission, 'rejecting': True, 'unread_notifications': 0, 'pending_count': 0})
