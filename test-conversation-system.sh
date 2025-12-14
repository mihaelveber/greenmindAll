#!/bin/bash
# Quick Test Script for AI Conversation System
# Run this to verify everything is working

echo "🧪 AI Conversation System - Quick Test"
echo "======================================"
echo ""

# Check services
echo "1️⃣ Checking services..."
docker compose ps

echo ""
echo "2️⃣ Backend logs (last 10 lines)..."
docker compose logs backend --tail 10

echo ""
echo "3️⃣ Database status..."
docker compose exec backend python manage.py shell -c "
from accounts.models import AIConversation, ItemVersion, ESRSUserResponse
print('Users with responses:', ESRSUserResponse.objects.values('user').distinct().count())
print('Total responses:', ESRSUserResponse.objects.count())
print('Responses with AI answers:', ESRSUserResponse.objects.exclude(ai_answer__isnull=True).exclude(ai_answer='').count())
print('AI Conversations:', AIConversation.objects.count())
print('Item Versions:', ItemVersion.objects.count())
"

echo ""
echo "4️⃣ Test data sample..."
docker compose exec backend python manage.py shell -c "
from accounts.models import ESRSUserResponse
r = ESRSUserResponse.objects.exclude(ai_answer__isnull=True).exclude(ai_answer='').first()
if r:
    print(f'Sample disclosure: {r.disclosure.code}')
    print(f'Response ID: {r.id}')
    print(f'AI answer length: {len(r.ai_answer or \"\")} chars')
    print(f'Manual answer: {\"Yes\" if r.manual_answer else \"No\"}')
else:
    print('No sample data found')
"

echo ""
echo "✅ System Check Complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Open browser: http://localhost:5173"
echo "2. Login to application"
echo "3. Navigate to any ESRS disclosure"
echo "4. Click '💬 Refine with AI' button"
echo "5. Type instruction and press Ctrl+Enter"
echo "6. Watch for AI response in blue bubble"
echo "7. Click 'Use This Version' to apply"
echo ""
echo "📖 For detailed testing: see TESTING_GUIDE.md"
echo "🎨 For UI details: see UI_VISUAL_GUIDE.md"
echo "🚀 For deployment status: see DEPLOYMENT_SUMMARY.md"
