"""
Team collaboration models for multi-user ESRS documentation
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
import secrets


class UserRole(models.Model):
    """
    Defines user roles within an organization/account
    Admin: Can invite users, assign disclosures, manage all
    Member: Can edit only assigned disclosures
    """
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('member', 'Team Member'),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='team_role'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    organization = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='team_members',
        help_text='The admin user who owns this account'
    )
    show_all_disclosures = models.BooleanField(
        default=False,
        help_text='If True, user sees all disclosures. If False, user sees only assigned disclosures.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'organization')
    
    def __str__(self):
        return f"{self.user.email} - {self.role} in {self.organization.email}'s team"


class UserInvitation(models.Model):
    """
    Tracks invitations sent to new team members
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    email = models.EmailField()
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_invitations'
    )
    role = models.CharField(max_length=20, choices=UserRole.ROLE_CHOICES, default='member')
    token = models.CharField(max_length=64, unique=True, default=secrets.token_urlsafe)
    temporary_password = models.CharField(max_length=128, help_text='Temporary password sent in email')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Default: 7 days expiration
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        return timezone.now() > self.expires_at and self.status == 'pending'
    
    def __str__(self):
        return f"Invitation to {self.email} by {self.invited_by.email}"


class DisclosureAssignment(models.Model):
    """
    Assigns specific ESRS disclosures to team members
    """
    disclosure = models.ForeignKey(
        'ESRSDisclosure',
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assigned_disclosures'
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assignments_made'
    )
    organization = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='disclosure_assignments',
        help_text='The admin user who owns this account'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, help_text='Assignment notes or instructions')
    
    class Meta:
        unique_together = ('disclosure', 'organization')  # One assignment per disclosure per org
    
    def __str__(self):
        return f"{self.disclosure.code} assigned to {self.assigned_to.email}"


class ActivityLog(models.Model):
    """
    Comprehensive activity tracking for all user actions
    """
    ACTION_CHOICES = [
        ('ai_answer', 'Generated AI Answer'),
        ('manual_answer', 'Edited Manual Answer'),
        ('notes_update', 'Updated Notes'),
        ('document_upload', 'Uploaded Document'),
        ('document_link', 'Linked Document'),
        ('document_unlink', 'Unlinked Document'),
        ('completion_toggle', 'Toggled Completion'),
        ('chart_extract', 'Extracted Charts'),
        ('image_generate', 'Generated Image'),
        ('assignment_change', 'Changed Assignment'),
        ('user_invite', 'Invited User'),
        ('version_create', 'Created Version'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='activities'
    )
    organization = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='team_activities',
        help_text='The admin user who owns this account'
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    disclosure = models.ForeignKey(
        'ESRSDisclosure',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs'
    )
    details = models.JSONField(default=dict, blank=True, help_text='Additional action details')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['organization', '-timestamp']),
            models.Index(fields=['disclosure', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
        ]
    
    def __str__(self):
        disclosure_info = f" on {self.disclosure.code}" if self.disclosure else ""
        return f"{self.user.email}: {self.action}{disclosure_info} at {self.timestamp}"
