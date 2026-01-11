from celery import shared_task
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, urlunparse
from collections import deque
import time

logger = logging.getLogger(__name__)


def normalize_url(url: str) -> str:
    """Normalize URL by removing fragments and trailing slashes"""
    parsed = urlparse(url)
    # Remove fragment and query (optional - keep query if needed)
    normalized = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path.rstrip('/'),
        '',  # params
        parsed.query,  # keep query for dynamic pages
        ''   # remove fragment
    ))
    return normalized


def is_same_domain(url1: str, url2: str) -> bool:
    """Check if two URLs belong to the same domain"""
    domain1 = urlparse(url1).netloc
    domain2 = urlparse(url2).netloc
    # Handle www. prefix
    domain1 = domain1.replace('www.', '')
    domain2 = domain2.replace('www.', '')
    return domain1 == domain2


def extract_links(soup: BeautifulSoup, base_url: str) -> set:
    """Extract all internal links from a page"""
    links = set()
    for anchor in soup.find_all('a', href=True):
        href = anchor['href']
        # Convert relative URLs to absolute
        absolute_url = urljoin(base_url, href)
        
        # Only include same-domain links
        if is_same_domain(base_url, absolute_url):
            normalized = normalize_url(absolute_url)
            # Filter out common non-content URLs
            if not any(ext in normalized.lower() for ext in [
                '.pdf', '.jpg', '.png', '.gif', '.zip', '.exe', 
                '.doc', '.docx', '.xls', '.xlsx', '.mp4', '.mp3',
                'javascript:', 'mailto:', 'tel:'
            ]):
                links.add(normalized)
    
    return links


def scrape_page(url: str, headers: dict) -> tuple:
    """Scrape a single page and return (text_content, links, title)"""
    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=10,
            allow_redirects=True
        )
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = soup.find('title')
        page_title = title.string.strip() if title and title.string else url
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'iframe', 'noscript']):
            element.decompose()
        
        # Extract text
        text_content = soup.get_text(separator='\n', strip=True)
        lines = [line.strip() for line in text_content.splitlines() if line.strip()]
        clean_text = '\n'.join(lines)
        
        # Extract links
        links = extract_links(soup, url)
        
        return clean_text, links, page_title
        
    except Exception as e:
        logger.warning(f'Failed to scrape {url}: {str(e)}')
        return '', set(), url


@shared_task(bind=True)
def scrape_company_website_task(self, user_id: int, website_url: str, max_pages: int = 50, max_depth: int = 3):
    """Celery task to crawl and scrape entire company website (multiple pages)"""
    from accounts.models import User, Document
    import os
    from django.conf import settings
    
    try:
        user = User.objects.get(id=user_id)
        
        # Clean and validate URL
        website_url = website_url.strip()  # Remove leading/trailing whitespace
        if not website_url.startswith(('http://', 'https://')):
            website_url = 'https://' + website_url
        
        logger.info(f'Starting web crawl of {website_url} for user {user.email} (max_pages={max_pages}, max_depth={max_depth})')
        
        # Validate URL
        parsed_url = urlparse(website_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError('Invalid URL format')
        
        # Normalize starting URL
        start_url = normalize_url(website_url)
        
        # Setup crawling
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; GreenMindAI/1.0; +https://greenmind.ai)'
        }
        
        visited = set()
        to_visit = deque([(start_url, 0)])  # (url, depth)
        all_content = []
        page_count = 0
        
        # BFS crawl
        while to_visit and page_count < max_pages:
            current_url, depth = to_visit.popleft()
            
            # Skip if already visited or too deep
            if current_url in visited or depth > max_depth:
                continue
            
            visited.add(current_url)
            page_count += 1
            
            logger.info(f'Crawling page {page_count}/{max_pages}: {current_url} (depth={depth})')
            
            # Scrape page
            text_content, links, page_title = scrape_page(current_url, headers)
            
            if text_content:
                all_content.append(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PAGE: {page_title}
URL: {current_url}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{text_content}
""")
            
            # Add new links to queue (only if not at max depth)
            if depth < max_depth:
                for link in links:
                    if link not in visited:
                        to_visit.append((link, depth + 1))
            
            # Be polite - small delay between requests
            time.sleep(0.5)
            
            # Update task progress
            progress = min(100, int((page_count / max_pages) * 100))
            self.update_state(state='PROGRESS', meta={'current': page_count, 'total': max_pages, 'progress': progress})
        
        # Combine all content
        combined_content = '\n\n'.join(all_content)
        
        # Limit total size
        max_size = 500000  # 500KB - enough for comprehensive website content
        if len(combined_content) > max_size:
            combined_content = combined_content[:max_size] + '\n\n[Content truncated due to size limit]'
        
        # Extract site metadata from root page
        root_soup = BeautifulSoup(requests.get(start_url, headers=headers, timeout=10).content, 'html.parser')
        site_title = root_soup.find('title')
        site_title_text = site_title.string if site_title else parsed_url.netloc
        
        meta_description = root_soup.find('meta', attrs={'name': 'description'})
        description = meta_description.get('content', '') if meta_description else ''
        
        # Create final document
        document_content = f"""Company Website: {site_title_text}
Domain: {parsed_url.netloc}
Root URL: {start_url}
Description: {description}
Pages Crawled: {page_count}
Total Content Size: {len(combined_content)} characters

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WEBSITE CONTENT (All Pages):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{combined_content}
"""
        
        # Save to media directory
        media_dir = os.path.join(settings.MEDIA_ROOT, 'documents', f'user_{user.id}')
        os.makedirs(media_dir, exist_ok=True)
        
        # Use timestamp for unique filename
        timestamp = int(time.time())
        file_name = f"Company Website: {parsed_url.netloc}"
        file_path_relative = f'documents/user_{user.id}/website_{parsed_url.netloc}_{timestamp}.txt'
        file_path_full = os.path.join(settings.MEDIA_ROOT, file_path_relative)
        
        with open(file_path_full, 'w', encoding='utf-8') as f:
            f.write(document_content)
        
        # Create document record (mark as global)
        document = Document.objects.create(
            user=user,
            file_name=file_name,
            file_path=file_path_relative,
            file_size=len(document_content.encode('utf-8')),
            is_global=True,  # Company website is a global document
            file_type='text/plain'
        )
        
        logger.info(f'Website crawled: {page_count} pages scraped, saved as document {document.id} for user {user.email}')
        
        # Start RAG processing in background (chunking + embeddings)
        from accounts.document_rag_tasks import process_document_with_rag
        task = process_document_with_rag.delay(document.id)
        logger.info(f'Started RAG processing task {task.id} for website document {document.id}')
        
        return {
            'success': True,
            'document_id': document.id,
            'url': website_url,
            'pages_crawled': page_count,
            'content_size': len(combined_content),
            'title': site_title_text
        }
        
    except requests.Timeout:
        logger.error(f'Timeout crawling website {website_url}')
        raise Exception('Website request timed out. Please try again.')
    
    except requests.RequestException as e:
        logger.error(f'Request error crawling {website_url}: {str(e)}')
        raise Exception(f'Failed to access website: {str(e)}')
    
    except Exception as e:
        logger.error(f'Error crawling website {website_url}: {str(e)}')
        raise
