#!/bin/bash

echo "🚀 Zagon Greenmind AI System..."
echo ""
echo "📦 Gradim Docker containers..."
docker-compose build

echo ""
echo "🎯 Zagon vseh servisov..."
docker-compose up -d

echo ""
echo "⏳ Čakam da se servisi zaženejo..."
sleep 10

echo ""
echo "✅ Aplikacija je na voljo:"
echo "   Frontend:      http://localhost:5173"
echo "   Admin Panel:   http://localhost:5174 ⭐ NEW!"
echo "   Backend API:   http://localhost:8090/api"
echo "   API Docs:      http://localhost:8090/api/docs"
echo "   Flower:        http://localhost:5555"
echo ""
echo "👤 Test account:"
echo "   Email:    mihael@example.com"
echo "   Username: mihaelv"
echo "   Password: corelite"
echo ""
echo "📊 Admin Access:"
echo "   Superuser: mihael.veber@gmail.com"
echo ""
echo "🎯 Za ustavitev: docker-compose down"
echo "📝 Za loge: docker-compose logs -f [service_name]"
echo ""
