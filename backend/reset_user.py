"""
Reset user mihael.veber@gmail.com - delete all documents, images, conversations, responses
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import User, Document, ESRSUserResponse
from django.db import connection

# Find user
user_email = "mihael.veber@gmail.com"
try:
    user = User.objects.get(email=user_email)
    print(f"✅ Found user: {user.email} (ID: {user.id})")
    
    # Delete conversation messages and threads using raw SQL to avoid circular import
    with connection.cursor() as cursor:
        # Get counts first
        cursor.execute("SELECT COUNT(*) FROM conversation_messages WHERE thread_id IN (SELECT id FROM conversation_threads WHERE user_id = %s)", [user.id])
        messages_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM conversation_threads WHERE user_id = %s", [user.id])
        threads_count = cursor.fetchone()[0]
        
        # Delete
        cursor.execute("DELETE FROM conversation_messages WHERE thread_id IN (SELECT id FROM conversation_threads WHERE user_id = %s)", [user.id])
        cursor.execute("DELETE FROM conversation_threads WHERE user_id = %s", [user.id])
        
        print(f"🗑️  Deleted {messages_count} conversation messages")
        print(f"🗑️  Deleted {threads_count} conversation threads")
    
    # Delete all user responses (this clears ai_answer, final_answer, images, charts, etc.)
    responses_count = ESRSUserResponse.objects.filter(user=user).count()
    ESRSUserResponse.objects.filter(user=user).delete()
    print(f"🗑️  Deleted {responses_count} user responses (AI answers, approved answers, images)")
    
    # Delete all user documents
    docs_count = Document.objects.filter(user=user).count()
    for doc in Document.objects.filter(user=user):
        # Delete physical file
        if doc.file_path and os.path.exists(doc.file_path):
            os.remove(doc.file_path)
            print(f"   📄 Deleted file: {doc.file_name}")
    
    Document.objects.filter(user=user).delete()
    print(f"🗑️  Deleted {docs_count} documents")
    
    # Reset wizard status
    user.wizard_completed = False
    user.save()
    print(f"🔄 Reset wizard_completed to False")
    
    print(f"\n✅ User {user_email} has been reset - like first login!")
    
except User.DoesNotExist:
    print(f"❌ User {user_email} not found")
