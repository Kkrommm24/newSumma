from rest_framework import serializers
from news.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from django.utils.translation import gettext_lazy as _


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        try:
            data = super().validate(attrs)
        except AuthenticationFailed:
            raise AuthenticationFailed(
                _('Tên đăng nhập hoặc mật khẩu không đúng.'),
                'no_active_account'
            )
        except Exception as e:
            raise e

        user_serializer = UserSerializer(self.user)
        data['user'] = user_serializer.data

        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'avatar',
            'is_staff',
            'is_superuser')
