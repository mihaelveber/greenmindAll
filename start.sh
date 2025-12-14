#!/bin/bash

echo "🚀 Zagon Auth Project..."
echo ""
echo "📦 Gradim Docker containers..."
docker-compose build

echo ""
echo "🎯 Zagon vseh servisov..."
docker-compose up

echo ""
echo "✅ Aplikacija je na voljo:"
echo "   Frontend: http://localhost:5173"
echo "   Backend API: http://localhost:8090/api"
echo "   API Docs: http://localhost:8090/api/docs"
echo "   Flower: http://localhost:5555"
echo ""
echo "�� Test account:"
echo "   Email: mihael@example.com"
echo "   Username: mihaelv"
echo "   Password: corelite"
