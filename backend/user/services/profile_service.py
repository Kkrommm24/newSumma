from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
import cloudinary
import cloudinary.uploader
import cloudinary.api
from typing import Dict, Optional, Any

User = get_user_model()


class ProfileService:
    @staticmethod
    def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
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

    @staticmethod
    def update_user_profile(user_id: str,
                            data: Dict[str,
                                       Any],
                            avatar_file: Optional[Any] = None) -> Optional[Dict[str,
                                                                                Any]]:
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
            return ProfileService.get_user_profile(user_id)

        except ObjectDoesNotExist:
            return None

    @staticmethod
    def delete_user_profile(user_id: str) -> bool:
        try:
            user = User.objects.get(pk=user_id)
            user.is_active = False
            user.save()
            return True
        except ObjectDoesNotExist:
            return False
