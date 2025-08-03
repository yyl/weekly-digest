# Readwise Weekly Digest Generator

An automated system that generates weekly reading digests from your Readwise account and commits them as draft blog posts to a GitHub repository. Perfect for bloggers who want to track their reading habits and share insights.

## Features

- 📊 **Comprehensive Reading Statistics**: Track articles archived, total word count, and breakdowns by category/source
- 📝 **Highlight Collection**: Gather all highlights created in the past week
- 📄 **Markdown Generation**: Create beautifully formatted digest posts with YAML front matter
- 🔄 **Automated Deployment**: Runs weekly on Google Cloud Functions with Cloud Scheduler
- 📦 **GitHub Integration**: Automatically commits draft posts to your blog repository

## What Gets Generated

Each weekly digest includes:

- **Overview Statistics**: Number of articles read, total words, highlight count, and average time to archive
- **Article Breakdowns**: By category (articles, books, etc.), source (RSS, imports, etc.)
- **Archived Articles List**: Titles, authors, word counts, and time to archive (in hours), sorted by most recently archived
- **Highlights**: All highlights created during the week with optional notes
- **YAML Front Matter**: Ready for static site generators (Hugo, Jekyll, etc.)

## Quick Start

### 1. Get Your API Tokens

**Readwise Token:**
- Go to [https://readwise.io/access_token](https://readwise.io/access_token)
- Copy your access token

**GitHub Token:**
- Go to [GitHub Settings > Personal Access Tokens](https://github.com/settings/tokens)
- Create a new token with `repo` scope
- Copy the token

### 2. Local Testing

```bash
# Clone or download the files
# Install dependencies
pip install -r requirements.txt

# Install python-dotenv for local testing
pip install python-dotenv

# Copy environment template
cp .env.template .env

# Edit .env with your actual tokens
nano .env

# Run local test (dry run - won't commit to GitHub)
python test_local.py

# Run test with actual GitHub commit
python test_local.py --commit
```

### 3. Deploy to Google Cloud

```bash
# Make deployment script executable
chmod +x deploy.sh

# Set your environment variables
export READWISE_ACCESS_TOKEN="your_token_here"
export GITHUB_TOKEN="your_github_token_here"
export GITHUB_REPO_OWNER="your_username"
export GITHUB_REPO_NAME="your_repo_name"

# Deploy (replace with your actual project ID)
./deploy.sh your-google-cloud-project-id us-central1
```

## Architecture

```
Cloud Scheduler (Weekly) → Pub/Sub Topic → Cloud Function
                                              ↓
                                         Readwise APIs
                                              ↓
                                      Process & Generate
                                              ↓
                                         GitHub API
                                              ↓
                                      Your Blog Repo
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `READWISE_ACCESS_TOKEN` | Your Readwise API token | ✅ | - |
| `GITHUB_TOKEN` | GitHub Personal Access Token with repo scope | ✅ | - |
| `GITHUB_REPO_OWNER` | GitHub username/organization | ✅ | - |
| `GITHUB_REPO_NAME` | Repository name | ✅ | - |
| `GITHUB_TARGET_BRANCH` | Target branch for commits | ❌ | `main` |

### Schedule Configuration

By default, the digest runs every Monday at midnight UTC. You can modify the schedule in `deploy.sh`:

```bash
SCHEDULE="0 0 * * 1"  # Monday at midnight UTC
```

Common schedule examples:
- `"0 8 * * 1"` - Monday at 8 AM UTC
- `"0 0 * * 0"` - Sunday at midnight UTC
- `"0 9 * * SUN"` - Sunday at 9 AM UTC

## File Structure

```
├── main.py                 # Cloud Function entry point
├── readwise_client.py      # Readwise API integration
├── github_client.py        # GitHub API integration
├── data_processor.py       # Data processing logic
├── markdown_generator.py   # Markdown content generation
├── requirements.txt        # Python dependencies
├── deploy.sh              # Deployment script
├── test_local.py          # Local testing script
├── .env.template          # Environment variables template
└── README.md              # This file
```

## Generated Markdown Format

```markdown
---
title: "Weekly Reading Digest - 2024-01-01 to 2024-01-07"
date: 2024-01-08T00:00:00Z
draft: true
tags: ["reading", "digest", "readwise", "automated"]
categories: ["Reading"]
---

## Overview

- **Articles Archived**: 5
- **Total Words Read**: 12,450
- **Highlights Created**: 23
- **Average Words per Article**: 2,490
- **Average Time Before Archive**: 2.00 hours

## Article Breakdowns

### By Category
- **Article**: 4
- **Book**: 1

### By Source
- **Reader RSS**: 3
- **Import URL**: 2

### By Location
- **Archive**: 5

### Archived Articles
- **Article Title** by Author Name (2,500 words) (archived after 1.00 hours)
- **Another Article Title** by Another Author (1,500 words) (archived after 3.00 hours)

## Highlights from the Past Week

1. "Insightful quote from your reading..."
   - *Note: Your personal note about this highlight*

2. "Another interesting highlight..."
```

## Troubleshooting

### Common Issues

**"Missing required environment variables"**
- Ensure all required environment variables are set
- Check that your `.env` file is properly formatted

**"Readwise connection failed"**
- Verify your Readwise access token is correct
- Check if your token has proper permissions

**"GitHub connection failed"**
- Verify your GitHub token has `repo` scope
- Ensure the repository exists and you have write access

**"No data found"**
- The system looks for articles archived in the past 7 days
- If you haven't archived any articles recently, the digest will be minimal

### Viewing Logs

**Local Testing:**
```bash
python test_local.py
```

**Google Cloud Function:**
```bash
gcloud functions logs read weekly-digest-generator --region=us-central1 --project=your-project-id
```

**Google Cloud Console:**
Visit the Cloud Functions page in Google Cloud Console to view logs and monitoring.

### Manual Execution

You can manually trigger the Cloud Function:

```bash
gcloud scheduler jobs run weekly-digest-schedule --location=us-central1 --project=your-project-id
```

## Customization

### Modify the Schedule
Edit the `SCHEDULE` variable in `deploy.sh` before deployment.

### Change Output Format
Modify `markdown_generator.py` to customize the generated markdown format.

### Add More Data
Extend `data_processor.py` to include additional statistics or data from Readwise.

### Custom Repository Structure
Update the file path in `main.py` if your blog uses a different directory structure.

## Cost Considerations

This system is designed to be cost-effective:

- **Cloud Function**: Only runs once per week, typically under 1 minute
- **Cloud Scheduler**: Minimal cost for weekly scheduling
- **Pub/Sub**: Very low message volume
- **Estimated monthly cost**: Under $1 USD for typical usage

## Privacy and Security

- API tokens are stored as environment variables in Google Cloud
- No data is stored persistently; everything is processed in memory
- All communication uses HTTPS
- Generated content is committed to your private repository (or public if you choose)

## Contributing

Feel free to customize this system for your needs! Some ideas for enhancements:

- Add email notifications for failed runs
- Include book highlights in addition to article highlights
- Generate charts or visualizations of reading data
- Support for multiple Readwise accounts
- Integration with other note-taking systems

## License

This project is open source. Feel free to use, modify, and distribute as needed.

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review the logs for error messages
3. Test locally using `test_local.py`
4. Verify your API tokens are correct and have proper permissions

---

Happy reading and blogging! 📚✨