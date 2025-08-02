#!/usr/bin/env python3
"""
Local testing script for the Readwise Weekly Digest Generator using UV.
This script allows you to test the functionality locally before deploying to Cloud Functions.
"""

import os
import sys
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add src directory to path to import our modules
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(project_root / ".env")
except ImportError:
    print("Warning: python-dotenv not installed. Install with: uv add --dev python-dotenv")
    print("Using environment variables from shell instead.")

from readwise_digest import ReadwiseClient, GitHubClient, MarkdownGenerator, DataProcessor

# Configure logging for local testing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if all required environment variables are set"""
    required_vars = [
        'READWISE_ACCESS_TOKEN',
        'GITHUB_TOKEN',
        'GITHUB_REPO_OWNER',
        'GITHUB_REPO_NAME'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.info("Create a .env file in the project root with:")
        for var in missing_vars:
            logger.info(f"{var}=your_value_here")
        logger.info("\nOr set them in your shell environment.")
        return False
    
    return True

def test_readwise_connection():
    """Test connection to Readwise API"""
    logger.info("Testing Readwise connection...")
    
    readwise_client = ReadwiseClient(os.getenv('READWISE_ACCESS_TOKEN'))
    
    if readwise_client.test_connection():
        logger.info("✅ Readwise connection successful")
        return True
    else:
        logger.error("❌ Readwise connection failed")
        return False

def test_github_connection():
    """Test connection to GitHub API"""
    logger.info("Testing GitHub connection...")
    
    try:
        github_client = GitHubClient(
            token=os.getenv('GITHUB_TOKEN'),
            repo_owner=os.getenv('GITHUB_REPO_OWNER'),
            repo_name=os.getenv('GITHUB_REPO_NAME'),
            target_branch=os.getenv('GITHUB_TARGET_BRANCH', 'main')
        )
        
        if github_client.test_connection():
            logger.info("✅ GitHub connection successful")
            return True
        else:
            logger.error("❌ GitHub connection failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ GitHub connection failed: {str(e)}")
        return False

def test_data_fetching():
    """Test fetching data from Readwise APIs"""
    logger.info("Testing data fetching...")
    
    readwise_client = ReadwiseClient(os.getenv('READWISE_ACCESS_TOKEN'))
    
    # Calculate date range (past 7 days)
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=7)
    
    try:
        # Fetch archived documents
        logger.info("Fetching archived documents...")
        archived_documents = readwise_client.get_archived_documents(start_date)
        logger.info(f"✅ Found {len(archived_documents)} archived documents")
        
        # Fetch highlights
        logger.info("Fetching highlights...")
        highlights = readwise_client.get_recent_highlights(start_date)
        logger.info(f"✅ Found {len(highlights)} highlights")
        
        return archived_documents, highlights, start_date, end_date
        
    except Exception as e:
        logger.error(f"❌ Data fetching failed: {str(e)}")
        return None, None, None, None

def test_data_processing(archived_documents, highlights, start_date, end_date):
    """Test data processing"""
    logger.info("Testing data processing...")
    
    try:
        data_processor = DataProcessor()
        processed_data = data_processor.process_weekly_data(
            archived_documents=archived_documents,
            highlights=highlights,
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info("✅ Data processing successful")
        logger.info(f"  - Documents: {processed_data['documents']['total_count']}")
        logger.info(f"  - Words: {processed_data['documents']['total_word_count']:,}")
        logger.info(f"  - Highlights: {processed_data['highlights']['total_count']}")
        
        return processed_data
        
    except Exception as e:
        logger.error(f"❌ Data processing failed: {str(e)}")
        return None

def test_markdown_generation(processed_data):
    """Test markdown generation"""
    logger.info("Testing markdown generation...")
    
    try:
        markdown_generator = MarkdownGenerator()
        markdown_content = markdown_generator.generate_digest(processed_data)
        
        logger.info("✅ Markdown generation successful")
        logger.info(f"  - Content length: {len(markdown_content)} characters")
        
        # Save to local file for inspection
        output_dir = project_root / "output"
        output_dir.mkdir(exist_ok=True)
        filename = output_dir / f"test_digest_{processed_data['date_range']['start_formatted']}.md"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.info(f"  - Saved test output to: {filename}")
        
        return markdown_content
        
    except Exception as e:
        logger.error(f"❌ Markdown generation failed: {str(e)}")
        return None

def test_github_integration(markdown_content, processed_data, dry_run=True):
    """Test GitHub integration"""
    logger.info(f"Testing GitHub integration (dry_run={dry_run})...")
    
    try:
        github_client = GitHubClient(
            token=os.getenv('GITHUB_TOKEN'),
            repo_owner=os.getenv('GITHUB_REPO_OWNER'),
            repo_name=os.getenv('GITHUB_REPO_NAME'),
            target_branch=os.getenv('GITHUB_TARGET_BRANCH', 'main')
        )
        
        # Create test filename
        filename = f"content/posts/test-{processed_data['date_range']['start_formatted']}-weekly-reading-digest.md"
        
        if dry_run:
            logger.info(f"✅ GitHub integration test passed (dry run)")
            logger.info(f"  - Would create file: {filename}")
            logger.info(f"  - Content length: {len(markdown_content)} characters")
            return True
        else:
            # Actually create the file
            commit_info = github_client.create_or_update_file(
                file_path=filename,
                content=markdown_content,
                commit_message=f"test: Add weekly reading digest test {processed_data['date_range']['start_formatted']}"
            )
            
            logger.info("✅ GitHub integration successful")
            logger.info(f"  - Created file: {filename}")
            logger.info(f"  - Commit SHA: {commit_info['sha']}")
            logger.info(f"  - Commit URL: {commit_info['url']}")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ GitHub integration failed: {str(e)}")
        return False

def run_full_test(dry_run=True):
    """Run the complete test suite"""
    logger.info("=" * 60)
    logger.info("READWISE WEEKLY DIGEST GENERATOR - LOCAL TEST (UV)")
    logger.info("=" * 60)
    
    # Check environment
    if not check_environment():
        return False
    
    # Test connections
    if not test_readwise_connection():
        return False
    
    if not test_github_connection():
        return False
    
    # Test data fetching
    archived_documents, highlights, start_date, end_date = test_data_fetching()
    if archived_documents is None:
        return False
    
    # Test data processing
    processed_data = test_data_processing(archived_documents, highlights, start_date, end_date)
    if processed_data is None:
        return False
    
    # Test markdown generation
    markdown_content = test_markdown_generation(processed_data)
    if markdown_content is None:
        return False
    
    # Test GitHub integration
    if not test_github_integration(markdown_content, processed_data, dry_run=dry_run):
        return False
    
    logger.info("=" * 60)
    logger.info("✅ ALL TESTS PASSED!")
    logger.info("=" * 60)
    
    if dry_run:
        logger.info("This was a dry run. To actually commit to GitHub, run with --commit")
    
    return True

if __name__ == "__main__":
    # Check if user wants to actually commit to GitHub
    dry_run = "--commit" not in sys.argv
    
    if not dry_run:
        logger.warning("Running in COMMIT mode - will actually create files in GitHub!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Aborted by user")
            sys.exit(0)
    
    success = run_full_test(dry_run=dry_run)
    sys.exit(0 if success else 1)