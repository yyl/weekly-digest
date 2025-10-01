# Readwise Weekly Digest Generator

Automated system that generates weekly reading digests from your Readwise account and publishes them to your blog via GitHub.

## Overview

This serverless application runs weekly on Google Cloud Functions, fetching your archived articles and highlights from Readwise, processing the data into a formatted markdown digest, and committing it to your GitHub blog repository for automatic publication.

## Code Structure

### Core Files

- **`main.py`** - Cloud Function entry points. Contains `weekly_digest_generator()` for Pub/Sub triggers and `run_digest_generation()` with the core orchestration logic.

- **`readwise_client.py`** - Readwise API client handling authentication, rate limiting, and pagination for both Reader API (archived documents) and main API (highlights).

- **`github_client.py`** - GitHub API client using PyGithub to create/update files in your repository with proper authentication and error handling.

- **`data_processor.py`** - Processes raw API responses into structured data: counts articles, calculates word counts, aggregates by category/source, and extracts highlight texts.

- **`markdown_generator.py`** - Generates formatted markdown content with YAML front matter, statistics sections, and highlight lists ready for static site generators.

### Configuration Files

- **`pyproject.toml`** - UV project configuration defining dependencies, tool settings (black, ruff), and project metadata.

- **`scripts/deploy.sh`** - Deployment automation script that sets up IAM permissions, deploys the Cloud Function, and configures Cloud Scheduler.

- **`scripts/test_local.py`** - Local testing script to verify the complete pipeline before deploying to the cloud.

## Cloud Architecture

```
Cloud Scheduler (cron: weekly)
    ↓ publishes message
Pub/Sub Topic
    ↓ triggers via Eventarc
Cloud Function (Python 3.11, 256MB, Gen 2)
    ↓ fetches data
Readwise APIs (Reader + Main)
    ↓ returns documents & highlights
Data Processing → Markdown Generation
    ↓ commits file
GitHub API
    ↓ pushes to repository
Your Blog Repository
    ↓ webhook triggers
Cloudflare Pages (auto-builds & deploys)
```

**Execution flow:** Every Monday at midnight UTC, Cloud Scheduler publishes a message to a Pub/Sub topic. This triggers the Cloud Function via Eventarc, which creates a push subscription automatically. The function fetches the past week's archived documents and highlights from Readwise, processes the data into statistics and lists, generates a markdown file with proper front matter, and commits it to your GitHub repository. Cloudflare Pages detects the commit and rebuilds your site, publishing the new digest.

**Key components:**
- Cloud Function runs stateless, scales to zero when idle (no cost)
- Pub/Sub provides reliable message delivery with automatic retries
- Eventarc manages the connection between Pub/Sub and Cloud Function
- Environment variables store API tokens securely (encrypted at rest)
- IAM permissions control access between services

## Common Workflows

### 1. Initial Setup
```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Set up project
./setup.sh

# Configure environment variables
cp .env.template .env
# Edit .env with your API tokens

# Test locally
uv run python scripts/test_local.py
```

### 2. Deploy to Google Cloud
```bash
export READWISE_ACCESS_TOKEN="your_token"
export GITHUB_TOKEN="your_github_token"
export GITHUB_REPO_OWNER="your_username"
export GITHUB_REPO_NAME="your_repo"

./scripts/deploy.sh your-project-id us-central1
```

### 3. Manual Trigger for Testing
```bash
# Trigger via Pub/Sub
gcloud pubsub topics publish weekly-digest-trigger \
  --message='{"test":true}' \
  --project=your-project-id

# Or trigger via Scheduler
gcloud scheduler jobs run weekly-digest-schedule \
  --location=us-central1 \
  --project=your-project-id
```

### 4. View Logs and Debug
```bash
# View function logs
gcloud functions logs read weekly-digest-generator \
  --region=us-central1 \
  --project=your-project-id \
  --limit=50

# Check function status
gcloud functions describe weekly-digest-generator \
  --region=us-central1 \
  --gen2
```

### 5. Update Configuration
```bash
# Update environment variables
gcloud functions deploy weekly-digest-generator \
  --update-env-vars GITHUB_REPO_NAME=new-repo \
  --region=us-central1 \
  --project=your-project-id

# Change schedule (edit deploy.sh SCHEDULE variable, then redeploy)
# Example: SCHEDULE="0 8 * * 1"  # Monday at 8 AM UTC
```

## Requirements

- Python 3.11+
- UV package manager
- Google Cloud Project with billing enabled
- Readwise account with API access
- GitHub repository for your blog
- API tokens: Readwise access token, GitHub personal access token (repo scope)

## Cost

Typical monthly cost: $0-$0.10
- Cloud Function: ~$0.001 (4 invocations/month, 30s each)
- Cloud Scheduler: First 3 jobs free
- Pub/Sub: First 10GB free
- Cloud Logging: First 50GB free

## Generated Content

Each weekly digest includes:
- Article count, total words read, highlight count
- Breakdown by category (articles, books, etc.)
- Breakdown by source (iOS, RSS, import, etc.)
- List of archived articles with titles, authors, word counts, summaries
- All highlights created during the week with optional notes
- YAML front matter ready for Hugo, Jekyll, or other static site generators

## Troubleshooting

**Function not triggering:** Check Pub/Sub subscription exists with `gcloud pubsub topics list-subscriptions weekly-digest-trigger`. If missing, redeploy the function.

**Permission errors:** Ensure IAM roles are set correctly. The deploy script handles this automatically, but may need 30-60 seconds for propagation.

**Date format errors:** Verify datetime objects are being formatted as ISO 8601 with Z suffix (e.g., `2025-09-30T00:00:00Z`) not with timezone offsets.

**Rate limiting:** Readwise APIs have rate limits (20-50 requests/minute). The client includes exponential backoff and retry logic.

**Missing environment variables:** Check they're set during deployment with `gcloud functions describe weekly-digest-generator --format="value(serviceConfig.environmentVariables)"`.

## License

MIT