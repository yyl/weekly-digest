import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
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
        # markdown_parts.append(f"# Weekly Reading Digest - {date_range['start_formatted']} to {date_range['end_formatted']}")
        # markdown_parts.append("")
        
        # Add overview section
        markdown_parts.append(self._generate_overview(documents, highlights))
        
        # Add document breakdowns
        if documents['total_count'] > 0:
            markdown_parts.append(self._generate_document_breakdowns(documents))
        
        # Add highlights section
        if highlights['total_count'] > 0:
            markdown_parts.append(self._generate_highlights_section(highlights))
        
        # Add footer
        # markdown_parts.append(self._generate_footer(generation_time))
        
        final_markdown = "\n".join(markdown_parts)
        logger.info("Markdown content generation completed")
        
        return final_markdown
    
    def _generate_front_matter(self, date_range: Dict, generation_time: datetime) -> str:
        """Generate YAML front matter for the markdown file"""
        title = f"Weekly Reading Digest - {date_range['start_formatted']} to {date_range['end_formatted']}"
        
        pdt = ZoneInfo("America/Los_Angeles")
        pdt_time = generation_time.astimezone(pdt)
        date_iso = pdt_time.isoformat(timespec='seconds')
        
        front_matter = f"""---
title: "{title}"
date: {date_iso}
draft: true
tags: ["reading", "digest", "readwise", "automated"]
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

        if documents.get('average_time_to_archive', 0) > 0:
            avg_time = int(documents['average_time_to_archive'])
            overview_parts.insert(-1, f"- **Average Time Before Archive**: {avg_time} hours")
        
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
        
        # Source breakdown
        if documents['source_breakdown']:
            breakdown_parts.extend([
                "### By Source",
                ""
            ])
            for source, count in documents['source_breakdown'].items():
                if source:
                    source_display = source.replace('_', ' ').title()
                else:
                    source_display = 'Unknown'
                breakdown_parts.append(f"- **{source_display}**: {count}")
            breakdown_parts.append("")
        
        # Tag breakdown
        if documents.get('tag_breakdown'):
            breakdown_parts.extend([
                "### By Tag",
                ""
            ])
            for tag, count in documents['tag_breakdown'].items():
                breakdown_parts.append(f"- **{tag}**: {count}")
            breakdown_parts.append("")

        # List of archived articles
        if documents['documents']:
            breakdown_parts.extend([
                "### Archived Articles",
                ""
            ])

            # Sort documents by last_moved_at time, most recent first
            # The 'last_moved_at' is an ISO string, so we parse it for sorting.
            # Fallback to a very old date if 'last_moved_at' is missing.
            sorted_documents = sorted(
                documents['documents'],
                key=lambda d: datetime.fromisoformat(d['last_moved_at'].replace('Z', '+00:00')) if d.get('last_moved_at') else datetime.min.replace(tzinfo=timezone.utc),
                reverse=True
            )
            
            for doc in sorted_documents:
                title = doc['title']
                author = doc['author']
                word_count = doc['word_count']
                
                # Create article entry
                article_line = f"- **{title}**"
                
                if author:
                    article_line += f" by {author}"
                
                if word_count > 0:
                    article_line += f" ({word_count:,} words)"

                if doc.get('time_to_archive') is not None:
                    time_to_archive = doc['time_to_archive']
                    article_line += f" (archived after {time_to_archive:.2f} hours)"
                
                breakdown_parts.append(article_line)
            
            breakdown_parts.append("")
        
        return "\n".join(breakdown_parts)
    
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