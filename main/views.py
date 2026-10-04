# views.py
import time
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from .models import Question, ExamAttempt, Profile, Notification

# --- INDEX & AUTH VIEWS ---
def index_view(request):
    return render(request, 'index.html')

def login_view(request):
    if request.method == "POST":
        u_name = request.POST.get('username')
        p_word = request.POST.get('password')
        user = authenticate(request, username=u_name, password=p_word)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'index.html')

def enroll_view(request):
    if request.method == "POST":
        u_name = request.POST.get('username')
        email = request.POST.get('email')
        p_word = request.POST.get('password')

        if User.objects.filter(username=u_name).exists():
            messages.error(request, "Username is already taken.")
            return redirect('index')

        user = User.objects.create_user(username=u_name, email=email, password=p_word)
        Profile.objects.get_or_create(user=user)
        login(request, user)
        messages.success(request, "Account created successfully!")
        return redirect('dashboard')

    return redirect('index')

def logout_view(request):
    logout(request)
    return redirect('index')

# --- ADMIN LOGIN VIEW ---
def admin_login_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_panel')

    if request.method == "POST":
        u_name = request.POST.get('username')
        p_word = request.POST.get('password')

        if p_word != 'oluchi@098321':
            messages.error(request, "Invalid administrator password.")
            return render(request, 'admin_login.html')

        user = authenticate(request, username=u_name, password=p_word)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_panel')
        else:
            messages.error(request, "Invalid credentials or insufficient permissions.")

    return render(request, 'admin_login.html')

# --- DASHBOARD VIEW ---
@login_required
def dashboard_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    attempts = ExamAttempt.objects.filter(user=request.user).order_by('-date_taken')

    attempts_count = attempts.count()
    highest_score = max([a.percentage for a in attempts], default=0)

    # Week-specific question counts (matches database 'week1', 'week2')
    w1_count = Question.objects.filter(week='week1').count()
    w2_count = Question.objects.filter(week='week2').count()

    context = {
        'payment_status': profile.payment_status,
        'attempts': attempts,
        'attempts_count': attempts_count,
        'highest_score': round(highest_score, 1),
        'w1_count': w1_count,
        'w2_count': w2_count,
    }
    return render(request, 'dashboard.html', context)

@login_required
def confirm_payment_view(request):
    if request.method == "POST":
        profile, _ = Profile.objects.get_or_create(user=request.user)
        profile.payment_status = 'PENDING'
        profile.save()

        Notification.objects.create(
            message=f"{request.user.username} submitted payment confirmation.",
            link_name='admin_panel',
        )
        messages.info(request, "Payment confirmation submitted. An administrator will review your account soon.")
    return redirect('dashboard')
@login_required
def exam_view(request, week='week1'):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if profile.payment_status != 'APPROVED':
        messages.error(request, "Your access has not been approved yet.")
        return redirect('dashboard')

    # Question.week is stored lowercase ('week1' / 'week2'), so use it as-is
    db_week = week.lower()

    # Check retake gate
    if not profile.retake_approved:
        latest_attempt = ExamAttempt.objects.filter(user=request.user, week=db_week).order_by('-date_taken').first()
        return render(request, 'exam.html', {
            'retake_locked': True,
            'retake_requested': profile.retake_requested,
            'latest_attempt': latest_attempt,
            'selected_week': week,
        })

    questions = Question.objects.filter(week=db_week)

    if not questions.exists():
        messages.warning(request, f"No questions currently available for {db_week}.")
        return redirect('dashboard')  # Return to dashboard if empty

    return render(request, 'exam.html', {
        'questions': questions,
        'is_review': False,
        'retake_locked': False,
        'selected_week': week,
    })

@login_required
def submit_exam_view(request):
    if request.method == "POST":
        profile, _ = Profile.objects.get_or_create(user=request.user)
        week = request.POST.get('week', 'week1')
        questions = Question.objects.filter(week=week)
        total_questions = questions.count()

        if total_questions == 0:
            messages.error(request, "No questions were found for this exam.")
            return redirect('dashboard')

        correct_count = 0
        user_answers = {}

        for question in questions:
            selected_option = request.POST.get(f"question_{question.id}")
            if selected_option:
                user_answers[str(question.id)] = selected_option
                if selected_option == question.correct_option:
                    correct_count += 1

        percentage = (correct_count / total_questions) * 100 if total_questions > 0 else 0

        # Calculate time spent
        started_at_ms = request.POST.get('exam_started_at_ms')
        time_taken_seconds = None
        if started_at_ms:
            try:
                start_sec = int(started_at_ms) / 1000.0
                time_taken_seconds = int(time.time() - start_sec)
            except ValueError:
                pass

        attempt = ExamAttempt.objects.create(
            user=request.user,
            score=correct_count,
            total_questions=total_questions,
            percentage=round(percentage, 1),
            user_answers=user_answers,
            time_taken_seconds=time_taken_seconds,
            week=week
        )

        # Lock retakes until student reviews and requests approval
        profile.retake_approved = False
        profile.retake_requested = False
        profile.save()

        messages.success(request, f"Exam submitted! You scored {correct_count}/{total_questions} ({round(percentage, 1)}%).")
        return redirect('exam_review', attempt_id=attempt.id)

    return redirect('dashboard')

