from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('login/', views.login_view, name='login'),
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('enroll/', views.enroll_view, name='enroll'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('confirm-payment/', views.confirm_payment_view, name='confirm_payment'),
    path('exam/', views.exam_view, name='exam'),
    path('submit-exam/', views.submit_exam_view, name='submit_exam'),
    path('admin-panel/', views.admin_panel_view, name='admin_panel'),
    path('admin-panel/payment/<int:profile_id>/<str:action>/', views.process_payment, name='process_payment'),
    path('exam/review/<int:attempt_id>/', views.exam_review_view, name='exam_review'),
    path('exam/request-retake/', views.request_retake_view, name='request_retake'),
    path('admin-panel/retake/<int:profile_id>/<str:action>/', views.process_retake, name='process_retake'),
    path('admin-panel/student/<int:user_id>/scores/', views.admin_student_scores_view, name='admin_student_scores'),
    path('admin-panel/notification/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('admin-panel/notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
]