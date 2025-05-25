from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

User = get_user_model()


def change_user_password(user_id, old_password, new_password):
    try:
        user = User.objects.get(pk=user_id)
        if not user.check_password(old_password):
            raise ValueError("Mật khẩu hiện tại không đúng.")

        user.set_password(new_password)
        user.save()
        return True
    except ObjectDoesNotExist:
        raise ObjectDoesNotExist("Không tìm thấy người dùng.")


def delete_account_with_password(user_id, password):
    try:
        user = User.objects.get(pk=user_id)
        if not user.check_password(password):
            raise ValueError("Mật khẩu không đúng.")

        if not user.is_active:
            return True

        user.is_active = False
        user.save(update_fields=['is_active'])
        return True
    except ObjectDoesNotExist:
        raise ObjectDoesNotExist("Không tìm thấy người dùng.")
