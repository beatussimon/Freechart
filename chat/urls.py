from django.urls import path
from django.contrib.auth import logout
from django.shortcuts import redirect
from . import views

def logout_view(request):
    print(f"Logout called: User authenticated before = {request.user.is_authenticated}")
    logout(request)
    print(f"Logout called: User authenticated after = {request.user.is_authenticated}")
    return redirect('landing_page')

urlpatterns = [
    path('', views.ChatListView.as_view(), name='chat_list'),
    path('chat/<int:pk>/', views.ChatDetailView.as_view(), name='chat_detail'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('start_chat/<int:user_id>/', views.StartChatView.as_view(), name='start_chat'),
    path('group/create/', views.GroupCreateView.as_view(), name='group_create'),
    path('group/invite/<int:pk>/', views.GroupInviteView.as_view(), name='group_invite'),
    path('logout/', logout_view, name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.EditProfileView.as_view(), name='edit_profile'),
]