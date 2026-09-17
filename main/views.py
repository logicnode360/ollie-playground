from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Question, ExamAttempt, Profile

# --- ADMIN LOGIN VIEW ---
def admin_login_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_panel')

    if request.method == "POST":
        u_name = request.POST.get('username')
        p_word = request.POST.get('password')

        # Check for fixed admin password
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
    if request.user.profile.payment_status != 'APPROVED':
        messages.error(request, "Your payment must be approved before you can start the exam.")
        return redirect('dashboard')

    questions = Question.objects.all().order_by('id')
    return render(request, 'exam.html', {'questions': questions})

@login_required
def submit_exam_view(request):
    if request.method == "POST":
        questions = Question.objects.all()
        total = questions.count()
        score = sum(1 for q in questions if request.POST.get(f"question_{q.id}") == q.correct_option)
        pct = (score / total * 100) if total > 0 else 0

        ExamAttempt.objects.create(
            user=request.user,
            score=score,
            total_questions=total,
            percentage=round(pct, 1)
        )
        messages.success(request, f"Exam submitted! You scored {score}/{total} ({pct:.1f}%).")
        return redirect('dashboard')
    return redirect('exam')

@user_passes_test(lambda u: u.is_staff, login_url='admin_login')
def admin_panel_view(request):
    pending_payments = Profile.objects.filter(payment_status='PENDING')
    approved_users = Profile.objects.filter(payment_status='APPROVED')

    context = {
        'total_questions': Question.objects.count(),
        'total_students': User.objects.filter(is_staff=False).count(),
        'pending_payments': pending_payments,
        'approved_users': approved_users,
    }
    return render(request, 'admin-panel.html', context)

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