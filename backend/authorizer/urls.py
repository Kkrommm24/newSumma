from django.urls import path
from authorizer.views.auth import MyTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView

app_name = 'news_auth'

urlpatterns = [
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
