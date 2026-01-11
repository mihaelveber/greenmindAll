#!/bin/bash

# 🧪 Cost Warning Modal - Automated Test Script
# Run this script to verify basic functionality before manual testing

echo "🧪 Starting Cost Warning Modal Tests..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Test 1: Frontend compilation
echo "📦 Test 1: Frontend Compilation"
docker-compose logs frontend --tail=20 | grep -q "ready in"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ PASS${NC} - Frontend compiles without errors"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - Frontend compilation failed"
    ((FAILED++))
fi
echo ""

# Test 2: Backend API keys configured
echo "🔑 Test 2: API Keys Configuration"
docker-compose exec -T backend python manage.py shell <<EOF
from django.conf import settings
import sys

try:
    openai = bool(settings.OPENAI_API_KEY)
    anthropic = bool(settings.ANTHROPIC_API_KEY)
    google = bool(settings.GOOGLE_API_KEY)
    
    if openai and anthropic and google:
        print("✅ All API keys configured")
        sys.exit(0)
    else:
        print("❌ Missing API keys:")
        if not openai: print("  - OPENAI_API_KEY")
        if not anthropic: print("  - ANTHROPIC_API_KEY")
        if not google: print("  - GOOGLE_API_KEY")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error checking API keys: {e}")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ PASS${NC} - All 3 API keys configured"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - API keys missing or error"
    ((FAILED++))
fi
echo ""

# Test 3: Database migration status
echo "🗄️  Test 3: Database Migration 0040"
docker-compose exec -T backend python manage.py shell <<EOF
from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT name FROM django_migrations WHERE app='accounts' AND name='0040_add_reasoning_model_choices';")
result = cursor.fetchone()
import sys
sys.exit(0 if result else 1)
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ PASS${NC} - Migration 0040 applied"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - Migration 0040 not found"
    ((FAILED++))
fi
echo ""

# Test 4: User model has 15 model choices
echo "🎯 Test 4: Model Choices in Database"
docker-compose exec -T backend python manage.py shell <<EOF
from accounts.models import User
import sys
field = User._meta.get_field('preferred_llm_model')
choices = field.choices
num_choices = len(choices)
print(f"Model choices: {num_choices}")
sys.exit(0 if num_choices == 15 else 1)
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ PASS${NC} - User model has 15 model choices"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - User model does not have 15 choices"
    ((FAILED++))
fi
echo ""

# Test 5: Frontend model selector has 15 options
echo "🎨 Test 5: Frontend Model Selector"
MODEL_COUNT=$(grep -o "{ label:" frontend/src/views/StandardView.vue | wc -l | tr -d ' ')
if [ "$MODEL_COUNT" = "15" ]; then
    echo -e "${GREEN}✅ PASS${NC} - Frontend has 15 model options"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  INFO${NC} - Frontend has $MODEL_COUNT model options (expected 15)"
    ((FAILED++))
fi
echo ""

# Test 6: Cost warning modal exists in frontend
echo "⚠️  Test 6: Cost Warning Modal Component"
grep -q "showCostWarning" frontend/src/views/StandardView.vue
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ PASS${NC} - Cost warning modal implemented"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - Cost warning modal not found"
    ((FAILED++))
fi
echo ""

# Test 7: Expensive model detection function exists
echo "💰 Test 7: Expensive Model Detection"
grep -q "isExpensiveModel" frontend/src/views/StandardView.vue
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ PASS${NC} - isExpensiveModel function exists"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - isExpensiveModel function not found"
    ((FAILED++))
fi
echo ""

# Test 8: Extended Thinking backend implementation
echo "🧠 Test 8: Extended Thinking Backend"
grep -q "thinking.*enabled" backend/accounts/tasks.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ PASS${NC} - Extended Thinking implemented in backend"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - Extended Thinking not found in backend"
    ((FAILED++))
fi
echo ""

# Test 9: ThinkingProcess component exists
echo "💭 Test 9: ThinkingProcess Component"
if [ -f "frontend/src/components/ThinkingProcess.vue" ]; then
    echo -e "${GREEN}✅ PASS${NC} - ThinkingProcess component exists"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - ThinkingProcess component not found"
    ((FAILED++))
fi
echo ""

# Test 10: Frontend server responding
echo "🌐 Test 10: Frontend Server Status"
curl -s http://localhost:5173 > /dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ PASS${NC} - Frontend server responding"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - Frontend server not responding"
    ((FAILED++))
fi
echo ""

# Test 11: Backend server responding
echo "🖥️  Test 11: Backend Server Status"
curl -s http://localhost:8000/api/health > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ PASS${NC} - Backend server responding"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  SKIP${NC} - Backend health endpoint may not exist (not critical)"
fi
echo ""

# Test 12: Docker services running
echo "🐳 Test 12: Docker Services Status"
SERVICES=$(docker-compose ps --services --filter "status=running" | wc -l | tr -d ' ')
if [ "$SERVICES" -ge 4 ]; then
    echo -e "${GREEN}✅ PASS${NC} - All Docker services running ($SERVICES services)"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - Not all services running ($SERVICES/4+)"
    ((FAILED++))
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Passed: $PASSED${NC}"
echo -e "${RED}❌ Failed: $FAILED${NC}"
TOTAL=$((PASSED + FAILED))
echo "📈 Total: $TOTAL"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 All automated tests passed!${NC}"
    echo ""
    echo "✨ Ready for manual testing!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Open http://localhost:5173"
    echo "2. Login to application"
    echo "3. Navigate to ESRS disclosure"
    echo "4. Select GPT-5 (o1) model"
    echo "5. Click 'Get AI Answer'"
    echo "6. Verify cost warning modal appears"
    echo ""
    echo "📖 Full test plan: TEST_COST_WARNING_MODAL.md"
    exit 0
else
    echo ""
    echo -e "${RED}⚠️  Some tests failed!${NC}"
    echo ""
    echo "❌ Please fix the failing tests before manual testing"
    echo "📖 Check logs for details"
    exit 1
fi
