"""
Admin API endpoints for user management, token usage, and cost tracking
"""
from ninja import Router, Schema
from typing import List, Optional
from datetime import datetime, timedelta, date
from decimal import Decimal
from django.db.models import Sum, Count, Avg, Q, F
from django.db.models.functions import TruncDate
from django.contrib.auth import get_user_model

from accounts.token_models import TokenUsage, OrganizationTokenStats
from accounts.models import ESRSUserResponse, UserRole, ActivityLog
from accounts.auth import AdminAuth

User = get_user_model()
router = Router()


# Schemas
class TokenUsageSchema(Schema):
    id: int
    user_email: str
    organization_email: str
    action_type: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    timestamp: datetime
    request_duration_ms: Optional[int] = None
    disclosure_code: Optional[str] = None


class UserTokenStatsSchema(Schema):
    user_id: int
    user_email: str
    role: str
    total_tokens: int
    total_cost_usd: float
    api_calls_count: int
    last_activity: Optional[datetime] = None


class OrganizationStatsSchema(Schema):
    organization_id: int
    organization_email: str
    company_type: Optional[str] = None
    total_users: int
    total_tokens: int
    total_cost_usd: float
    api_calls_count: int
    created_at: datetime


class DailyCostSchema(Schema):
    date: str  # YYYY-MM-DD
    total_tokens: int
    total_cost_usd: float
    api_calls_count: int
    ai_answer_tokens: int
    conversation_tokens: int
    rag_search_tokens: int


class UserDetailSchema(Schema):
    id: int
    email: str
    first_name: str
    last_name: str
    role: str
    company_type: Optional[str] = None
    wizard_completed: bool
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    total_tokens: int
    total_cost_usd: float
    completion_percentage: float
    team_members_count: int


class AnalyticsEngagementSchema(Schema):
    user_id: int
    user_email: str
    total_logins: int
    active_days: int
    avg_session_duration_minutes: Optional[float] = None
    last_active: Optional[datetime] = None
    total_actions: int


class AnalyticsProductivitySchema(Schema):
    user_id: int
    user_email: str
    total_disclosures: int
    completed_disclosures: int
    completion_rate: float
    ai_answers_used: int
    manual_answers_used: int
    ai_usage_rate: float
    avg_tokens_per_disclosure: float


class AnalyticsSummarySchema(Schema):
    total_users: int
    active_users_7d: int
    active_users_30d: int
    total_api_calls: int
    total_tokens_used: int
    total_cost_usd: float
    avg_cost_per_user: float
    most_active_user: Optional[str] = None
    most_expensive_user: Optional[str] = None


# Helper function to check admin access
def require_admin(request):
    """Check if user is superuser/admin"""
    if not request.auth or not request.auth.is_superuser:
        return {"error": "Admin access required"}, 403
    return None


@router.get(
    "/token-usage",
    response=List[TokenUsageSchema],
    auth=AdminAuth(),
    summary="Get token usage records"
)
def list_token_usage(
    request,
    user_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    action_type: Optional[str] = None,
    days: int = 30,
    limit: int = 100
):
    """
    Get token usage records with filters.
    Admin-only endpoint.
    
    Query params:
    - user_id: Filter by specific user
    - organization_id: Filter by organization
    - action_type: Filter by action type (ai_answer, conversation, rag_search, etc.)
    - days: Number of days to look back (default: 30)
    - limit: Max records to return (default: 100, max: 1000)
    """
    
    # Build query
    queryset = TokenUsage.objects.select_related('user', 'organization', 'disclosure')
    
    # Date filter
    since_date = datetime.now() - timedelta(days=days)
    queryset = queryset.filter(timestamp__gte=since_date)
    
    # Apply filters
    if user_id:
        queryset = queryset.filter(user_id=user_id)
    if organization_id:
        queryset = queryset.filter(organization_id=organization_id)
    if action_type:
        queryset = queryset.filter(action_type=action_type)
    
    # Limit results
    limit = min(limit, 1000)  # Max 1000 records
    queryset = queryset[:limit]
    
    # Format response
    results = []
    for usage in queryset:
        results.append(TokenUsageSchema(
            id=usage.id,
            user_email=usage.user.email,
            organization_email=usage.organization.email,
            action_type=usage.action_type,
            model=usage.model,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            cost_usd=float(usage.cost_usd),
            timestamp=usage.timestamp,
            request_duration_ms=usage.request_duration_ms,
            disclosure_code=usage.disclosure.code if usage.disclosure else None
        ))
    
    return results


