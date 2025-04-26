from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth import get_user_model

User = get_user_model()

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