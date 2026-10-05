# models.py
from django.db import models
from django.contrib.auth.models import User

class Question(models.Model):
    WEEK_CHOICES = [
        ('week1', 'Week 1'),
        ('week2', 'Week 2'),
    ]
    question = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_option = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])
    explanation = models.TextField(blank=True, help_text="Key note explanation shown during review.")
    week = models.CharField(max_length=20, default='week1')

    def __str__(self):
        return f"[{self.week.upper()}] Q{self.id}: {self.question[:50]}"

class Profile(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('UNPAID', 'Unpaid'),
        ('PENDING', 'Pending Verification'),
        ('APPROVED', 'Approved'),
        ('DENIED', 'Denied'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='UNPAID')
    retake_approved = models.BooleanField(default=True)
    retake_requested = models.BooleanField(default=False)
    retake_denied = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.payment_status}"

class Notification(models.Model):
    message = models.CharField(max_length=255)
    link_name = models.CharField(max_length=100, blank=True, help_text="URL name to reverse for the 'view' link, e.g. 'admin_student_scores'.")
    link_arg = models.PositiveIntegerField(null=True, blank=True, help_text="Single positional arg for link_name, e.g. a user id.")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.message

class ExamAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attempts')
    score = models.IntegerField()
    total_questions = models.IntegerField()
    percentage = models.FloatField()
    user_answers = models.JSONField(default=dict, blank=True)  # Stores {"question_id": "selected_option"}
    date_taken = models.DateTimeField(auto_now_add=True)
    time_taken_seconds = models.PositiveIntegerField(null=True, blank=True, help_text="Wall-clock time from exam start to submission, in seconds.")
    week = models.CharField(max_length=10, default='week1')

    def time_taken_display(self):
        if self.time_taken_seconds is None:
            return None
        minutes, seconds = divmod(self.time_taken_seconds, 60)
        return f"{minutes}m {seconds:02d}s"

    def __str__(self):
        return f"{self.user.username} - [{self.week.upper()}] {self.score}/{self.total_questions} ({self.date_taken.strftime('%Y-%m-%d')})"