@router.get(
    "/users/stats",
    response=List[UserTokenStatsSchema],
    auth=AdminAuth(),
    summary="Get user statistics with token usage"
)
def list_users_with_stats(
    request,
    organization_id: Optional[int] = None,
    days: int = 30
):
    """
    Get all users with token usage statistics.
    Admin-only endpoint.
    
    Query params:
    - organization_id: Filter by organization
    - days: Number of days for statistics (default: 30)
    """
    
    # Get all users or filter by organization
    users_query = User.objects.all()
    if organization_id:
        # Get org and all its members
        users_query = User.objects.filter(
            Q(id=organization_id) | Q(created_by_id=organization_id)
        )
    
    since_date = datetime.now() - timedelta(days=days)
    
    results = []
    for user in users_query:
        # Get token stats
        token_stats = TokenUsage.objects.filter(
            user=user,
            timestamp__gte=since_date
        ).aggregate(
            total_tokens=Sum('total_tokens'),
            total_cost=Sum('cost_usd'),
            api_calls=Count('id')
        )
        
        # Get role
        try:
            role_obj = UserRole.objects.get(user=user)
            role = role_obj.role
        except UserRole.DoesNotExist:
            role = 'owner' if not user.created_by else 'member'
        
        # Get last activity
        last_activity = ActivityLog.objects.filter(user=user).order_by('-timestamp').first()
        
        results.append(UserTokenStatsSchema(
            user_id=user.id,
            user_email=user.email,
            role=role,
            total_tokens=token_stats['total_tokens'] or 0,
            total_cost_usd=float(token_stats['total_cost'] or 0),
            api_calls_count=token_stats['api_calls'] or 0,
            last_activity=last_activity.timestamp if last_activity else None
        ))
    
    # Sort by cost descending
    results.sort(key=lambda x: x.total_cost_usd, reverse=True)
    
    return results


@router.get(
    "/organizations/stats",
    response=List[OrganizationStatsSchema],
    auth=AdminAuth(),
    summary="Get organization statistics"
)
def list_organizations_with_stats(request, days: int = 30):
    """
    Get all organizations with aggregated token usage.
    Admin-only endpoint.
    
    Query params:
    - days: Number of days for statistics (default: 30)
    """
    
    # Get all organization owners (users without created_by)
    organizations = User.objects.filter(created_by__isnull=True)
    
    since_date = datetime.now() - timedelta(days=days)
    
    results = []
    for org in organizations:
        # Get token stats for org and all members
        token_stats = TokenUsage.objects.filter(
            organization=org,
            timestamp__gte=since_date
        ).aggregate(
            total_tokens=Sum('total_tokens'),
            total_cost=Sum('cost_usd'),
            api_calls=Count('id')
        )
        
        # Count members
        members_count = User.objects.filter(created_by=org).count()
        
        results.append(OrganizationStatsSchema(
            organization_id=org.id,
            organization_email=org.email,
            company_type=org.company_type,
            total_users=members_count + 1,  # +1 for owner
            total_tokens=token_stats['total_tokens'] or 0,
            total_cost_usd=float(token_stats['total_cost'] or 0),
            api_calls_count=token_stats['api_calls'] or 0,
            created_at=org.date_joined
        ))
    
    # Sort by cost descending
    results.sort(key=lambda x: x.total_cost_usd, reverse=True)
    
    return results


