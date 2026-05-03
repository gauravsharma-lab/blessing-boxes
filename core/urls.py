from django.urls import path
from . import views
from django.contrib.auth import views as auth_views




urlpatterns = [
    path('', views.homepage, name='homepage'),

    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('signup/', views.signup, name='signup'),

    path('select-role/<str:role>/', views.select_role, name='select_role'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('donate/', views.donate_food, name='donate_food'),
    path('accept/<int:donation_id>/', views.accept_delivery, name='accept_delivery'),
    path('contact/', views.contact, name='contact'),
    path('privacy/', views.privacy, name='privacy'),
    path('edit-donation/<int:id>/', views.edit_donation, name='edit_donation'),
    path('delete-donation/<int:id>/', views.delete_donation, name='delete_donation'),
    path('my-donations/', views.my_donations, name='my_donations'),
    path('update-ngo/', views.update_ngo_profile, name='update_ngo_profile'),
    
    # Volunteer URLs
    path('volunteer/accept/<int:donation_id>/', views.volunteer_accept_task, name='volunteer_accept_task'),
    path('volunteer/complete/<int:donation_id>/', views.volunteer_complete_delivery, name='volunteer_complete_delivery'),
]