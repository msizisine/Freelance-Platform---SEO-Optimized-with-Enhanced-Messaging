from django.urls import path
from .views import (
    ConversationListView, ConversationDetailView, ConversationCreateView,
    send_message, block_user, unblock_user, report_message, search_users
)

app_name = 'messaging'

urlpatterns = [
    path('', ConversationListView.as_view(), name='list'),
    path('create/<int:user_id>/', ConversationCreateView.as_view(), name='create'),
    path('<int:pk>/', ConversationDetailView.as_view(), name='detail'),
    path('<int:pk>/send/', send_message, name='send'),
    path('block/<int:user_id>/', block_user, name='block_user'),
    path('unblock/<int:user_id>/', unblock_user, name='unblock_user'),
    path('report/<int:message_pk>/', report_message, name='report'),
    path('search/', search_users, name='search_users'),
]
