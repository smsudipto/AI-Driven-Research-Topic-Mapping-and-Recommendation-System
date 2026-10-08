from django.db import models
from accounts.models import Accounts

class SystemLog(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Accounts, on_delete=models.SET_NULL, null=True, blank=True, related_name='system_logs')
    action = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        user_str = self.user.username if self.user else "Anonymous/System"
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {user_str} - {self.action}"