@router.get(
    "/costs/daily",
    response=List[DailyCostSchema],
    auth=AdminAuth(),
    summary="Get daily cost breakdown"
)
def get_daily_costs(
    request,
    organization_id: Optional[int] = None,
    days: int = 30
):
    """
    Get daily cost breakdown.
    Admin-only endpoint.
    
    Query params:
    - organization_id: Filter by organization
    - days: Number of days (default: 30, max: 365)
    """
    
    days = min(days, 365)  # Max 1 year
    since_date = datetime.now() - timedelta(days=days)
    
    # Build query
    queryset = TokenUsage.objects.filter(timestamp__gte=since_date)
    if organization_id:
        queryset = queryset.filter(organization_id=organization_id)
    
    # Group by date and action type
    daily_stats = queryset.annotate(
        date=TruncDate('timestamp')
    ).values('date').annotate(
        total_tokens=Sum('total_tokens'),
        total_cost=Sum('cost_usd'),
        api_calls=Count('id'),
        ai_answer_tokens=Sum('total_tokens', filter=Q(action_type='ai_answer')),
        conversation_tokens=Sum('total_tokens', filter=Q(action_type='conversation')),
        rag_search_tokens=Sum('total_tokens', filter=Q(action_type='rag_search'))
    ).order_by('date')
    
    results = []
    for stat in daily_stats:
        results.append(DailyCostSchema(
            date=stat['date'].isoformat(),
            total_tokens=stat['total_tokens'] or 0,
            total_cost_usd=float(stat['total_cost'] or 0),
            api_calls_count=stat['api_calls'] or 0,
            ai_answer_tokens=stat['ai_answer_tokens'] or 0,
            conversation_tokens=stat['conversation_tokens'] or 0,
            rag_search_tokens=stat['rag_search_tokens'] or 0
        ))
    
    return results


@router.get(
    "/users",
    response=List[UserDetailSchema],
    auth=AdminAuth(),
    summary="Get all users with details"
)
def list_all_users(request):
    """
    Get all users with comprehensive details.
    Admin-only endpoint.
    """
    
    users = User.objects.all().order_by('-date_joined')
    
    results = []
    for user in users:
        # Get token stats (all time)
        token_stats = TokenUsage.objects.filter(user=user).aggregate(
            total_tokens=Sum('total_tokens'),
            total_cost=Sum('cost_usd')
        )
        
        # Get role
        try:
            role_obj = UserRole.objects.get(user=user)
            role = role_obj.role
        except UserRole.DoesNotExist:
            role = 'owner' if not user.created_by else 'member'
        
        # Calculate completion percentage
        total_disclosures = ESRSUserResponse.objects.filter(user=user).count()
        completed_disclosures = ESRSUserResponse.objects.filter(
            user=user
        ).exclude(
            Q(final_answer__isnull=True) | Q(final_answer='')
        ).count()
        
        completion_pct = (completed_disclosures / total_disclosures * 100) if total_disclosures > 0 else 0
        
        # Count team members
        team_members_count = User.objects.filter(created_by=user).count()
        
        results.append(UserDetailSchema(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=role,
            company_type=user.company_type,
            wizard_completed=user.wizard_completed,
            is_active=user.is_active,
            created_at=user.date_joined,
            last_login=user.last_login,
            total_tokens=token_stats['total_tokens'] or 0,
            total_cost_usd=float(token_stats['total_cost'] or 0),
            completion_percentage=round(completion_pct, 1),
            team_members_count=team_members_count
        ))
    
    return results


