from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
import cloudinary
import cloudinary.uploader
import cloudinary.api

User = get_user_model()


def get_user_profile(user_id):
    try:
        user = User.objects.get(pk=user_id)
        avatar_url = user.avatar if user.avatar else settings.DEFAULT_AVATAR_URL
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'avatar': avatar_url,
            'created_at': user.created_at,
        }
    except ObjectDoesNotExist:
        return None


def update_user_profile(user_id, data, avatar_file=None):
    """
    Cập nhật thông tin hồ sơ người dùng.
    Nếu có avatar_file, tải lên Cloudinary và cập nhật URL.
    """
    try:
        user = User.objects.get(pk=user_id)

        for key, value in data.items():
            if key != 'avatar':
                setattr(user, key, value)

        if avatar_file:
            try:
                upload_result = cloudinary.uploader.upload(
                    avatar_file,
                    folder=settings.CLOUDINARY_FOLDER,
                    public_id=f"avatar_{user_id}",
                    overwrite=True,
                    resource_type="image"
                )
                user.avatar = upload_result.get('secure_url')
            except Exception as e:
                print(f"Cloudinary upload failed: {e}")
                raise ValueError("Lỗi tải lên ảnh đại diện.")

        user.save()
        return get_user_profile(user_id)

    except ObjectDoesNotExist:
        return None


def delete_user_profile(user_id):
    try:
        user = User.objects.get(pk=user_id)
        user.is_active = False
        user.save()
        return True
    except ObjectDoesNotExist:
        return False
