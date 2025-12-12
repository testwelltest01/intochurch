from django.apps import AppConfig

class MinistryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ministry'
    verbose_name = '교회 데이터 관리'  # <--- 이 줄 추가!