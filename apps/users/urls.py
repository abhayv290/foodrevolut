from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomerAddressDetailView,CustomerAddressView,
    CustomerProfileView,CustomerRegisterView,CustomerSetDefaultAddressView,
    ChangePasswordView,RestaurantOwnerProfileView,ResendVerificationEmailView,
    AgentAvailabilityView,DeliveryAgentRegisterView,DeliveryAgentProfileView,
    RestaurantOwnerRegisterView,LoginView,LogoutView,MeView,
    VerifyEmailView ,DeliveryAgentProfileLocation
)

app_name = "users"

urlpatterns = [
    #  Registration -------------------------------------------------------------------
    path("auth/register/customer/",CustomerRegisterView.as_view(),name="register-customer"),
    path("auth/register/restaurant-owner/",RestaurantOwnerRegisterView.as_view(), name="register-owner"),
    path("auth/register/delivery-agent/",DeliveryAgentRegisterView.as_view(),   name="register-agent"),

    # ─ Auth -----------------------------------------------------------------------
    path("auth/login/", LoginView.as_view(),    name="login"),
    path("auth/logout/",LogoutView.as_view(),   name="logout"),
    path("auth/token/refresh/", TokenRefreshView.as_view(),   name="token-refresh"),
    path("auth/me/",MeView.as_view(),        name="me"),

    #  Password ---------------------------------------------------------------------
    path("auth/password/change/", ChangePasswordView.as_view(), name="password-change"),

    #  Email verification ------------------------------------------------------
    # GET  ?token=<uuid>  — user clicks link from email
    path("auth/email/verify/",VerifyEmailView.as_view(),name="email-verify"),
    # POST { email }      — resend if token expired or email not received
    path("auth/email/resend-verification/",ResendVerificationEmailView.as_view(), name="email-resend"),

    # Customer ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    path("customer/profile/",CustomerProfileView.as_view(),name="customer-profile"),
    path("customer/addresses/",CustomerAddressView.as_view(), name="customer-addresses"),
    path("customer/addresses/<uuid:pk>/",CustomerAddressDetailView.as_view(),     name="customer-address-detail"),
    path("customer/addresses/<uuid:pk>/set-default/",CustomerSetDefaultAddressView.as_view(),         name="address-set-default"),

    #  Restaurant owner ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    path("restaurant-owner/profile/", RestaurantOwnerProfileView.as_view(), name="owner-profile"),

    #  Delivery agent ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    path("delivery-agent/profile/",  DeliveryAgentProfileView.as_view(),  name="agent-profile"),
    path("delivery-agent/location/",DeliveryAgentProfileLocation.as_view(),   name="agent-location"),
    path("delivery-agent/availability/",AgentAvailabilityView.as_view(),     name="agent-availability"),
]