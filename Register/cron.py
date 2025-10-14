# from django.utils import timezone
# from datetime import timedelta
# from Register.models import User
#
# def clean_inactive_users():
#     cutoff = timezone.now() - timedelta(hours=1)
#     # updated_at < cutoff 的用户强制登出
#     User.objects.filter(updated_at=cutoff, activated=True).update(activated=False)
#     print("Inactive users cleaned up.")
