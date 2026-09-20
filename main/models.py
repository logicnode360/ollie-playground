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

class ExamAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attempts')
    score = models.IntegerField()
    total_questions = models.IntegerField()
    percentage = models.FloatField()
    user_answers = models.JSONField(default=dict, blank=True)  # Stores {"question_id": "selected_option"}
    date_taken = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.score}/{self.total_questions} ({self.date_taken.strftime('%Y-%m-%d')})"