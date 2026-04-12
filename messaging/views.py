from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone
from .models import Conversation, Message, MessageBlock, MessageNotification
from .forms import MessageForm, MessageReportForm


class ConversationListView(LoginRequiredMixin, ListView):
    model = Conversation
    template_name = 'messages/conversation_list.html'
    context_object_name = 'conversations'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        conversations = Conversation.objects.filter(participants=user).annotate(
            unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=user))
        ).prefetch_related('participants', 'messages')
        
        # Get filter parameters
        search_query = self.request.GET.get('search', '').strip()
        status_filter = self.request.GET.get('status', '')
        sort_by = self.request.GET.get('sort', 'updated_desc')
        
        # Apply search filter
        if search_query:
            conversations = conversations.filter(
                Q(participants__first_name__icontains=search_query) |
                Q(participants__last_name__icontains=search_query) |
                Q(participants__email__icontains=search_query) |
                Q(messages__content__icontains=search_query)
            ).distinct()
        
        # Apply status filter
        if status_filter:
            if status_filter == 'unread':
                conversations = conversations.filter(
                    Q(messages__is_read=False) & ~Q(messages__sender=user)
                ).distinct()
            elif status_filter == 'read':
                conversations = conversations.exclude(
                    Q(messages__is_read=False) & ~Q(messages__sender=user)
                ).distinct()
        
        # Apply sorting
        if sort_by == 'updated_asc':
            conversations = conversations.order_by('updated_at')
        elif sort_by == 'created_desc':
            conversations = conversations.order_by('-created_at')
        elif sort_by == 'created_asc':
            conversations = conversations.order_by('created_at')
        elif sort_by == 'name_asc':
            # Sort by other participant's name
            conversations = list(conversations)
            conversations.sort(key=lambda x: x.get_other_participant(user).get_full_name() if x.get_other_participant(user) else '')
        elif sort_by == 'name_desc':
            conversations = list(conversations)
            conversations.sort(key=lambda x: x.get_other_participant(user).get_full_name() if x.get_other_participant(user) else '', reverse=True)
        else:  # updated_desc (default)
            conversations = conversations.order_by('-updated_at')
        
        # Filter out blocked users
        blocked_users = MessageBlock.objects.filter(
            blocker=user
        ).values_list('blocked', flat=True)
        
        filtered_conversations = []
        for conv in conversations:
            other_participant = conv.get_other_participant(user)
            if other_participant and other_participant.pk not in blocked_users:
                filtered_conversations.append(conv)
        
        return filtered_conversations
    
    def get_context_data(self, **kwargs):
        # Get conversations first
        conversations = self.get_queryset()
        
        # Add unread counts to each conversation
        conversations_with_data = []
        for conv in conversations:
            conv.unread_count = conv.get_unread_count(self.request.user)
            conv.last_message = conv.get_last_message()
            conversations_with_data.append(conv)
        
        # Get filter parameters
        search_query = self.request.GET.get('search', '').strip()
        status_filter = self.request.GET.get('status', '')
        sort_by = self.request.GET.get('sort', 'updated_desc')
        
        # Calculate statistics
        total_conversations = len(conversations_with_data)
        unread_conversations = len([c for c in conversations_with_data if c.unread_count > 0])
        
        # Create base context
        context = {
            'conversations': conversations_with_data,
            'unread_count': Message.objects.filter(
                conversation__in=conversations,
                is_read=False
            ).exclude(sender=self.request.user).count(),
            'total_conversations': total_conversations,
            'unread_conversations': unread_conversations,
            'search_query': search_query,
            'status_filter': status_filter,
            'sort_by': sort_by,
        }
        
        return context