@login_required
def exam_review_view(request, attempt_id):
    attempt = get_object_or_404(ExamAttempt, id=attempt_id, user=request.user)
    questions = Question.objects.filter(week=attempt.week)

    questions_data = []
    for q in questions:
        q_copy = q
        q_copy.user_answer = attempt.user_answers.get(str(q.id), None)
        questions_data.append(q_copy)

    return render(request, 'exam.html', {
        'is_review': True,
        'attempt': attempt,
        'questions': questions_data,
        'score': attempt.score,
        'total': attempt.total_questions,
        'percentage': attempt.percentage,
        'selected_week': attempt.week,
    })

@login_required
def request_retake_view(request):
    if request.method == "POST":
        profile, _ = Profile.objects.get_or_create(user=request.user)
        profile.retake_requested = True
        profile.save()

        Notification.objects.create(
            message=f"{request.user.username} requested exam retake approval.",
            link_name='admin_panel',
        )
        messages.success(request, "Retake request sent to administrator.")
    return redirect('dashboard')

# --- ADMIN PANEL VIEWS ---
def is_admin(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_admin)
def admin_panel_view(request):
    pending_payments = Profile.objects.filter(payment_status='PENDING')
    retake_requests = Profile.objects.filter(retake_requested=True)
    approved_users = Profile.objects.filter(payment_status='APPROVED')

    for profile in approved_users:
        latest = ExamAttempt.objects.filter(user=profile.user).order_by('-date_taken').first()
        profile.latest_score = latest.percentage if latest else None

    notifications = Notification.objects.filter(is_read=False)

    context = {
        'total_questions': Question.objects.count(),
        'total_students': User.objects.filter(is_staff=False).count(),
        'pending_payments': pending_payments,
        'retake_requests': retake_requests,
        'approved_users': approved_users,
        'notifications': notifications,
        'unread_notifications_count': notifications.count(),
    }
    return render(request, 'admin-panel.html', context)

@user_passes_test(is_admin)
def process_payment(request, profile_id, action):
    profile = get_object_or_404(Profile, id=profile_id)
    if action == 'approve':
        profile.payment_status = 'APPROVED'
        messages.success(request, f"Approved payment for {profile.user.username}.")
    elif action == 'deny':
        profile.payment_status = 'DENIED'
        messages.warning(request, f"Denied payment for {profile.user.username}.")
    profile.save()
    return redirect('admin_panel')

@user_passes_test(is_admin)
def process_retake(request, profile_id, action):
    profile = get_object_or_404(Profile, id=profile_id)
    if action == 'approve':
        profile.retake_approved = True
        profile.retake_requested = False
        messages.success(request, f"Unlocked retake for {profile.user.username}.")
    elif action == 'deny':
        profile.retake_requested = False
        messages.warning(request, f"Denied retake for {profile.user.username}.")
    profile.save()
    return redirect('admin_panel')

@user_passes_test(is_admin)
def admin_student_scores_view(request, user_id):
    student = get_object_or_404(User, id=user_id)
    attempts = ExamAttempt.objects.filter(user=student).order_by('-date_taken')
    return render(request, 'admin_student_scores.html', {'student': student, 'attempts': attempts})

@user_passes_test(is_admin)
def admin_attempt_review_view(request, attempt_id):
    attempt = get_object_or_404(ExamAttempt, id=attempt_id)
    questions = Question.objects.filter(week=attempt.week)

    questions_data = []
    for q in questions:
        q_copy = q
        q_copy.user_answer = attempt.user_answers.get(str(q.id), None)
        questions_data.append(q_copy)

    return render(request, 'exam.html', {
        'is_review': True,
        'is_admin_view': True,
        'reviewed_student': attempt.user,
        'attempt': attempt,
        'questions': questions_data,
        'score': attempt.score,
        'total': attempt.total_questions,
        'percentage': attempt.percentage,
        'selected_week': attempt.week,
    })

@user_passes_test(is_admin)
def mark_notification_read(request, notification_id):
    note = get_object_or_404(Notification, id=notification_id)
    note.is_read = True
    note.save()
    return redirect('admin_panel')

@user_passes_test(is_admin)
def mark_all_notifications_read(request):
    Notification.objects.filter(is_read=False).update(is_read=True)
    return redirect('admin_panel')