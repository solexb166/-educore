from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from accounts import views as auth_views
from dashboard import views as dash_views
from dashboard import chatbot_views
from students import views as student_views
from courses import views as course_views
from fees import views as fee_views
from results import views as result_views
from universities import views as uni_views
from notifications import views as notif_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dash_views.landing, name='landing'),
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('change-password/', auth_views.change_password, name='change_password'),

    # Dashboard
    path('dashboard/', dash_views.dashboard, name='dashboard'),
    path('analytics/', dash_views.analytics, name='analytics'),
    path('reports/', dash_views.reports, name='reports'),

    # Chatbot
    path('chatbot/message/', chatbot_views.chatbot_message, name='chatbot_message'),

    # Universities
    path('universities/', uni_views.universities_list, name='universities_list'),
    path('universities/create/', uni_views.university_create, name='university_create'),
    path('universities/<int:pk>/settings/', uni_views.university_settings, name='university_settings'),
    path('universities/<int:pk>/onboard/', uni_views.university_onboard, name='university_onboard'),
    path('super-analytics/', uni_views.super_analytics, name='super_analytics'),

    # Departments & Programmes
    path('departments/', uni_views.departments_list, name='departments_list'),
    path('programmes/', uni_views.programmes_list, name='programmes_list'),

    # Students
    path('students/', student_views.students_list, name='students_list'),
    path('students/register/', student_views.student_register, name='student_register'),
    path('students/<int:pk>/', student_views.student_detail, name='student_detail'),

    # Student Portal
    path('my/', student_views.my_dashboard, name='my_dashboard'),
    path('my/photo/', student_views.upload_photo, name='upload_photo'),
    path('my/courses/', student_views.my_courses, name='my_courses'),
    path('my/modules/select/', student_views.select_modules, name='select_modules'),
    path('my/results/', student_views.my_results, name='my_results'),
    path('my/transcript/', student_views.my_transcript, name='my_transcript'),
    path('my/fees/', student_views.my_fees, name='my_fees'),
    path('my/fees/submit/', student_views.submit_payment, name='submit_payment'),
    path('my/proof-of-registration/', student_views.proof_of_registration, name='proof_of_registration'),
    path('my/exam-docket/', student_views.my_exam_docket, name='my_exam_docket'),

    # Courses
    path('courses/', course_views.courses_list, name='courses_list'),
    path('courses/create/', course_views.course_create, name='course_create'),
    path('enrollments/', course_views.enrollments_list, name='enrollments_list'),
    path('enrollments/enroll/', course_views.enroll_student, name='enroll_student'),
    path('exam-office/', course_views.exam_office_dashboard, name='exam_office_dashboard'),
    path('exam-office/generate/', course_views.generate_dockets, name='generate_dockets'),
    path('exam-office/clearance/', course_views.clearance_list, name='clearance_list'),

    # Fees
    path('fees/', fee_views.fees_list, name='fees_list'),
    path('fees/pending/', fee_views.pending_payments, name='pending_payments'),
    path('fees/approve/<int:pk>/', fee_views.approve_payment, name='approve_payment'),
    path('fees/reject/<int:pk>/', fee_views.reject_payment, name='reject_payment'),

    # Results
    path('results/', result_views.results_list, name='results_list'),
    path('results/record/', result_views.record_result, name='record_result'),
    path('results/publish/<int:course_id>/', result_views.publish_results, name='publish_results'),
    path('results/course/<int:course_id>/', result_views.course_students, name='course_students'),

    # Users
    path('users/', auth_views.users_list, name='users_list'),
    path('users/create/', auth_views.create_user, name='create_user'),
    path('users/<int:pk>/edit/', auth_views.edit_user, name='edit_user'),
    path('users/<int:pk>/delete/', auth_views.delete_user, name='delete_user'),

    # Notifications
    path('notifications/', notif_views.notifications_list, name='notifications_list'),
    path('notifications/<int:pk>/read/', notif_views.mark_read, name='mark_read'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'core.views.custom_404'
handler500 = 'core.views.custom_500'