@router.get(
    "/analytics/engagement",
    response=List[AnalyticsEngagementSchema],
    auth=AdminAuth(),
    summary="Get user engagement analytics"
)
def get_engagement_analytics(request, days: int = 30):
    """
    Get user engagement metrics.
    Admin-only endpoint.
    
    Tracks: logins, active days, total actions, last active
    """
    
    since_date = datetime.now() - timedelta(days=days)
    users = User.objects.all()
    
    results = []
    for user in users:
        # Count activity logs (as proxy for "logins" and actions)
        activity_count = ActivityLog.objects.filter(
            user=user,
            timestamp__gte=since_date
        ).count()
        
        # Count active days (days with at least one activity)
        active_days = ActivityLog.objects.filter(
            user=user,
            timestamp__gte=since_date
        ).annotate(
            date=TruncDate('timestamp')
        ).values('date').distinct().count()
        
        # Get last activity
        last_activity = ActivityLog.objects.filter(user=user).order_by('-timestamp').first()
        
        results.append(AnalyticsEngagementSchema(
            user_id=user.id,
            user_email=user.email,
            total_logins=user.last_login is not None,  # Simplified
            active_days=active_days,
            avg_session_duration_minutes=None,  # Would need session tracking
            last_active=last_activity.timestamp if last_activity else None,
            total_actions=activity_count
        ))
    
    # Sort by active days descending
    results.sort(key=lambda x: x.active_days, reverse=True)
    
    return results


@router.get(
    "/analytics/productivity",
    response=List[AnalyticsProductivitySchema],
    auth=AdminAuth(),
    summary="Get user productivity analytics"
)
def get_productivity_analytics(request):
    """
    Get user productivity metrics.
    Admin-only endpoint.
    
    Tracks: completion rates, AI vs Manual usage, tokens per disclosure
    """
    
    users = User.objects.all()
    
    results = []
    for user in users:
        # Get disclosure stats
        total_disclosures = ESRSUserResponse.objects.filter(user=user).count()
        
        if total_disclosures == 0:
            continue  # Skip users with no responses
        
        completed_disclosures = ESRSUserResponse.objects.filter(
            user=user
        ).exclude(
            Q(final_answer__isnull=True) | Q(final_answer='')
        ).count()
        
        # Count AI vs Manual answers
        ai_answers = ESRSUserResponse.objects.filter(
            user=user
        ).exclude(
            Q(ai_answer__isnull=True) | Q(ai_answer='')
        ).count()
        
        manual_answers = ESRSUserResponse.objects.filter(
            user=user
        ).exclude(
            Q(manual_answer__isnull=True) | Q(manual_answer='')
        ).count()
        
        # Get token usage stats
        token_stats = TokenUsage.objects.filter(
            user=user,
            action_type='ai_answer'
        ).aggregate(
            total_tokens=Sum('total_tokens')
        )
        
        total_tokens = token_stats['total_tokens'] or 0
        avg_tokens = total_tokens / completed_disclosures if completed_disclosures > 0 else 0
        
        completion_rate = (completed_disclosures / total_disclosures * 100) if total_disclosures > 0 else 0
        ai_usage_rate = (ai_answers / total_disclosures * 100) if total_disclosures > 0 else 0
        
        results.append(AnalyticsProductivitySchema(
            user_id=user.id,
            user_email=user.email,
            total_disclosures=total_disclosures,
            completed_disclosures=completed_disclosures,
            completion_rate=round(completion_rate, 1),
            ai_answers_used=ai_answers,
            manual_answers_used=manual_answers,
            ai_usage_rate=round(ai_usage_rate, 1),
            avg_tokens_per_disclosure=round(avg_tokens, 0)
        ))
    
    # Sort by completion rate descending
    results.sort(key=lambda x: x.completion_rate, reverse=True)
    
    return results


