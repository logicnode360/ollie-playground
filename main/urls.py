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
]