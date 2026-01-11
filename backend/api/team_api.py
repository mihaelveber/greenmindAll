"""
Team collaboration API endpoints
Handles user invitations, assignments, activity logs, and team management
"""
from ninja import Router
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from accounts.auth import JWTAuth
from accounts.team_models import UserRole, UserInvitation, DisclosureAssignment, ActivityLog
from accounts.models import ESRSDisclosure
from typing import List, Optional
from pydantic import BaseModel, EmailStr
import secrets
import string

User = get_user_model()
router = Router(tags=["Team Management"])


# ===== SCHEMAS =====

class InviteUserSchema(BaseModel):
    email: EmailStr
    role: str = 'member'  # 'admin' or 'member'


class InvitationSchema(BaseModel):
    id: int
    email: str
    role: str
    status: str
    created_at: str
    expires_at: str
    invited_by_email: str


class TeamMemberSchema(BaseModel):
    id: int
    email: str
    role: str
    joined_at: str
    is_organization_owner: bool
    show_all_disclosures: bool
    # Statistics
    assigned_tasks_count: int
    completed_assigned_tasks: int
    assigned_completion_percentage: float
    organization_completion_percentage: float


class AssignDisclosureSchema(BaseModel):
    disclosure_code: str  # e.g., "E1-1"
    assigned_to_email: str
    notes: Optional[str] = None


class AssignmentSchema(BaseModel):
    id: int
    disclosure_code: str
    disclosure_title: str
    assigned_to_email: str
    assigned_by_email: Optional[str]
    assigned_at: str
    notes: str


class ActivityLogSchema(BaseModel):
    id: int
    user_email: Optional[str]
    action: str
    disclosure_code: Optional[str]
    details: dict
    timestamp: str


class MessageResponseSchema(BaseModel):
    message: str
    success: bool = True


# ===== HELPER FUNCTIONS =====

