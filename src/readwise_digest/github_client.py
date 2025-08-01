import base64
import logging
from typing import Optional, Dict, Any
from github import Github, GithubException

logger = logging.getLogger(__name__)

class GitHubClientError(Exception):
    """Custom exception for GitHub client errors"""
    pass

class GitHubClient:
    """Client for interacting with GitHub API"""
    
    def __init__(self, token: str, repo_owner: str, repo_name: str, target_branch: str = 'main'):
        self.token = token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.target_branch = target_branch
        
        # Initialize PyGithub client
        self.github = Github(token)
        
        try:
            self.repo = self.github.get_repo(f"{repo_owner}/{repo_name}")
            logger.info(f"Successfully connected to repository: {repo_owner}/{repo_name}")
        except GithubException as e:
            raise GitHubClientError(f"Failed to access repository {repo_owner}/{repo_name}: {str(e)}")
    
    def create_or_update_file(self, file_path: str, content: str, commit_message: str) -> Dict[str, Any]:
        """
        Create a new file or update an existing file in the repository.
        
        Args:
            file_path: Path to the file in the repository
            content: File content as string
            commit_message: Commit message
            
        Returns:
            Dictionary with commit information
        """
        try:
            # Check if file already exists
            file_exists = False
            existing_file = None
            
            try:
                existing_file = self.repo.get_contents(file_path, ref=self.target_branch)
                file_exists = True
                logger.info(f"File {file_path} already exists, will update")
            except GithubException as e:
                if e.status == 404:
                    logger.info(f"File {file_path} does not exist, will create")
                else:
                    raise GitHubClientError(f"Error checking file existence: {str(e)}")
            
            # Create or update the file
            if file_exists:
                # Update existing file
                result = self.repo.update_file(
                    path=file_path,
                    message=commit_message,
                    content=content,
                    sha=existing_file.sha,
                    branch=self.target_branch
                )
                logger.info(f"Successfully updated file: {file_path}")
            else:
                # Create new file
                result = self.repo.create_file(
                    path=file_path,
                    message=commit_message,
                    content=content,
                    branch=self.target_branch
                )
                logger.info(f"Successfully created file: {file_path}")
            
            # Extract commit information
            commit_info = {
                'sha': result['commit'].sha,
                'url': result['commit'].html_url,
                'message': commit_message,
                'file_path': file_path
            }
            
            return commit_info
            
        except GithubException as e:
            error_msg = f"GitHub API error while creating/updating file {file_path}: {str(e)}"
            logger.error(error_msg)
            raise GitHubClientError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error while creating/updating file {file_path}: {str(e)}"
            logger.error(error_msg)
            raise GitHubClientError(error_msg)
    
    def file_exists(self, file_path: str) -> bool:
        """Check if a file exists in the repository"""
        try:
            self.repo.get_contents(file_path, ref=self.target_branch)
            return True
        except GithubException as e:
            if e.status == 404:
                return False
            raise GitHubClientError(f"Error checking file existence: {str(e)}")
    
    def get_file_content(self, file_path: str) -> Optional[str]:
        """Get file content from the repository"""
        try:
            file_content = self.repo.get_contents(file_path, ref=self.target_branch)
            return file_content.decoded_content.decode('utf-8')
        except GithubException as e:
            if e.status == 404:
                return None
            raise GitHubClientError(f"Error getting file content: {str(e)}")
    
    def test_connection(self) -> bool:
        """Test if the GitHub connection is working"""
        try:
            # Try to get repository information
            repo_star_count = self.repo.stargazers_count
            logger.info(f"Successfully connected to GitHub repository: {repo_star_count}")
            return True
        except Exception as e:
            logger.error(f"GitHub connection test failed: {str(e)}")
            return False