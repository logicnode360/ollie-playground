from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Question, ExamAttempt, Profile, Notification

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
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('admin_panel')
        else:
            messages.error(request, "Account does not have administrative permissions or username is incorrect.")

    return render(request, 'admin_login.html')


# --- REGULAR VIEWS ---
def index_view(request):
    if request.user.is_staff:
        return redirect('admin_panel')

    if request.user.is_authenticated and not request.user.is_staff:
        return redirect('dashboard')

    context = {
        'total_questions': Question.objects.count(),
    }
    return render(request, 'index.html', context)

def login_view(request):
    if request.method == "POST":
        u_name = request.POST.get('username')
        p_word = request.POST.get('password')
        user = authenticate(request, username=u_name, password=p_word)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, "Invalid username or password.")
    return redirect('index')

def enroll_view(request):
    if request.method == "POST":
        u_name = request.POST.get('username')
        email = request.POST.get('email')
        p_word = request.POST.get('password')

        if User.objects.filter(username=u_name).exists():
            messages.error(request, "Username already exists.")
            return redirect('index')

        user = User.objects.create_user(username=u_name, email=email, password=p_word)
        Profile.objects.create(user=user)

        login(request, user)
        messages.success(request, "Enrollment successful! Please complete your payment to access the exam.")
        return redirect('dashboard')
    return redirect('index')

def logout_view(request):
    logout(request)
    return redirect('index')

@login_required
def dashboard_view(request):
    if request.user.is_staff:
        return redirect('admin_panel')

    attempts = ExamAttempt.objects.filter(user=request.user).order_by('-date_taken')
    attempts_count = attempts.count()
    highest_score = max([att.percentage for att in attempts], default=0)

    context = {
        'attempts': attempts,
        'attempts_count': attempts_count,
        'highest_score': round(highest_score, 1),
        'payment_status': request.user.profile.payment_status,
    }
    return render(request, 'dashboard.html', context)

@login_required
def confirm_payment_view(request):
    if request.method == "POST":
        profile = request.user.profile
        profile.payment_status = 'PENDING'
        profile.save()
        messages.info(request, "Payment submitted! Admin approval is pending.")
    return redirect('dashboard')

@login_required
def exam_view(request):
    profile = request.user.profile
    if profile.payment_status != 'APPROVED':
        messages.error(request, "Your payment must be approved before you can start the exam.")
        return redirect('dashboard')

    has_prior_attempt = ExamAttempt.objects.filter(user=request.user).exists()

    # Only gate retakes -- first attempt is always allowed.
    if has_prior_attempt and not profile.retake_approved:
        latest_attempt = ExamAttempt.objects.filter(user=request.user).order_by('-date_taken').first()
        context = {
            'retake_locked': True,
            'retake_requested': profile.retake_requested,
            'latest_attempt': latest_attempt,
        }
        return render(request, 'exam.html', context)

    questions = Question.objects.all().order_by('id')
    return render(request, 'exam.html', {'questions': questions, 'is_review': False})

@login_required
def submit_exam_view(request):
    if request.method == "POST":
        questions = Question.objects.all()
        total = questions.count()
        score = 0
        user_answers = {}

        for q in questions:
            selected = request.POST.get(f"question_{q.id}")
            if selected:
                user_answers[str(q.id)] = selected
                if selected == q.correct_option:
                    score += 1

        pct = (score / total * 100) if total > 0 else 0

        attempt = ExamAttempt.objects.create(
            user=request.user,
            score=score,
            total_questions=total,
            percentage=round(pct, 1),
            user_answers=user_answers
        )

        Notification.objects.create(
            message=f"{request.user.username} completed the exam — scored {score}/{total} ({pct:.1f}%).",
            link_name='admin_student_scores',
            link_arg=request.user.id,
        )

        # Lock retakes until the student acknowledges review and an admin approves.
        profile = request.user.profile
        profile.retake_approved = False
        profile.retake_requested = False
        profile.save()

        messages.success(request, f"Exam submitted! You scored {score}/{total} ({pct:.1f}%).")
        return redirect('exam_review', attempt_id=attempt.id)

    return redirect('exam')

