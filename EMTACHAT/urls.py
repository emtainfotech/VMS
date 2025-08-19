# chat/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Main chat page
    path('', views.chat_view, name='chat_view'),

    # API to get details (messages, members) for a chat
    path('details/<int:group_id>/', views.get_chat_details, name='get_chat_details'),

    # API to create a new group
    path('create_group/', views.create_group_chat, name='create_group_chat'),

    # API to handle file uploads
    path('upload_attachment/<int:group_id>/', views.upload_attachment, name='upload_attachment'),

    # URL to download an attachment
    path('download_attachment/<int:attachment_id>/', views.download_attachment, name='download_attachment'),
]