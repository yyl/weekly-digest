# Readwise Weekly Digest Generator

Automated system that generates weekly reading digests from your Readwise account and publishes them to your blog via GitHub.

## Overview

This serverless application runs weekly on Google Cloud Functions, fetching your archived articles and highlights from Readwise, processing the data into a formatted markdown digest, and committing it to your GitHub blog repository for automatic publication.

## Architecture

```
Cloud Scheduler (every Saturday 1 AM UTC)
    ↓ publishes message
Pub/Sub Topic
    ↓ triggers
Cloud Function (Python 3.11)
    ↓ fetches data
Readwise APIs
    ↓ processes & generates
Markdown Digest
    ↓ commits
GitHub Repository
    ↓ auto-deploys
Your Blog
```

**Key components:**
- Cloud Function scales to zero when idle (minimal cost)
- Pub/Sub provides reliable message delivery
- Environment variables store API tokens securely
- Runs every Saturday at 1 AM UTC

## Code Structure

- **`main.py`** - Cloud Function entry point and orchestration logic
- **`readwise_client.py`** - Readwise API client with rate limiting and pagination
- **`github_client.py`** - GitHub API client for file operations
- **`data_processor.py`** - Processes API responses into structured data
- **`markdown_generator.py`** - Generates formatted markdown with YAML front matter
- **`scripts/deploy.sh`** - Deployment automation script
- **`scripts/test_local.py`** - Local testing script

## Quick Start

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

The deploy script will:
- Create Pub/Sub topic (if needed)
- Deploy the Cloud Function
- Create/update Cloud Scheduler job
- Set environment variables

### 3. Manual Testing
```bash
# Trigger via Scheduler
gcloud scheduler jobs run weekly-digest-schedule \
  --location=us-central1 \
  --project=your-project-id

# View logs
gcloud functions logs read weekly-digest-generator \
  --region=us-central1 \
  --project=your-project-id \
  --limit=50
```

### 4. Update Configuration
```bash
# Update environment variables
gcloud functions deploy weekly-digest-generator \
  --update-env-vars GITHUB_REPO_NAME=new-repo \
  --region=us-central1 \
  --project=your-project-id

# Change schedule (edit SCHEDULE in deploy.sh, then redeploy)
```

## Requirements

- Python 3.11+
- UV package manager
- Google Cloud Project with billing enabled
- Readwise account with API access
- GitHub repository for your blog
- API tokens: Readwise access token, GitHub personal access token (repo scope)

## Generated Content

Each weekly digest includes:
- Article count, total words read, highlight count
- Breakdown by category and source
- Table of archived articles with metadata
- Table of tags with counts
- All highlights created during the week with optional notes
- YAML front matter (published automatically with `draft: false`)

## Cost

Typical monthly cost: **$0-$0.10**
- Cloud Function: ~$0.001 (4 invocations/month, 30s each)
- Cloud Scheduler: First 3 jobs free
- Pub/Sub: First 10GB free
- Cloud Logging: First 50GB free

## Troubleshooting

**Function not triggering:** Check scheduler job status with `gcloud scheduler jobs describe weekly-digest-schedule --location=us-central1`. The deploy script handles Pub/Sub setup automatically.

**Permission errors:** IAM roles are set automatically by the deploy script. Allow 30-60 seconds for propagation after first deployment.

**Rate limiting:** Readwise APIs have rate limits. The client includes exponential backoff and retry logic.

**Missing environment variables:** Check with `gcloud functions describe weekly-digest-generator --format="value(serviceConfig.environmentVariables)"`.

## License

MIT