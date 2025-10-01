import logging
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class MarkdownGenerator:
    """Generates markdown content for the weekly reading digest"""
    
    def generate_digest(self, processed_data: Dict[str, Any]) -> str:
        """
        Generate complete markdown content for the weekly digest.
        
        Args:
            processed_data: Processed weekly reading data
            
        Returns:
            Complete markdown content as string
        """
        logger.info("Generating markdown content for weekly digest")
        
        # Extract data components
        date_range = processed_data['date_range']
        documents = processed_data['documents']
        highlights = processed_data['highlights']
        generation_time = processed_data['generation_timestamp']
        
        # Build markdown content
        markdown_parts = []
        
        # Add YAML front matter
        markdown_parts.append(self._generate_front_matter(date_range, generation_time))
        
        # Add main heading
        markdown_parts.append(f"# Weekly Reading Digest - {date_range['start_formatted']} to {date_range['end_formatted']}")
        markdown_parts.append("")
        
        # Add overview section
        markdown_parts.append(self._generate_overview(documents, highlights))
        
        # Add document breakdowns
        if documents['total_count'] > 0:
            markdown_parts.append(self._generate_document_breakdowns(documents))
        
        # Add highlights section
        if highlights['total_count'] > 0:
            markdown_parts.append(self._generate_highlights_section(highlights))
        
        # Add footer
        markdown_parts.append(self._generate_footer(generation_time))
        
        final_markdown = "\n".join(markdown_parts)
        logger.info("Markdown content generation completed")
        
        return final_markdown
    
    def _generate_front_matter(self, date_range: Dict, generation_time: datetime) -> str:
        """Generate YAML front matter for the markdown file"""
        title = f"Weekly Reading Digest - {date_range['start_formatted']} to {date_range['end_formatted']}"
        date_iso = generation_time.isoformat() + "Z"
        
        front_matter = f"""---
title: "{title}"
date: {date_iso}
draft: false
tags: ["reading", "digest", "readwise"]
categories: ["Reading"]
---"""
        
        return front_matter
    
    def _generate_overview(self, documents: Dict, highlights: Dict) -> str:
        """Generate overview section with key statistics"""
        overview_parts = [
            "## Overview",
            "",
            f"- **Articles Archived**: {documents['total_count']}",
            f"- **Total Words Read**: {documents['total_word_count']:,}",
            f"- **Highlights Created**: {highlights['total_count']}",
            ""
        ]
        
        # Add average words if we have documents
        if documents['total_count'] > 0:
            avg_words = documents['total_word_count'] // documents['total_count']
            overview_parts.insert(-1, f"- **Average Words per Article**: {avg_words:,}")
        
        return "\n".join(overview_parts)
    
    def _generate_document_breakdowns(self, documents: Dict) -> str:
        """Generate breakdown sections for documents"""
        breakdown_parts = [
            "## Article Breakdowns",
            ""
        ]
        
        # Category breakdown
        if documents['category_breakdown']:
            breakdown_parts.extend([
                "### By Category",
                ""
            ])
            for category, count in documents['category_breakdown'].items():
                breakdown_parts.append(f"- **{category.title()}**: {count}")
            breakdown_parts.append("")
        
        # Source breakdown with proper capitalization
        if documents['source_breakdown']:
            breakdown_parts.extend([
                "### By Source",
                ""
            ])
            for source, count in documents['source_breakdown'].items():
                source_display = self._format_source_name(source)
                breakdown_parts.append(f"- **{source_display}**: {count}")
            breakdown_parts.append("")
        
        # Location breakdown (should mostly be 'archive' but good for completeness)
        if documents['location_breakdown']:
            breakdown_parts.extend([
                "### By Location",
                ""
            ])
            for location, count in documents['location_breakdown'].items():
                breakdown_parts.append(f"- **{location.title()}**: {count}")
            breakdown_parts.append("")
        
        # List of archived articles
        if documents['documents']:
            breakdown_parts.extend([
                "### Archived Articles",
                ""
            ])
            
            for doc in documents['documents']:
                title = doc['title']
                author = doc['author']
                word_count = doc['word_count']
                source_url = doc['source_url']
                
                # Create article entry
                if source_url:
                    article_line = f"- **[{title}]({source_url})**"
                else:
                    article_line = f"- **{title}**"
                
                if author:
                    article_line += f" by {author}"
                
                if word_count > 0:
                    article_line += f" ({word_count:,} words)"
                
                breakdown_parts.append(article_line)
                
                # Add summary if available
                if doc['summary']:
                    breakdown_parts.append(f"  - {doc['summary']}")
            
            breakdown_parts.append("")
        
        return "\n".join(breakdown_parts)
    
    def _format_source_name(self, source: str) -> str:
        """Format source name with proper capitalization"""
        # Special cases for common sources
        special_cases = {
            'ios': 'iOS',
            'macos': 'macOS',
            'rss': 'RSS',
            'api': 'API',
            'url': 'URL',
            'pdf': 'PDF',
            'epub': 'EPUB',
            'html': 'HTML',
        }
        
        # Check if the entire source is a special case
        if source.lower() in special_cases:
            return special_cases[source.lower()]
        
        # Handle compound names like "reader_ios" or "import_url"
        parts = source.replace('_', ' ').replace('-', ' ').split()
        formatted_parts = []
        
        for part in parts:
            if part.lower() in special_cases:
                formatted_parts.append(special_cases[part.lower()])
            else:
                formatted_parts.append(part.title())
        
        return ' '.join(formatted_parts)
    
    def _generate_highlights_section(self, highlights: Dict) -> str:
        """Generate highlights section"""
        highlights_parts = [
            "## Highlights from the Past Week",
            ""
        ]
        
        if not highlights['highlights']:
            highlights_parts.extend([
                "No highlights were created this week.",
                ""
            ])
            return "\n".join(highlights_parts)
        
        # Group highlights by source if we have that information
        # For now, we'll just list them chronologically
        for i, highlight in enumerate(highlights['highlights'], 1):
            text = highlight['text']
            note = highlight['note']
            
            # Add the highlight text
            highlights_parts.append(f"{i}. \"{text}\"")
            
            # Add note if present
            if note:
                highlights_parts.append(f"   - *Note: {note}*")
            
            highlights_parts.append("")
        
        return "\n".join(highlights_parts)
    
    def _generate_footer(self, generation_time: datetime) -> str:
        """Generate footer with generation timestamp"""
        footer_parts = [
            "---",
            "",
            f"*Generated on {generation_time.strftime('%Y-%m-%d at %H:%M UTC')} using Readwise API*"
        ]
        
        return "\n".join(footer_parts)