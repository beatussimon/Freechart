from django.contrib import admin
from .models import UserProfile, Chat, Message, ReadReceipt, Reaction

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'avatar']
    list_filter = ['user']
    search_fields = ['user__username']

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'is_group', 'created_at']
    filter_horizontal = ['participants', 'admins']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'sender', 'chat', 'content', 'timestamp', 'is_read', 'is_deleted']

@admin.register(ReadReceipt)
class ReadReceiptAdmin(admin.ModelAdmin):
    list_display = ['message', 'user', 'read_at']

@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ['message', 'user', 'emoji', 'created_at']