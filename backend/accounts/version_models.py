from django.db import models
from django.conf import settings
import uuid


class AIConversation(models.Model):
    """
    Stores AI conversation history for refining content
    Each conversation is linked to a specific item (answer, chart, image, table)
    """
    ITEM_TYPE_CHOICES = [
        ('TEXT', 'Text Answer'),
        ('CHART', 'Chart'),
        ('IMAGE', 'Image'),
        ('TABLE', 'Table'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_conversations')
    disclosure = models.ForeignKey('ESRSDisclosure', on_delete=models.CASCADE, null=True, blank=True, 
                                   related_name='conversations')
    item_type = models.CharField(max_length=10, choices=ITEM_TYPE_CHOICES)
    item_id = models.IntegerField(help_text="ID of the item being refined (response_id, chart_id, etc)")
    
    # Conversation messages stored as JSON array
    # Format: [{"role": "user", "content": "make it shorter"}, {"role": "assistant", "content": "..."}]
    messages = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'item_type', 'item_id']),
            models.Index(fields=['disclosure']),
        ]
    
    def __str__(self):
        return f"{self.item_type} conversation for user {self.user.email} ({len(self.messages)} messages)"
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation"""
        self.messages.append({
            'role': role,
            'content': content,
            'timestamp': models.DateTimeField(auto_now_add=True).isoformat()
        })
        self.save()


class ItemVersion(models.Model):
    """
    Stores versions of content items with tree structure
    Each version can have a parent, creating a version tree
    """
    ITEM_TYPE_CHOICES = [
        ('TEXT', 'Text Answer'),
        ('CHART', 'Chart'),
        ('IMAGE', 'Image'),
        ('TABLE', 'Table'),
    ]
    
    CHANGE_TYPE_CHOICES = [
        ('INITIAL', 'Initial Version'),
        ('AI_REFINEMENT', 'AI Refinement'),
        ('MANUAL_EDIT', 'Manual Edit'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='item_versions')
    disclosure = models.ForeignKey('ESRSDisclosure', on_delete=models.CASCADE, related_name='item_versions')
    
    item_type = models.CharField(max_length=10, choices=ITEM_TYPE_CHOICES)
    item_id = models.IntegerField(help_text="ID of the base item (ESRSUserResponse.id for TEXT)")
    version_number = models.IntegerField(default=1)
    
    # Tree structure
    parent_version = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='child_versions')
    
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPE_CHOICES)
    change_description = models.TextField(blank=True, help_text="Summary of what changed")
    
    # Content stored as JSON
    # For TEXT: {"text": "...", "format": "markdown"}
    # For CHART: {"type": "pie", "data": [...], "labels": [...], "colors": [...]}
    # For IMAGE: {"image_base64": "...", "prompt": "...", "url": "..."}
    # For TABLE: {"headers": [...], "rows": [...], "formatting": {...}}
    content = models.JSONField()
    
    conversation = models.ForeignKey(AIConversation, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='versions')
    
    # === USER TRACKING FOR MULTI-USER COLLABORATION ===
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='created_versions', help_text='User who created this version')
    
    is_selected = models.BooleanField(default=False, help_text="Currently active version")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by_user = models.BooleanField(default=False, help_text="True if manually edited, False if AI generated")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'item_type', 'item_id']),
            models.Index(fields=['disclosure']),
            models.Index(fields=['is_selected']),
        ]
        unique_together = [['item_type', 'item_id', 'version_number']]
    
    def __str__(self):
        return f"{self.item_type} v{self.version_number} for disclosure {self.disclosure.code}"
    
    def get_version_tree(self):
        """Get all versions in the tree starting from root"""
        if self.parent_version:
            return self.parent_version.get_version_tree()
        
        # This is the root, build tree
        return self._build_tree()
    
    def _build_tree(self):
        """Recursively build version tree"""
        children = list(self.child_versions.all())
        return {
            'version': self,
            'children': [child._build_tree() for child in children]
        }
    
    def select_as_active(self):
        """Mark this version as the selected one, deselect others"""
        # Deselect all other versions of same item
        ItemVersion.objects.filter(
            item_type=self.item_type,
            item_id=self.item_id,
            user=self.user
        ).update(is_selected=False)
        
        # Select this version
        self.is_selected = True
        self.save()
    
    @classmethod
    def create_initial_version(cls, user, disclosure, item_type, item_id, content):
        """Create the first version of an item"""
        return cls.objects.create(
            user=user,
            disclosure=disclosure,
            item_type=item_type,
            item_id=item_id,
            version_number=1,
            change_type='INITIAL',
            change_description='Initial version',
            content=content,
            is_selected=True,
            created_by_user=False
        )
    
    @classmethod
    def create_refinement_version(cls, parent_version, content, conversation, change_description):
        """Create a new version from AI refinement"""
        # Get next version number
        max_version = ItemVersion.objects.filter(
            item_type=parent_version.item_type,
            item_id=parent_version.item_id,
            user=parent_version.user
        ).aggregate(models.Max('version_number'))['version_number__max'] or 0
        
        new_version = cls.objects.create(
            user=parent_version.user,
            disclosure=parent_version.disclosure,
            item_type=parent_version.item_type,
            item_id=parent_version.item_id,
            version_number=max_version + 1,
            parent_version=parent_version,
            change_type='AI_REFINEMENT',
            change_description=change_description,
            content=content,
            conversation=conversation,
            is_selected=False,
            created_by_user=False
        )
        
        return new_version
    
    @classmethod
    def create_manual_version(cls, parent_version, content, change_description):
        """Create a new version from manual editing"""
        max_version = ItemVersion.objects.filter(
            item_type=parent_version.item_type,
            item_id=parent_version.item_id,
            user=parent_version.user
        ).aggregate(models.Max('version_number'))['version_number__max'] or 0
        
        new_version = cls.objects.create(
            user=parent_version.user,
            disclosure=parent_version.disclosure,
            item_type=parent_version.item_type,
            item_id=parent_version.item_id,
            version_number=max_version + 1,
            parent_version=parent_version,
            change_type='MANUAL_EDIT',
            change_description=change_description,
            content=content,
            is_selected=False,
            created_by_user=True
        )
        
        return new_version
