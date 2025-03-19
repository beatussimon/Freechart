from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.utils import timezone
from .models import Chat, Message, ReadReceipt, Reaction

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.group_name = f'chat_{self.chat_id}'
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        chat = Chat.objects.get(id=self.chat_id)
        
        if action == 'message':
            message = data['message']
            msg = Message.objects.create(chat=chat, sender=self.user, content=message)
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender': self.user.username,
                    'timestamp': msg.timestamp.strftime('%H:%M'),
                    'message_id': msg.id,
                    'file': msg.file.url if msg.file else None,
                }
            )
        elif action == 'typing':
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'typing_indicator',
                    'sender': self.user.username,
                }
            )
        elif action == 'read':
            message_id = data['message_id']
            message = Message.objects.get(id=message_id)
            ReadReceipt.objects.get_or_create(message=message, user=self.user)
            message.is_read = True
            message.save()
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'read_receipt',
                    'message_id': message_id,
                }
            )
        elif action == 'reaction':
            message_id = data['message_id']
            emoji = data['emoji']
            message = Message.objects.get(id=message_id)
            Reaction.objects.get_or_create(message=message, user=self.user, emoji=emoji)
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'reaction_update',
                    'message_id': message_id,
                    'emoji': emoji,
                }
            )
        elif action == 'delete':
            message_id = data['message_id']
            message = Message.objects.get(id=message_id, sender=self.user)
            message.is_deleted = True
            message.save()
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'message_delete',
                    'message_id': message_id,
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'sender': event['sender'],
            'timestamp': event['timestamp'],
            'message_id': event['message_id'],
            'file': event['file'],
        }))

    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'sender': event['sender'],
        }))

    async def read_receipt(self, event):
        await self.send(text_data=json.dumps({
            'type': 'read',
            'message_id': event['message_id'],
        }))

    async def reaction_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'reaction',
            'message_id': event['message_id'],
            'emoji': event['emoji'],
        }))

    async def message_delete(self, event):
        await self.send(text_data=json.dumps({
            'type': 'delete',
            'message_id': event['message_id'],
        }))