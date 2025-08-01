"""
Readwise Weekly Digest Generator

An automated system that generates weekly reading digests from Readwise
and commits them as draft blog posts to GitHub repositories.
"""

__version__ = "1.0.0"
__author__ = "Your Name"

from .readwise_client import ReadwiseClient
from .github_client import GitHubClient
from .data_processor import DataProcessor
from .markdown_generator import MarkdownGenerator

__all__ = [
    "ReadwiseClient",
    "GitHubClient", 
    "DataProcessor",
    "MarkdownGenerator",
]