@router.get(
    "/analytics/summary",
    response=AnalyticsSummarySchema,
    auth=AdminAuth(),
    summary="Get system analytics summary"
)
def get_analytics_summary(request):
    """
    Get overall system analytics summary.
    Admin-only endpoint.
    """
    
    # Total users
    total_users = User.objects.count()
    
    # Active users
    since_7d = datetime.now() - timedelta(days=7)
    since_30d = datetime.now() - timedelta(days=30)
    
    active_7d = ActivityLog.objects.filter(
        timestamp__gte=since_7d
    ).values('user').distinct().count()
    
    active_30d = ActivityLog.objects.filter(
        timestamp__gte=since_30d
    ).values('user').distinct().count()
    
    # Token stats
    token_stats = TokenUsage.objects.aggregate(
        total_calls=Count('id'),
        total_tokens=Sum('total_tokens'),
        total_cost=Sum('cost_usd')
    )
    
    # Most active user (by actions)
    most_active = ActivityLog.objects.values('user__email').annotate(
        action_count=Count('id')
    ).order_by('-action_count').first()
    
    # Most expensive user (by tokens)
    most_expensive = TokenUsage.objects.values('user__email').annotate(
        total_cost=Sum('cost_usd')
    ).order_by('-total_cost').first()
    
    total_cost = float(token_stats['total_cost'] or 0)
    avg_cost = total_cost / total_users if total_users > 0 else 0
    
    return AnalyticsSummarySchema(
        total_users=total_users,
        active_users_7d=active_7d,
        active_users_30d=active_30d,
        total_api_calls=token_stats['total_calls'] or 0,
        total_tokens_used=token_stats['total_tokens'] or 0,
        total_cost_usd=total_cost,
        avg_cost_per_user=round(avg_cost, 2),
        most_active_user=most_active['user__email'] if most_active else None,
        most_expensive_user=most_expensive['user__email'] if most_expensive else None
    )


# ============================================
# USER DOCUMENT PERMISSIONS
# ============================================

class StandardTypeSchema(Schema):
    """Available standard types"""
    code: str
    label: str


class UserPermissionsSchema(Schema):
    """User's allowed standard types"""
    user_id: int
    user_email: str
    allowed_standards: List[str]


class UpdatePermissionsSchema(Schema):
    """Update user's allowed standards"""
    allowed_standards: List[str]


@router.get(
    "/standard-types",
    response=List[StandardTypeSchema],
    auth=AdminAuth(),
    tags=["admin"]
)
def get_standard_types(request):
    """
    Get all available standard types
    
    Requires: Superuser
    """
    if not request.auth.is_superuser:
        return 403, {"message": "Superuser access required"}
    
    from accounts.models import ESRSCategory
    
    return [
        StandardTypeSchema(code=code, label=label)
        for code, label in ESRSCategory.STANDARD_TYPE_CHOICES
    ]


@router.get(
    "/users/{user_id}/permissions",
    response=UserPermissionsSchema,
    auth=AdminAuth(),
    tags=["admin"]
)
def get_user_permissions(request, user_id: int):
    """
    Get user's document access permissions
    
    Requires: Superuser
    Returns: List of allowed standard types. Empty = all allowed.
    """
    if not request.auth.is_superuser:
        return 403, {"message": "Superuser access required"}
    
    try:
        user = User.objects.get(id=user_id)
        return UserPermissionsSchema(
            user_id=user.id,
            user_email=user.email,
            allowed_standards=user.allowed_standards or []
        )
    except User.DoesNotExist:
        return 404, {"message": "User not found"}


@router.put(
    "/users/{user_id}/permissions",
    response=UserPermissionsSchema,
    auth=AdminAuth(),
    tags=["admin"]
)
def update_user_permissions(request, user_id: int, payload: UpdatePermissionsSchema):
    """
    Update user's document access permissions
    
    Requires: Superuser
    Payload: { "allowed_standards": ["ESRS", "ISO9001", "GDPR"] }
    
    Empty list = all standards allowed
    """
    if not request.auth.is_superuser:
        return 403, {"message": "Superuser access required"}
    
    try:
        user = User.objects.get(id=user_id)
        user.allowed_standards = payload.allowed_standards
        user.save(update_fields=['allowed_standards'])
        
        return UserPermissionsSchema(
            user_id=user.id,
            user_email=user.email,
            allowed_standards=user.allowed_standards or []
        )
    except User.DoesNotExist:
        return 404, {"message": "User not found"}

