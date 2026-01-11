#!/bin/bash

echo "📊 Checking admin user status..."
docker-compose exec backend python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()

# Check superuser
admin = User.objects.filter(is_superuser=True).first()
if admin:
    print(f'✅ Superuser exists: {admin.email}')
else:
    print('❌ No superuser found! Create one with: docker-compose exec backend python manage.py createsuperuser')

# Show total users
total = User.objects.count()
print(f'👥 Total users: {total}')
"

echo ""
echo "🚀 Admin panel running at: http://localhost:5174"
echo "🔧 Backend API running at: http://localhost:8090/api/admin"
echo ""
echo "To test admin API, first login to get JWT token:"
echo "  curl -X POST http://localhost:8090/api/login/ -H 'Content-Type: application/json' -d '{\"email\":\"admin@example.com\",\"password\":\"yourpassword\"}'"
