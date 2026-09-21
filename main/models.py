from django.db import models
from django.contrib.auth.models import User

class Question(models.Model):
    question = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_option = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])
    explanation = models.TextField(blank=True, help_text="Key note explanation shown during review.")

    def __str__(self):
        return f"Q{self.id}: {self.question[:50]}"

class Profile(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('UNPAID', 'Unpaid'),
        ('PENDING', 'Pending Verification'),
        ('APPROVED', 'Approved'),
        ('DENIED', 'Denied'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='UNPAID')

    def __str__(self):
        return f"{self.user.username} - {self.payment_status}"

class Notification(models.Model):
    """
    Simple admin-facing notification feed. Not tied to a specific staff user,
    since any staff member should be able to see/dismiss it — mirrors how
    the pending_payments queue works (shared, not per-admin).
    """
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

    def __str__(self):
        return f"{self.user.username} - {self.score}/{self.total_questions} ({self.date_taken.strftime('%Y-%m-%d')})"