class ConversationDetailView(LoginRequiredMixin, DetailView):
    model = Conversation
    template_name = 'messaging/conversation_detail.html'
    context_object_name = 'conversation'
    
    def get_queryset(self):
        user = self.request.user
        return Conversation.objects.filter(participants=user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conversation = self.get_object()
        
        # Mark messages as read
        unread_messages = conversation.messages.filter(
            is_read=False
        ).exclude(
            sender=self.request.user
        )
        
        for message in unread_messages:
            message.mark_as_read()
        
        # Mark notifications as read
        MessageNotification.objects.filter(
            user=self.request.user,
            message__conversation=conversation,
            is_read=False
        ).update(is_read=True)
        
        context['messages'] = conversation.messages.all()
        context['message_form'] = MessageForm()
        context['other_participant'] = conversation.get_other_participant(self.request.user)
        
        return context


class ConversationCreateView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = 'messages/conversation_create.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recipient_id = self.kwargs.get('user_id')
        if recipient_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            context['recipient'] = get_object_or_404(User, pk=recipient_id)
        return context
    
    def form_valid(self, form):
        recipient_id = self.kwargs.get('user_id')
        if not recipient_id:
            messages.error(self.request, 'Recipient not specified.')
            return self.form_invalid(form)
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        recipient = get_object_or_404(User, pk=recipient_id)
        
        # Check if user is blocked
        if MessageBlock.objects.filter(blocker=recipient, blocked=self.request.user).exists():
            messages.error(self.request, 'You cannot send messages to this user.')
            return self.form_invalid(form)
        
        # Get or create conversation
        conversation = Conversation.objects.filter(
            participants__in=[self.request.user, recipient]
        ).annotate(
            participant_count=Count('participants')
        ).filter(participant_count=2).first()
        
        if not conversation:
            conversation = Conversation.objects.create()
            conversation.participants.add(self.request.user, recipient)
        
        # Create message
        message = form.save(commit=False)
        message.conversation = conversation
        message.sender = self.request.user
        message.save()
        
        # Create notification for recipient
        MessageNotification.objects.create(
            user=recipient,
            message=message
        )
        
        messages.success(self.request, 'Message sent successfully!')
        return redirect('messaging:detail', pk=conversation.pk)


@login_required
def send_message(request, conversation_pk):
    conversation = get_object_or_404(Conversation, pk=conversation_pk, participants=request.user)
    
    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()
            
            # Update conversation timestamp
            conversation.save()
            
            # Create notification for other participant
            other_participant = conversation.get_other_participant(request.user)
            if other_participant:
                MessageNotification.objects.create(
                    user=other_participant,
                    message=message
                )
            
            # Add success message if middleware is available
            try:
                messages.success(request, 'Message sent successfully!')
            except:
                pass  # Messages middleware not available
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message_id': message.pk,
                    'content': message.content,
                    'created_at': message.created_at.strftime('%I:%M %p'),
                    'sender': request.user.email,
                })
            else:
                return redirect('messaging:detail', pk=conversation.pk)
        else:
            # Form is invalid
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid form data',
                    'form_errors': dict(form.errors)
                })
            else:
                try:
                    messages.error(request, 'Error sending message. Please check your input.')
                except:
                    pass  # Messages middleware not available
                return redirect('messaging:detail', pk=conversation_pk)
    
    return redirect('messaging:detail', pk=conversation_pk)


@login_required
def block_user(request, user_id):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    user_to_block = get_object_or_404(User, pk=user_id)
    
    if user_to_block == request.user:
        messages.error(request, 'You cannot block yourself.')
        return redirect('messaging:list')
    
    # Create or update block
    block, created = MessageBlock.objects.get_or_create(
        blocker=request.user,
        blocked=user_to_block
    )
    
    if created:
        messages.success(request, f'You have blocked {user_to_block.email}.')
    else:
        messages.info(request, f'You have already blocked {user_to_block.email}.')
    
    return redirect('messaging:list')


@login_required
def unblock_user(request, user_id):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    user_to_unblock = get_object_or_404(User, pk=user_id)
    
    try:
        block = MessageBlock.objects.get(blocker=request.user, blocked=user_to_unblock)
        block.delete()
        messages.success(request, f'You have unblocked {user_to_unblock.email}.')
    except MessageBlock.DoesNotExist:
        messages.info(request, f'{user_to_unblock.email} is not blocked.')
    
    return redirect('messaging:list')


@login_required
def report_message(request, message_pk):
    message = get_object_or_404(Message, pk=message_pk)
    
    if request.method == 'POST':
        form = MessageReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.message = message
            report.save()
            
            messages.success(request, 'Message reported successfully. Our team will review it.')
            return redirect('messaging:detail', pk=message.conversation.pk)
    else:
        form = MessageReportForm()
    
    return render(request, 'messages/report_form.html', {
        'form': form,
        'message': message
    })


@login_required
def search_users(request):
    query = request.GET.get('q', '')
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    users = User.objects.filter(
        Q(email__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query)
    ).exclude(pk=request.user.pk)[:10]
    
    # Filter out blocked users
    blocked_users = MessageBlock.objects.filter(
        blocker=request.user
    ).values_list('blocked', flat=True)
    
    users = users.exclude(pk__in=blocked_users)
    
    user_list = []
    for user in users:
        user_data = {
            'id': user.pk,
            'email': user.email,
            'name': f"{user.first_name} {user.last_name}".strip() or user.email,
            'user_type': user.user_type,
        }
        user_list.append(user_data)
    
    return JsonResponse({'users': user_list})
