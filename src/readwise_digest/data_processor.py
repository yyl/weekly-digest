import logging
from collections import defaultdict, Counter
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class DataProcessor:
    """Processes raw Readwise data into structured format for digest generation"""
    
    def process_weekly_data(self, archived_documents: List[Dict], highlights: List[Dict], 
                           start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Process weekly reading data from Readwise APIs.
        
        Args:
            archived_documents: List of documents archived in the past week
            highlights: List of highlights created in the past week
            start_date: Start of the week
            end_date: End of the week
            
        Returns:
            Processed data dictionary ready for markdown generation
        """
        logger.info("Processing weekly reading data")
        
        # Process archived documents
        document_stats = self._process_archived_documents(archived_documents)
        
        # Process highlights
        highlight_data = self._process_highlights(highlights)
        
        # Create the processed data structure
        processed_data = {
            'date_range': {
                'start': start_date,
                'end': end_date,
                'start_formatted': start_date.strftime('%Y-%m-%d'),
                'end_formatted': end_date.strftime('%Y-%m-%d')
            },
            'documents': document_stats,
            'highlights': highlight_data,
            'generation_timestamp': datetime.utcnow()
        }
        
        logger.info(f"Processed {document_stats['total_count']} documents and {len(highlight_data['highlights'])} highlights")
        return processed_data
    
    def _process_archived_documents(self, documents: List[Dict]) -> Dict[str, Any]:
        """Process archived documents to extract statistics"""
        if not documents:
            return {
                'total_count': 0,
                'total_word_count': 0,
                'category_breakdown': {},
                'source_breakdown': {},
                'location_breakdown': {},
                'documents': []
            }
        
        total_count = len(documents)
        total_word_count = 0
        category_counts = Counter()
        source_counts = Counter()
        location_counts = Counter()
        
        processed_documents = []
        
        for doc in documents:
            # Count words (handle missing word_count)
            word_count = doc.get('word_count', 0) or 0
            total_word_count += word_count
            
            # Count categories, sources, and locations
            category = doc.get('category', 'unknown')
            source = doc.get('source', 'unknown')
            location = doc.get('location', 'unknown')
            
            category_counts[category] += 1
            source_counts[source] += 1
            location_counts[location] += 1
            
            # Store processed document info
            processed_doc = {
                'title': doc.get('title', 'Untitled'),
                'author': doc.get('author', ''),
                'source': source,
                'category': category,
                'location': location,
                'word_count': word_count,
                'source_url': doc.get('source_url', ''),
                'site_name': doc.get('site_name', ''),
                'published_date': doc.get('published_date', ''),
                'summary': doc.get('summary', ''),
                'last_moved_at': doc.get('last_moved_at', ''),
                'updated_at': doc.get('updated_at', '')
            }
            processed_documents.append(processed_doc)
        
        return {
            'total_count': total_count,
            'total_word_count': total_word_count,
            'category_breakdown': dict(category_counts.most_common()),
            'source_breakdown': dict(source_counts.most_common()),
            'location_breakdown': dict(location_counts.most_common()),
            'documents': processed_documents
        }
    
    def _process_highlights(self, highlights: List[Dict]) -> Dict[str, Any]:
        """Process highlights to extract relevant information"""
        if not highlights:
            return {
                'total_count': 0,
                'highlights': [],
                'source_breakdown': {}
            }
        
        processed_highlights = []
        source_counts = Counter()
        
        for highlight in highlights:
            # Extract highlight text and metadata
            text = highlight.get('text', '').strip()
            if not text:
                continue
            
            # Get book/source information
            book_id = highlight.get('book_id')
            note = highlight.get('note', '').strip()
            location = highlight.get('location', '')
            highlighted_at = highlight.get('highlighted_at', '')
            
            # For source tracking, we'll need to make additional API calls
            # or use available fields. For now, we'll use what's available.
            source = 'unknown'  # We could enhance this by fetching book details
            
            processed_highlight = {
                'text': text,
                'note': note,
                'location': location,
                'highlighted_at': highlighted_at,
                'book_id': book_id,
                'source': source,
                'readwise_url': highlight.get('readwise_url', '')
            }
            
            processed_highlights.append(processed_highlight)
            source_counts[source] += 1
        
        return {
            'total_count': len(processed_highlights),
            'highlights': processed_highlights,
            'source_breakdown': dict(source_counts.most_common())
        }
    
    def _safe_get_value(self, data: Dict, key: str, default: Any = None) -> Any:
        """Safely get value from dictionary with fallback"""
        value = data.get(key, default)
        return value if value is not None else default