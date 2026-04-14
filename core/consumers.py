import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models_notifications import Notification, NotificationChannel

User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time notifications"""
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Create unique channel name for this connection
        self.channel_name = f"user_{self.user.id}_{self.channel_layer.name}"
        
        # Join user's personal notification group
        await self.channel_layer.group_add(
            f"user_{self.user.id}_notifications",
            self.channel_name
        )
        
        # Create notification channel record
        await self.create_notification_channel()
        
        # Accept the connection
        await self.accept()
        
        # Send unread notifications count
        await self.send_unread_count()
        
        # Send recent notifications
        await self.send_recent_notifications()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'user') and self.user.is_authenticated:
            # Leave the notification group
            await self.channel_layer.group_discard(
                f"user_{self.user.id}_notifications",
                self.channel_name
            )
            
            # Update notification channel
            await self.update_notification_channel(active=False)
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'mark_read':
                # Mark notification as read
                notification_id = data.get('notification_id')
                await self.mark_notification_read(notification_id)
                
            elif message_type == 'mark_all_read':
                # Mark all notifications as read
                await self.mark_all_notifications_read()
                
            elif message_type == 'ping':
                # Keep-alive ping
                await self.send_json({'type': 'pong'})
                
            elif message_type == 'get_unread_count':
                # Send unread count
                await self.send_unread_count()
                
        except json.JSONDecodeError:
            await self.send_error('Invalid message format')
        except Exception as e:
            await self.send_error(str(e))
    
    async def notification_message(self, event):
        """Handle new notification message"""
        notification_data = event['notification']
        
        # Send notification to client
        await self.send_json({
            'type': 'new_notification',
            'notification': notification_data
        })
        
        # Update unread count
        await self.send_unread_count()
    
    async def send_json(self, data):
        """Send JSON message to client"""
        await self.send(text_data=json.dumps(data))
    
    async def send_error(self, error_message):
        """Send error message to client"""
        await self.send_json({
            'type': 'error',
            'message': error_message
        })
    
    @database_sync_to_async
    def create_notification_channel(self):
        """Create notification channel record"""
        # Get client info from scope
        client_info = self.scope.get('client', {})
        headers = self.scope.get('headers', {})
        
        user_agent = ''
        for header, value in headers:
            if header.decode('utf-8').lower() == 'user-agent':
                user_agent = value.decode('utf-8')
                break
        
        NotificationChannel.objects.update_or_create(
            user=self.user,
            channel_name=self.channel_name,
            defaults={
                'ip_address': client_info[0] if client_info else None,
                'user_agent': user_agent,
                'is_active': True,
                'last_seen': timezone.now()
            }
        )
    
    @database_sync_to_async
    def update_notification_channel(self, active=True):
        """Update notification channel status"""
        try:
            channel = NotificationChannel.objects.get(
                user=self.user,
                channel_name=self.channel_name
            )
            channel.is_active = active
            if active:
                channel.last_seen = timezone.now()
            channel.save(update_fields=['is_active', 'last_seen'])
        except NotificationChannel.DoesNotExist:
            pass
    
    @database_sync_to_async
    def get_unread_notifications(self):
        """Get unread notifications for user"""
        return list(
            Notification.objects.filter(
                recipient=self.user,
                is_read=False
            ).order_by('-created_at').values(
                'id', 'notification_type', 'title', 'message',
                'created_at', 'action_url', 'action_text',
                'priority', 'data'
            )[:10]
        )
    
    @database_sync_to_async
    def get_unread_count(self):
        """Get unread notifications count"""
        return Notification.objects.filter(
            recipient=self.user,
            is_read=False
        ).count()
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark specific notification as read"""
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient=self.user
            )
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False
    
    @database_sync_to_async
    def mark_all_notifications_read(self):
        """Mark all notifications as read"""
        count = Notification.objects.filter(
            recipient=self.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        return count
    
    async def send_unread_count(self):
        """Send unread notifications count to client"""
        count = await self.get_unread_count()
        await self.send_json({
            'type': 'unread_count',
            'count': count
        })
    
    async def send_recent_notifications(self):
        """Send recent notifications to client"""
        notifications = await self.get_unread_notifications()
        await self.send_json({
            'type': 'recent_notifications',
            'notifications': notifications
        })


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time chat/messaging"""
    
    async def connect(self):
        """Handle WebSocket connection for chat"""
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Get conversation ID from URL
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f"chat_{self.conversation_id}"
        
        # Join chat room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Accept connection
        await self.accept()
        
        # Mark messages as seen
        await self.mark_messages_seen()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming chat messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'new_message':
                # Handle new message
                message_content = data.get('message', '').strip()
                if message_content:
                    message = await self.save_message(message_content)
                    if message:
                        # Broadcast to room
                        await self.channel_layer.group_send(
                            self.room_group_name,
                            {
                                'type': 'chat_message',
                                'message': message
                            }
                        )
            
            elif message_type == 'typing':
                # Handle typing indicator
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'typing_indicator',
                        'user_id': self.user.id,
                        'user_name': self.user.get_full_name() or self.user.email,
                        'is_typing': data.get('is_typing', False)
                    }
                )
            
            elif message_type == 'mark_read':
                # Mark messages as read
                message_ids = data.get('message_ids', [])
                await self.mark_messages_as_read(message_ids)
                
        except json.JSONDecodeError:
            await self.send_error('Invalid message format')
        except Exception as e:
            await self.send_error(str(e))
    
    async def chat_message(self, event):
        """Handle new chat message"""
        message = event['message']
        
        # Send message to client
        await self.send_json({
            'type': 'new_message',
            'message': message
        })
    
    async def typing_indicator(self, event):
        """Handle typing indicator"""
        # Don't send back to the same user
        if event['user_id'] != self.user.id:
            await self.send_json({
                'type': 'typing_indicator',
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'is_typing': event['is_typing']
            })
    
    @database_sync_to_async
    def save_message(self, content):
        """Save new message to database"""
        from messaging.models import Message, Conversation
        
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            
            # Check if user is part of conversation
            if not conversation.participants.filter(id=self.user.id).exists():
                return None
            
            message = Message.objects.create(
                conversation=conversation,
                sender=self.user,
                content=content
            )
            
            # Update conversation
            conversation.updated_at = timezone.now()
            conversation.save(update_fields=['updated_at'])
            
            # Create notification for other participants
            await self.create_message_notification(conversation, message)
            
            return {
                'id': message.id,
                'content': message.content,
                'sender_id': message.sender.id,
                'sender_name': message.sender.get_full_name() or message.sender.email,
                'created_at': message.created_at.isoformat(),
                'is_read': message.is_read
            }
            
        except Conversation.DoesNotExist:
            return None
    
    @database_sync_to_async
    def create_message_notification(self, conversation, message):
        """Create notification for new message"""
        from .models_notifications import Notification
        
        # Get other participants
        other_participants = conversation.participants.exclude(id=self.user.id)
        
        for participant in other_participants:
            Notification.objects.create(
                recipient=participant,
                sender=self.user,
                notification_type='message',
                title=f'New message from {self.user.get_full_name() or self.user.email}',
                title=message.content[:100] + ('...' if len(message.content) > 100 else ''),
                related_object_id=message.id,
                related_object_type='message',
                action_url=f"/messages/{conversation.id}/",
                action_text='View Message'
            )
    
    @database_sync_to_async
    def mark_messages_seen(self):
        """Mark unread messages in conversation as seen"""
        from messaging.models import Message
        
        Message.objects.filter(
            conversation_id=self.conversation_id,
            is_read=False
        ).exclude(sender=self.user).update(is_read=True)
    
    @database_sync_to_async
    def mark_messages_as_read(self, message_ids):
        """Mark specific messages as read"""
        from messaging.models import Message
        
        Message.objects.filter(
            id__in=message_ids,
            conversation_id=self.conversation_id
        ).exclude(sender=self.user).update(is_read=True)
    
    async def send_json(self, data):
        """Send JSON message to client"""
        await self.send(text_data=json.dumps(data))
    
    async def send_error(self, error_message):
        """Send error message to client"""
        await self.send_json({
            'type': 'error',
            'message': error_message
        })
