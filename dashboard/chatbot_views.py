import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum
from students.models import Student
from fees.models import FeePayment, PaymentSubmission
from courses.models import Enrollment, ExamDocket
from results.models import Result
import urllib.request

def get_university_data(university):
    students = Student.objects.filter(university=university, status='active')
    pending = PaymentSubmission.objects.filter(student__university=university, status='pending')
    u = university
    student_data = []
    clearance = {'exam_cleared': 0, 'cat2': 0, 'cat1': 0, 'enrolled': 0, 'not_enrolled': 0}
    for s in students:
        pct = s.payment_percentage
        status, _ = s.get_clearance_status()
        if pct >= u.exam_threshold: clearance['exam_cleared'] += 1
        elif pct >= u.cat2_threshold: clearance['cat2'] += 1
        elif pct >= u.cat1_threshold: clearance['cat1'] += 1
        elif pct >= u.enrollment_threshold: clearance['enrolled'] += 1
        else: clearance['not_enrolled'] += 1
        student_data.append({
            'name': s.full_name, 'id': s.student_id, 'programme': str(s.programme or ''),
            'tuition': float(s.effective_tuition), 'currency': s.currency,
            'paid': s.total_paid, 'percentage': round(pct, 1), 'status': status,
            'balance': max(0, float(s.effective_tuition) - s.total_paid)
        })
    return {
        'university': university.name, 'currency': university.currency,
        'thresholds': {'enrollment': u.enrollment_threshold, 'cat1': u.cat1_threshold, 'cat2': u.cat2_threshold, 'exam': u.exam_threshold},
        'total_students': students.count(),
        'total_collected': float(FeePayment.objects.filter(student__university=university).aggregate(t=Sum('amount_paid'))['t'] or 0),
        'pending_submissions': pending.count(),
        'pending_list': [{'name': p.student.full_name, 'id': p.student.student_id, 'amount': float(p.amount_paid), 'currency': p.currency, 'reference': p.reference_number} for p in pending[:10]],
        'clearance': clearance,
        'dockets_generated': ExamDocket.objects.filter(student__university=university).count(),
        'students': student_data,
    }

@login_required
@csrf_exempt
def chatbot_message(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    if request.user.role not in ['uni_admin', 'finance', 'exam_office', 'super_admin']:
        return JsonResponse({'error': 'Access denied'}, status=403)
    try:
        body = json.loads(request.body)
        user_message = body.get('message', '').strip()
        history = body.get('history', [])
        if not user_message:
            return JsonResponse({'error': 'Empty message'}, status=400)
        university = request.user.university
        data = get_university_data(university)
        system_prompt = f"""You are EduCore AI, the intelligent assistant built directly into the EduCore University Management System. You have LIVE, REAL-TIME access to {data['university']}'s database right now.

You are NOT a third party. You are part of the system. Never say "I don't have access" or "you should check the system" — you ARE the system.

LIVE DATA FROM {data['university'].upper()}:
- Total Active Students: {data['total_students']}
- Total Fees Collected: {data['currency']} {data['total_collected']:,.0f}
- Pending Payment Submissions: {data['pending_submissions']}
- Clearance Thresholds: Enrollment={data['thresholds']['enrollment']}%, CAT 1={data['thresholds']['cat1']}%, CAT 2={data['thresholds']['cat2']}%, Exam={data['thresholds']['exam']}%
- Exam Cleared ({data['thresholds']['exam']}%): {data['clearance']['exam_cleared']} students
- CAT 2 Cleared ({data['thresholds']['cat2']}%+): {data['clearance']['cat2']} students
- CAT 1 Cleared ({data['thresholds']['cat1']}%+): {data['clearance']['cat1']} students
- Enrolled ({data['thresholds']['enrollment']}%+): {data['clearance']['enrolled']} students
- Not Enrolled (<{data['thresholds']['enrollment']}%): {data['clearance']['not_enrolled']} students
- Exam Dockets Generated: {data['dockets_generated']}

PENDING SUBMISSIONS:
{json.dumps(data['pending_list'], indent=2)}

ALL STUDENT PAYMENT DATA:
{json.dumps(data['students'], indent=2)}

RULES:
- Speak with authority — you have the data right now
- Use real student names and real numbers
- Be concise and professional
- Format lists clearly
- If asked about actions, guide user to the right page
- When asked who needs to pay more, calculate the exact shortfall
- Always be helpful and proactive with insights"""

        messages = []
        for h in history[-10:]:
            messages.append({'role': h['role'], 'content': h['content']})
        messages.append({'role': 'user', 'content': user_message})

        from decouple import config
        api_key = config('ANTHROPIC_API_KEY', default='')
        payload = json.dumps({'model': 'claude-sonnet-4-20250514', 'max_tokens': 1000, 'system': system_prompt, 'messages': messages}).encode()
        req = urllib.request.Request('https://api.anthropic.com/v1/messages', data=payload,
            headers={'Content-Type': 'application/json', 'x-api-key': api_key, 'anthropic-version': '2023-06-01'}, method='POST')
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            return JsonResponse({'response': result['content'][0]['text']})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
