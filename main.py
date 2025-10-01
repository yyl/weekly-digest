import functions_framework
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os
import base64
from flask import Request

from readwise_client import ReadwiseClient
from github_client import GitHubClient
from markdown_generator import MarkdownGenerator
from data_processor import DataProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_digest_generation():
    """Core digest generation logic that can be called from any trigger type"""
    logger.info("Starting weekly digest generation")
    
    # Validate environment variables
    required_env_vars = [
        'READWISE_ACCESS_TOKEN',
        'GITHUB_TOKEN',
        'GITHUB_REPO_OWNER',
        'GITHUB_REPO_NAME'
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    # Initialize clients
    readwise_client = ReadwiseClient(os.getenv('READWISE_ACCESS_TOKEN'))
    github_client = GitHubClient(
        token=os.getenv('GITHUB_TOKEN'),
        repo_owner=os.getenv('GITHUB_REPO_OWNER'),
        repo_name=os.getenv('GITHUB_REPO_NAME'),
        target_branch=os.getenv('GITHUB_TARGET_BRANCH', 'main')
    )
    
    # Calculate date range (past 7 days)
    from datetime import timezone
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=7)
    
    logger.info(f"Fetching data for date range: {start_date.isoformat()} to {end_date.isoformat()}")
    
    # Fetch data from Readwise
    logger.info("Fetching archived documents from Readwise Reader API")
    archived_documents = readwise_client.get_archived_documents(start_date)
    
    logger.info("Fetching highlights from Readwise API")
    highlights = readwise_client.get_recent_highlights(start_date)
    
    logger.info(f"Found {len(archived_documents)} archived documents and {len(highlights)} highlights")
    
    # Process the data
    data_processor = DataProcessor()
    processed_data = data_processor.process_weekly_data(
        archived_documents=archived_documents,
        highlights=highlights,
        start_date=start_date,
        end_date=end_date
    )
    
    # Generate markdown content
    markdown_generator = MarkdownGenerator()
    markdown_content = markdown_generator.generate_digest(processed_data)
    
    # Create filename with date
    filename = f"content/posts/{start_date.strftime('%Y-%m-%d')}-weekly-reading-digest.md"
    
    # Commit to GitHub
    logger.info(f"Committing digest to GitHub: {filename}")
    github_client.create_or_update_file(
        file_path=filename,
        content=markdown_content,
        commit_message=f"feat: Add weekly reading digest draft {start_date.strftime('%Y-%m-%d')}"
    )
    
    logger.info("Weekly digest generation completed successfully")
    return {"status": "success", "message": "Weekly digest generated and committed to GitHub"}

@functions_framework.cloud_event
def weekly_digest_generator(cloud_event):
    """
    Cloud Function entry point for Pub/Sub trigger (production).
    Triggered by Cloud Scheduler via Pub/Sub.
    """
    try:
        logger.info("Triggered by Pub/Sub CloudEvent")
        return run_digest_generation()
    except Exception as e:
        logger.error(f"Error generating weekly digest: {str(e)}", exc_info=True)
        raise

@functions_framework.http
def weekly_digest_http(request: Request):
    """
    HTTP entry point for manual testing.
    Can be invoked directly via curl or gcloud functions call.
    """
    try:
        logger.info("Triggered by HTTP request")
        result = run_digest_generation()
        return result, 200
    except Exception as e:
        logger.error(f"Error generating weekly digest: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}, 500

# For local testing
if __name__ == "__main__":
    # Mock cloud event for local testing
    class MockCloudEvent:
        pass
    
    weekly_digest_generator(MockCloudEvent())