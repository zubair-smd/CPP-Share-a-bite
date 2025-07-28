
from django.contrib import admin
from django.urls import include,path
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [

    path("",views.index.as_view(), name="index"),
    path("about",views.about.as_view(), name="about"),
    path("dashboard",views.admin_dashboard.as_view(), name="admin_dashboard"),
    path("ngos",views.admin_ngo_list.as_view(), name="admin_ngo_list"),
    path("donations",views.admin_donations.as_view(), name="admin_donations"),
    path("households",views.admin_households.as_view(), name="admin_households"),
    path("admin_add_ngo",views.admin_add_ngo.as_view(), name="admin_add_ngo"),
    path("login",views.login.as_view(), name="login"),
    path("logout",views.logout.as_view(), name="logout"),
    path("signup",views.signup.as_view(), name="signup"),
    
    path("admin_assign_ngo/<int:donation_id>/",views.admin_assign_ngo.as_view(), name="admin_assign_ngo"),
    path("admin_assign_ngo",views.admin_assign_ngo.as_view(), name="admin_assign_ngo"),
    
    path("ngo_donations",views.ngo_donations.as_view(), name="ngo_donations"),
    path("ngo_requests",views.ngo_requests.as_view(), name="ngo_requests"),
    
    path("household_donations",views.household_donations.as_view(), name="household_donations"),
    path("add_donation",views.household_add_donation.as_view(), name="household_add_donation"),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
