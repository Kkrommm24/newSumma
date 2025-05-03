from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth import get_user_model
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_welcome_email_task(self, user_id):
    try:
        user = User.objects.get(id=user_id)
        subject = 'Chào mừng bạn đến với NewSumma!'
        
        html_message = render_to_string('user/welcome_email.html', {'username': user.username})
        plain_message = strip_tags(html_message)
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user.email]

        try:
            send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)
            return f"Successfully sent welcome email to {user.email}"
        except Exception as exc:
            print(f"[Celery Task] Error sending email to {user.email}: {exc}. Retrying...")
            raise self.retry(exc=exc)

    except User.DoesNotExist:
        print(f"[Celery Task] User with id {user_id} does not exist. Cannot send email.")
        return f"User {user_id} not found."
    except Exception as e:
        print(f"[Celery Task] Unexpected error for user {user_id}: {e}")
        return f"Unexpected error for user {user_id}."

@shared_task
def send_password_reset_email(recipient_email, reset_link):
    subject = 'Đặt lại mật khẩu cho tài khoản News Summarizer của bạn'
    message = (
        f'Xin chào,\n\n'
        f'Bạn (hoặc ai đó) đã yêu cầu đặt lại mật khẩu cho tài khoản của bạn.\n'
        f'Vui lòng nhấp vào liên kết dưới đây để đặt mật khẩu mới:\n\n'
        f'{reset_link}\n\n'
        f'Liên kết này sẽ hết hạn sau 5 phút.\n\n'
        f'Nếu bạn không yêu cầu điều này, vui lòng bỏ qua email này.\n\n'
        f'Trân trọng,\n'
        f'Đội ngũ News Summarizer'
    )
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient_email],
            fail_silently=False,
        )
        return "Password reset email sent successfully!"
    except Exception as e:
        logger.error(f"Error sending password reset email to {recipient_email}: {e}")
        raise 