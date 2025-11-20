from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import AccessibleLoginView, DashboardRedirectView

urlpatterns = [
    path("login/", AccessibleLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("dashboard/", DashboardRedirectView.as_view(), name="account-dashboard"),
]

