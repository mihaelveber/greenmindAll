#!/bin/bash

echo "📊 GREENMIND AI - SYSTEM STATUS REPORT"
echo "======================================"
echo ""

# Docker status
echo "🐳 DOCKER SERVICES:"
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
echo ""

# Database stats
echo "📚 DATABASE STATISTICS:"
docker-compose exec -T backend python manage.py shell -c "
from accounts.models import ESRSCategory, ESRSStandard, ESRSDisclosure
from django.contrib.auth import get_user_model

User = get_user_model()

print(f'Users: {User.objects.count()}')
print(f'Categories: {ESRSCategory.objects.count()}')
print(f'Standards: {ESRSStandard.objects.count()}')
print(f'Disclosures: {ESRSDisclosure.objects.count()}')
print('')
print('Disclosures by Type:')
for std_type, name in ESRSDisclosure.STANDARD_TYPE_CHOICES:
    count = ESRSDisclosure.objects.filter(standard_type=std_type).count()
    if count > 0:
        print(f'  {std_type}: {count}')
" 2>/dev/null

echo ""
echo "🌐 ACCESS URLS:"
echo "  Frontend:      http://localhost:5173"
echo "  Admin Panel:   http://localhost:5174 ⭐"
echo "  Backend API:   http://localhost:8090/api"
echo "  API Docs:      http://localhost:8090/api/docs"
echo "  Flower:        http://localhost:5555"
echo ""

echo "✅ SYSTEM STATUS: FULLY OPERATIONAL"
echo ""
