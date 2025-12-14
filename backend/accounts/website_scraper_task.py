from celery import shared_task
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def scrape_company_website_task(self, user_id: int, website_url: str):
    """Celery task to scrape and parse company website HTML content"""
    from accounts.models import User, Document
    import os
    from django.conf import settings
    
    try:
        user = User.objects.get(id=user_id)
        logger.info(f'Scraping website {website_url} for user {user.email}')
        
        # Validate URL
        parsed_url = urlparse(website_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError('Invalid URL format')
        
        # Fetch website content with timeout
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; GreenMindAI/1.0; +https://greenmind.ai)'
        }
        
        response = requests.get(
            website_url,
            headers=headers,
            timeout=15,
            allow_redirects=True
        )
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()
        
        # Extract text content
        text_content = soup.get_text(separator='\n', strip=True)
        
        # Clean up whitespace
        lines = [line.strip() for line in text_content.splitlines() if line.strip()]
        clean_text = '\n'.join(lines)
        
        # Limit to reasonable size (e.g., 100KB)
        max_size = 100000
        if len(clean_text) > max_size:
            clean_text = clean_text[:max_size] + '\n\n[Content truncated due to size limit]'
        
        # Extract metadata
        title = soup.find('title')
        title_text = title.string if title else parsed_url.netloc
        
        meta_description = soup.find('meta', attrs={'name': 'description'})
        description = meta_description.get('content', '') if meta_description else ''
        
        # Create document content
        document_content = f"""Company Website: {title_text}
URL: {website_url}
Description: {description}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXTRACTED CONTENT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{clean_text}
"""
        
        # Save as document
        # Create new document (allow multiple websites)
        file_name = f"Company Website: {parsed_url.netloc}"
        
        # Save to media directory
        media_dir = os.path.join(settings.MEDIA_ROOT, 'documents', f'user_{user.id}')
        os.makedirs(media_dir, exist_ok=True)
        
        file_path = os.path.join(media_dir, 'company_website.txt')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(document_content)
        
        # Create document record (mark as global)
        document = Document.objects.create(
            user=user,
            file_name=file_name,
            file_path=f'documents/user_{user.id}/company_website.txt',
            file_size=len(document_content.encode('utf-8')),
            is_global=True,  # Company website is a global document
            file_type='text/plain'
        )
        
        logger.info(f'Website scraped and saved as document {document.id} for user {user.email}')
        
        # Start RAG processing in background (chunking + embeddings)
        from accounts.document_rag_tasks import process_document_with_rag
        task = process_document_with_rag.delay(document.id)
        logger.info(f'Started RAG processing task {task.id} for website document {document.id}')
        
        return {
            'success': True,
            'document_id': document.id,
            'url': website_url,
            'content_size': len(clean_text),
            'title': title_text
        }
        
    except requests.Timeout:
        logger.error(f'Timeout scraping website {website_url}')
        raise Exception('Website request timed out. Please try again.')
    
    except requests.RequestException as e:
        logger.error(f'Request error scraping {website_url}: {str(e)}')
        raise Exception(f'Failed to access website: {str(e)}')
    
    except Exception as e:
        logger.error(f'Error scraping website {website_url}: {str(e)}')
        raise
