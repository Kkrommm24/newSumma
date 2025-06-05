from django.contrib.auth import get_user_model
from ..tasks import send_welcome_email_task
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

def register_user(validated_data):
    try:
        validated_data.pop('password2', None) 
        username = validated_data.pop('username')
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            **validated_data
        )
        
        # Gửi email chào mừng
        # Đảm bảo task được gọi sau khi user đã được tạo và lưu thành công
        send_welcome_email_task.apply_async(
            args=[str(user.id)], 
            queue='high_priority'
        )
        logger.info(f"RegistrationService: User {user.username} (ID: {user.id}) registered successfully. Welcome email task queued.")
        return user
    except Exception as e:
        logger.error(f"RegistrationService: Error during user registration for email {validated_data.get('email')}: {e}", exc_info=True)
        raise