@login_required
def exam_review_view(request, attempt_id):
    """Displays the completed exam attempt in review mode."""
    attempt = get_object_or_404(ExamAttempt, id=attempt_id, user=request.user)
    questions = Question.objects.all().order_by('id')

    # Attach user answer directly onto each question instance
    for q in questions:
        q.user_answer = attempt.user_answers.get(str(q.id))

    context = {
        'questions': questions,
        'is_review': True,
        'score': attempt.score,
        'total': attempt.total_questions,
        'percentage': attempt.percentage,
        'attempt': attempt,
    }
    return render(request, 'exam.html', context)

@login_required
def request_retake_view(request):
    """Student confirms they've reviewed their last attempt and asks an admin to unlock a retake."""
    if request.method == "POST":
        profile = request.user.profile
        if not profile.retake_approved and not profile.retake_requested:
            profile.retake_requested = True
            profile.save()

            Notification.objects.create(
                message=f"{request.user.username} reviewed their result and is requesting a retake.",
                link_name='admin_student_scores',
                link_arg=request.user.id,
            )
            messages.info(request, "Retake request sent. An admin will review and unlock it shortly.")
    return redirect('exam')


@user_passes_test(lambda u: u.is_staff, login_url='admin_login')
def admin_panel_view(request):
    pending_payments = Profile.objects.filter(payment_status='PENDING')
    approved_users = Profile.objects.filter(payment_status='APPROVED')

    # Attach the latest score to each approved profile
    for profile in approved_users:
        latest_attempt = ExamAttempt.objects.filter(user=profile.user).order_by('-date_taken').first()
        if latest_attempt:
            profile.latest_score = latest_attempt.percentage
        else:
            profile.latest_score = None

    notifications = Notification.objects.filter(is_read=False)[:10]
    retake_requests = Profile.objects.filter(retake_requested=True)

    context = {
        'total_questions': Question.objects.count(),
        'total_students': User.objects.filter(is_staff=False).count(),
        'pending_payments': pending_payments,
        'approved_users': approved_users,
        'notifications': notifications,
        'unread_notifications_count': Notification.objects.filter(is_read=False).count(),
        'retake_requests': retake_requests,
    }
    return render(request, 'admin-panel.html', context)


@user_passes_test(lambda u: u.is_staff, login_url='admin_login')
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    notification.is_read = True
    notification.save()
    return redirect('admin_panel')


@user_passes_test(lambda u: u.is_staff, login_url='admin_login')
def mark_all_notifications_read(request):
    Notification.objects.filter(is_read=False).update(is_read=True)
    return redirect('admin_panel')

@user_passes_test(lambda u: u.is_staff, login_url='admin_login')
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

@user_passes_test(lambda u: u.is_staff, login_url='admin_login')
def process_retake(request, profile_id, action):
    profile = get_object_or_404(Profile, id=profile_id)
    if action == 'approve':
        profile.retake_approved = True
        profile.retake_requested = False
        messages.success(request, f"Retake unlocked for {profile.user.username}.")
    elif action == 'deny':
        profile.retake_requested = False
        messages.warning(request, f"Retake request denied for {profile.user.username}.")
    profile.save()
    return redirect('admin_panel')


@user_passes_test(lambda u: u.is_staff, login_url='admin_login')
def admin_student_scores_view(request, user_id):
    student = get_object_or_404(User, id=user_id)
    # Fetch all attempts for this specific student, ordered by newest first
    attempts = ExamAttempt.objects.filter(user=student).order_by('-date_taken')
    
    context = {
        'student': student,
        'attempts': attempts,
    }
    return render(request, 'admin_student_scores.html', context)