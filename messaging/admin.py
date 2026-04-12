from django.contrib import admin
from .models import Conversation, Message, MessageAttachment, MessageReport, MessageBlock, MessageNotification


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('created_at',)


class MessageAttachmentInline(admin.TabularInline):
    model = MessageAttachment
    extra = 0
    readonly_fields = ('file_size', 'content_type')


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'participant_list', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('participants__email',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [MessageInline]
    
    def participant_list(self, obj):
        return ', '.join([user.email for user in obj.participants.all()])
    participant_list.short_description = 'Participants'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'sender', 'content_preview', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('sender__email', 'content')
    readonly_fields = ('created_at',)
    inlines = [MessageAttachmentInline]
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'
    
    fieldsets = (
        ('Message Information', {
            'fields': ('conversation', 'sender', 'content', 'file_attachment')
        }),
        ('Status', {
            'fields': ('is_read', 'read_at')
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ('message', 'filename', 'file_size_display', 'content_type')
    # list_filter = ('content_type', 'created_at')  # Removed created_at since field doesn't exist
    list_filter = ('content_type',)
    search_fields = ('filename', 'message__content')
    # readonly_fields = ('file_size', 'created_at')  # Removed created_at since field doesn't exist
    readonly_fields = ('file_size',)
    
    def file_size_display(self, obj):
        return obj.get_file_size_display()
    file_size_display.short_description = 'File Size'


@admin.register(MessageReport)
class MessageReportAdmin(admin.ModelAdmin):
    list_display = ('reporter', 'message', 'reason', 'is_resolved', 'created_at')
    list_filter = ('reason', 'is_resolved', 'created_at')
    search_fields = ('reporter__email', 'message__content', 'description')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Report Information', {
            'fields': ('reporter', 'message', 'reason', 'description')
        }),
        ('Status', {
            'fields': ('is_resolved',)
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(MessageBlock)
class MessageBlockAdmin(admin.ModelAdmin):
    list_display = ('blocker', 'blocked', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('blocker__email', 'blocked__email')
    readonly_fields = ('created_at',)


@admin.register(MessageNotification)
class MessageNotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__email', 'message__content')
    readonly_fields = ('created_at',)
