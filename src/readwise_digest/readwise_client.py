import requests
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class ReadwiseAPIError(Exception):
    """Custom exception for Readwise API errors"""
    pass

class ReadwiseClient:
    """Client for interacting with Readwise Reader and main APIs"""
    
    READER_BASE_URL = "https://readwise.io/api/v3/"
    MAIN_BASE_URL = "https://readwise.io/api/v2/"
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Token {access_token}',
            'Content-Type': 'application/json'
        })
    
    def _make_request(self, method: str, url: str, params: Dict = None, data: Dict = None) -> Dict[str, Any]:
        """Make HTTP request with retry logic and rate limiting"""
        max_retries = 3
        base_delay = 1
        
        for attempt in range(max_retries):
            try:
                response = self.session.request(method, url, params=params, json=data)
                
                if response.status_code == 429:  # Rate limited
                    retry_after = int(response.headers.get('Retry-After', base_delay * (2 ** attempt)))
                    logger.warning(f"Rate limited. Waiting {retry_after} seconds before retry {attempt + 1}/{max_retries}")
                    time.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise ReadwiseAPIError(f"Request failed after {max_retries} attempts: {str(e)}")
                logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                time.sleep(base_delay * (2 ** attempt))
        
        raise ReadwiseAPIError("Max retries exceeded")
    
    def get_archived_documents(self, start_date: datetime) -> List[Dict[str, Any]]:
        """
        Fetch documents that were archived in the past week from Reader API.
        Uses the last_moved_at field to determine when items were moved to archive.
        """
        logger.info("Fetching archived documents from Readwise Reader API")
        
        all_documents = []
        page_cursor = None
        start_date_iso = start_date.isoformat().replace('+00:00', 'Z')
        
        while True:
            params = {
                'location': 'archive',
                'updatedAfter': start_date_iso
            }
            
            if page_cursor:
                params['pageCursor'] = page_cursor
            
            url = urljoin(self.READER_BASE_URL, 'list/')
            response_data = self._make_request('GET', url, params=params)
            
            documents = response_data.get('results', [])
            
            # Filter documents that were actually moved to archive within our date range
            # Check both last_moved_at and updated_at to catch items moved to archive
            filtered_documents = []
            for doc in documents:
                last_moved_str = doc.get('last_moved_at')
                updated_str = doc.get('updated_at')
                
                if last_moved_str:
                    last_moved = datetime.fromisoformat(last_moved_str.replace('Z', '+00:00'))
                    if last_moved >= start_date and doc.get('location') == 'archive':
                        filtered_documents.append(doc)
                elif updated_str:
                    updated = datetime.fromisoformat(updated_str.replace('Z', '+00:00'))
                    if updated >= start_date and doc.get('location') == 'archive':
                        filtered_documents.append(doc)
            
            all_documents.extend(filtered_documents)
            
            page_cursor = response_data.get('nextPageCursor')
            if not page_cursor:
                break
                
            logger.info(f"Fetched {len(filtered_documents)} archived documents from this page, continuing...")
        
        logger.info(f"Total archived documents fetched: {len(all_documents)}")
        return all_documents
    
    def get_recent_highlights(self, start_date: datetime) -> List[Dict[str, Any]]:
        """Fetch highlights created in the past week from main Readwise API"""
        logger.info("Fetching recent highlights from Readwise main API")
        
        all_highlights = []
        page = 1
        start_date_iso = start_date.isoformat().replace('+00:00', 'Z')
        
        while True:
            params = {
                'highlighted_at__gt': start_date_iso,
                'page_size': 1000,  # Max allowed
                'page': page
            }
            
            url = urljoin(self.MAIN_BASE_URL, 'highlights/')
            response_data = self._make_request('GET', url, params=params)
            
            highlights = response_data.get('results', [])
            if not highlights:
                break
            
            all_highlights.extend(highlights)
            
            # Check if there's a next page
            if not response_data.get('next'):
                break
                
            page += 1
            logger.info(f"Fetched {len(highlights)} highlights from page {page-1}, continuing...")
        
        logger.info(f"Total highlights fetched: {len(all_highlights)}")
        return all_highlights
    
    def test_connection(self) -> bool:
        """Test if the API connection is working"""
        try:
            url = urljoin(self.MAIN_BASE_URL, 'auth/')
            response = self.session.get(url)
            return response.status_code == 204
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False