from django.db import models
from accounts.models import Account as User

class ChatHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_history')
    question = models.TextField()
    answer = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    def get_question_preview(self, length=50):
        if len(self.question) > length:
            return self.question[:length] + '...'
        return self.question
    
    def get_answer_preview(self, length=50):
        if len(self.answer) > length:
            return self.answer[:length] + '...'
        return self.answer