def generate_temporary_password(length=12):
    """Generate a secure random password"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(characters) for _ in range(length))


def send_invitation_email(invitation: UserInvitation, temp_password: str):
    """
    Trigger async email sending via Celery task
    
    Args:
        invitation: UserInvitation instance
        temp_password: Generated temporary password
    """
    from accounts.tasks import send_invitation_email_task
    
    # Send email asynchronously via Celery
    send_invitation_email_task.delay(
        email=invitation.email,
        invited_by_name=invitation.invited_by.email,
        role=invitation.role,
        temp_password=temp_password,
        token=invitation.token,
        expires_at=invitation.expires_at.strftime('%Y-%m-%d %H:%M')
    )


def log_activity(user, organization, action, disclosure=None, details=None):
    """Helper to log user activities"""
    ActivityLog.objects.create(
        user=user,
        organization=organization,
        action=action,
        disclosure=disclosure,
        details=details or {}
    )


def get_organization_owner(user):
    """Get the organization owner for a user"""
    if user.is_organization_owner:
        return user
    
    # User is a team member, get their organization owner
    try:
        role = UserRole.objects.get(user=user)
        return role.organization
    except UserRole.DoesNotExist:
        return None


def is_admin(user):
    """Check if user is admin"""
    if user.is_organization_owner:
        return True
    
    try:
        role = UserRole.objects.get(user=user)
        return role.role == 'admin'
    except UserRole.DoesNotExist:
        return False


# ===== API ENDPOINTS =====

@router.get("/team/members", response=List[TeamMemberSchema], auth=JWTAuth())
def list_team_members(request):
    """List all team members in the organization with statistics"""
    from accounts.models import ESRSUserResponse, ESRSDisclosure
    from accounts.team_models import DisclosureAssignment
    
    user = request.auth
    organization = get_organization_owner(user)
    
    if not organization:
        return []
    
    # Get total disclosures count for organization
    total_disclosures = ESRSDisclosure.objects.count()
    
    # Get completed disclosures count for organization
    completed_org_disclosures = ESRSUserResponse.objects.filter(
        user__in=[organization] + list(UserRole.objects.filter(organization=organization).values_list('user', flat=True)),
        final_answer__isnull=False
    ).exclude(final_answer='').values('disclosure').distinct().count()
    
    members = []
    
    # Calculate stats for organization owner
    org_assigned = DisclosureAssignment.objects.filter(
        assigned_to=organization,
        organization=organization
    ).count()
    
    org_completed_assigned = ESRSUserResponse.objects.filter(
        disclosure__in=DisclosureAssignment.objects.filter(
            assigned_to=organization,
            organization=organization
        ).values_list('disclosure', flat=True),
        final_answer__isnull=False
    ).exclude(final_answer='').values('disclosure').distinct().count() if org_assigned > 0 else 0
    
    org_assigned_pct = (org_completed_assigned / org_assigned * 100) if org_assigned > 0 else 0
    org_completion_pct = (completed_org_disclosures / total_disclosures * 100) if total_disclosures > 0 else 0
    
    members.append({
        'id': organization.id,
        'email': organization.email,
        'role': 'admin',
        'joined_at': organization.date_joined.isoformat(),
        'is_organization_owner': True,
        'show_all_disclosures': True,  # Admin always sees all
        'assigned_tasks_count': org_assigned,
        'completed_assigned_tasks': org_completed_assigned,
        'assigned_completion_percentage': round(org_assigned_pct, 2),
        'organization_completion_percentage': round(org_completion_pct, 2)
    })
    
    # Get team members
    roles = UserRole.objects.filter(organization=organization).select_related('user')
    for role in roles:
        # Count assigned tasks
        assigned_count = DisclosureAssignment.objects.filter(
            assigned_to=role.user,
            organization=organization
        ).count()
        
        # Count completed assigned tasks
        completed_assigned = ESRSUserResponse.objects.filter(
            disclosure__in=DisclosureAssignment.objects.filter(
                assigned_to=role.user,
                organization=organization
            ).values_list('disclosure', flat=True),
            final_answer__isnull=False
        ).exclude(final_answer='').values('disclosure').distinct().count() if assigned_count > 0 else 0
        
        # Calculate percentages
        assigned_pct = (completed_assigned / assigned_count * 100) if assigned_count > 0 else 0
        
        members.append({
            'id': role.user.id,
            'email': role.user.email,
            'role': role.role,
            'joined_at': role.created_at.isoformat(),
            'is_organization_owner': False,
            'show_all_disclosures': role.show_all_disclosures,
            'assigned_tasks_count': assigned_count,
            'completed_assigned_tasks': completed_assigned,
            'assigned_completion_percentage': round(assigned_pct, 2),
            'organization_completion_percentage': round(org_completion_pct, 2)
        })
    
    return members


@router.post("/team/invite", response=MessageResponseSchema, auth=JWTAuth())
def invite_user(request, data: InviteUserSchema):
    """Invite a new user to the team (admin only)"""
    user = request.auth
    
    # Check if user is admin
    if not is_admin(user):
        return 403, {"success": False, "message": "Only admins can invite users"}
    
    organization = get_organization_owner(user)
    
    # Check if user already exists
    if User.objects.filter(email=data.email).exists():
        return 400, {"success": False, "message": "User with this email already exists"}
    
    # Check if invitation already exists
    if UserInvitation.objects.filter(email=data.email, status='pending').exists():
        return 400, {"success": False, "message": "Pending invitation already exists for this email"}
    
    # Generate temporary password
    temp_password = generate_temporary_password()
    
    # Create invitation
    with transaction.atomic():
        invitation = UserInvitation.objects.create(
            email=data.email,
            invited_by=organization,
            role=data.role,
            temporary_password=temp_password,
            expires_at=timezone.now() + timezone.timedelta(days=7)
        )
        
        # Log activity
        log_activity(
            user=user,
            organization=organization,
            action='user_invite',
            details={'email': data.email, 'role': data.role}
        )
    
    # Send invitation email
    try:
        send_invitation_email(invitation, temp_password)
    except Exception as e:
        return 500, {"success": False, "message": f"Failed to send email: {str(e)}"}
    
    return {"message": f"Invitation sent to {data.email}", "success": True}


@router.get("/team/invitations", response=List[InvitationSchema], auth=JWTAuth())
def list_invitations(request):
    """List all pending invitations (admin only)"""
    user = request.auth
    
    if not is_admin(user):
        return 403, []
    
    organization = get_organization_owner(user)
    invitations = UserInvitation.objects.filter(invited_by=organization)
    
    return [
        {
            'id': inv.id,
            'email': inv.email,
            'role': inv.role,
            'status': inv.status,
            'created_at': inv.created_at.isoformat(),
            'expires_at': inv.expires_at.isoformat(),
            'invited_by_email': inv.invited_by.email
        }
        for inv in invitations
    ]


@router.delete("/team/invitations/{invitation_id}", response=MessageResponseSchema, auth=JWTAuth())
def cancel_invitation(request, invitation_id: int):
    """Cancel a pending invitation (admin only)"""
    user = request.auth
    
    if not is_admin(user):
        return 403, {"success": False, "message": "Only admins can cancel invitations"}
    
    organization = get_organization_owner(user)
    
    try:
        invitation = UserInvitation.objects.get(id=invitation_id, invited_by=organization)
        invitation.status = 'cancelled'
        invitation.save()
        
        log_activity(
            user=user,
            organization=organization,
            action='user_invite',
            details={'action': 'cancelled', 'email': invitation.email}
        )
        
        return {"message": "Invitation cancelled", "success": True}
    except UserInvitation.DoesNotExist:
        return 404, {"success": False, "message": "Invitation not found"}


@router.post("/team/assign", response=MessageResponseSchema, auth=JWTAuth())
def assign_disclosure(request, data: AssignDisclosureSchema):
    """Assign a disclosure to a team member (admin only)"""
    user = request.auth
    
    if not is_admin(user):
        return 403, {"success": False, "message": "Only admins can assign disclosures"}
    
    organization = get_organization_owner(user)
    
    # Get disclosure
    try:
        disclosure = ESRSDisclosure.objects.get(code=data.disclosure_code)
    except ESRSDisclosure.DoesNotExist:
        return 404, {"success": False, "message": f"Disclosure {data.disclosure_code} not found"}
    
    # Get assigned user
    try:
        assigned_user = User.objects.get(email=data.assigned_to_email)
    except User.DoesNotExist:
        return 404, {"success": False, "message": f"User {data.assigned_to_email} not found"}
    
    # Verify assigned user is part of the team
    if assigned_user.id != organization.id:
        if not UserRole.objects.filter(user=assigned_user, organization=organization).exists():
            return 403, {"success": False, "message": "User is not part of this team"}
    
    # Create or update assignment
    assignment, created = DisclosureAssignment.objects.update_or_create(
        disclosure=disclosure,
        organization=organization,
        defaults={
            'assigned_to': assigned_user,
            'assigned_by': user,
            'notes': data.notes or ''
        }
    )
    
    # Log activity
    log_activity(
        user=user,
        organization=organization,
        action='assignment_change',
        disclosure=disclosure,
        details={
            'assigned_to': data.assigned_to_email,
            'action': 'created' if created else 'updated'
        }
    )
    
    action = "created" if created else "updated"
    return {"message": f"Assignment {action} successfully", "success": True}


@router.get("/team/assignments", response=List[AssignmentSchema], auth=JWTAuth())
def list_assignments(request):
    """List all disclosure assignments"""
    user = request.auth
    organization = get_organization_owner(user)
    
    if not organization:
        return []
    
    assignments = DisclosureAssignment.objects.filter(
        organization=organization
    ).select_related('disclosure', 'assigned_to', 'assigned_by')
    
    return [
        {
            'id': a.id,
            'disclosure_code': a.disclosure.code,
            'disclosure_title': a.disclosure.name,
            'assigned_to_email': a.assigned_to.email,
            'assigned_by_email': a.assigned_by.email if a.assigned_by else None,
            'assigned_at': a.assigned_at.isoformat(),
            'notes': a.notes
        }
        for a in assignments
    ]


@router.delete("/team/assignments/{assignment_id}", response=MessageResponseSchema, auth=JWTAuth())
def remove_assignment(request, assignment_id: int):
    """Remove a disclosure assignment (admin only)"""
    user = request.auth
    
    if not is_admin(user):
        return 403, {"success": False, "message": "Only admins can remove assignments"}
    
    organization = get_organization_owner(user)
    
    try:
        assignment = DisclosureAssignment.objects.get(id=assignment_id, organization=organization)
        disclosure = assignment.disclosure
        assigned_to_email = assignment.assigned_to.email
        
        assignment.delete()
        
        log_activity(
            user=user,
            organization=organization,
            action='assignment_change',
            disclosure=disclosure,
            details={'action': 'removed', 'assigned_to': assigned_to_email}
        )
        
        return {"message": "Assignment removed", "success": True}
    except DisclosureAssignment.DoesNotExist:
        return 404, {"success": False, "message": "Assignment not found"}


@router.get("/team/activity", response=List[ActivityLogSchema], auth=JWTAuth())
def get_activity_log(request, limit: int = 100):
    """Get activity log for the organization"""
    user = request.auth
    organization = get_organization_owner(user)
    
    if not organization:
        return []
    
    activities = ActivityLog.objects.filter(
        organization=organization
    ).select_related('user', 'disclosure')[:limit]
    
    return [
        {
            'id': a.id,
            'user_email': a.user.email if a.user else None,
            'action': a.action,
            'disclosure_code': a.disclosure.code if a.disclosure else None,
            'details': a.details,
            'timestamp': a.timestamp.isoformat()
        }
        for a in activities
    ]


@router.delete("/team/members/{member_id}", response=MessageResponseSchema, auth=JWTAuth())
def remove_team_member(request, member_id: int):
    """Remove a team member (admin only)"""
    user = request.auth
    
    if not is_admin(user):
        return 403, {"success": False, "message": "Only admins can remove team members"}
    
    organization = get_organization_owner(user)
    
    try:
        member_user = User.objects.get(id=member_id)
        role = UserRole.objects.get(user=member_user, organization=organization)
        
        # Delete user role and all related data
        with transaction.atomic():
            role.delete()
            
            # Optionally delete the user account itself
            # member_user.delete()
            
            log_activity(
                user=user,
                organization=organization,
                action='user_invite',
                details={'action': 'removed', 'email': member_user.email}
            )
        
        return {"message": f"Team member {member_user.email} removed", "success": True}
    except (User.DoesNotExist, UserRole.DoesNotExist):
        return 404, {"success": False, "message": "Team member not found"}


@router.put("/team/members/{member_id}/role", response=MessageResponseSchema, auth=JWTAuth())
def change_member_role(request, member_id: int, role: str):
    """Change a team member's role (admin only)"""
    user = request.auth
    
    if not is_admin(user):
        return 403, {"success": False, "message": "Only admins can change roles"}
    
    if role not in ['admin', 'member']:
        return 400, {"success": False, "message": "Invalid role. Must be 'admin' or 'member'"}
    
    organization = get_organization_owner(user)
    
    try:
        member_user = User.objects.get(id=member_id)
        member_role = UserRole.objects.get(user=member_user, organization=organization)
        
        old_role = member_role.role
        member_role.role = role
        member_role.save()
        
        log_activity(
            user=user,
            organization=organization,
            action='user_invite',
            details={
                'action': 'role_changed',
                'email': member_user.email,
                'old_role': old_role,
                'new_role': role
            }
        )
        
        return {"message": f"Role changed to {role}", "success": True}
    except (User.DoesNotExist, UserRole.DoesNotExist):
        return 404, {"success": False, "message": "Team member not found"}


@router.put("/team/members/{member_id}/view-filter", response=MessageResponseSchema, auth=JWTAuth())
def update_view_filter(request, member_id: int, show_all: bool):
    """Update whether a team member sees all disclosures or only assigned ones (admin only)"""
    user = request.auth
    
    if not is_admin(user):
        return 403, {"success": False, "message": "Only admins can change view settings"}
    
    organization = get_organization_owner(user)
    
    try:
        member_user = User.objects.get(id=member_id)
        member_role = UserRole.objects.get(user=member_user, organization=organization)
        
        member_role.show_all_disclosures = show_all
        member_role.save()
        
        log_activity(
            user=user,
            organization=organization,
            action='user_invite',
            details={
                'action': 'view_filter_changed',
                'email': member_user.email,
                'show_all_disclosures': show_all
            }
        )
        
        filter_type = "all disclosures" if show_all else "only assigned disclosures"
        return {"message": f"View filter updated: user will see {filter_type}", "success": True}
    except (User.DoesNotExist, UserRole.DoesNotExist):
        return 404, {"success": False, "message": "Team member not found"}
