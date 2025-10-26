#!/bin/bash

# Readwise Weekly Digest Generator - UV Deployment Script
# This script deploys the Cloud Function using UV for dependency management

set -e  # Exit on any error

# Configuration variables
PROJECT_ID=${1:-"your-project-id"}
REGION=${2:-"us-central1"}
FUNCTION_NAME="weekly-digest-generator"
TOPIC_NAME="weekly-digest-trigger"
JOB_NAME="weekly-digest-schedule"
SCHEDULE="0 1 * * 6"  # Every Saturday at 1 AM UTC (cron format)

echo "Deploying Readwise Weekly Digest Generator to Google Cloud"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Function: $FUNCTION_NAME"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "Error: pyproject.toml not found. Please run from project root directory."
    exit 1
fi

# Check if required environment variables are set
if [ -z "$READWISE_ACCESS_TOKEN" ]; then
    echo "Error: READWISE_ACCESS_TOKEN environment variable is required"
    echo "Get your token from: https://readwise.io/access_token"
    exit 1
fi

if [ -z "$GITHUB_TOKEN" ]; then
    echo "Error: GITHUB_TOKEN environment variable is required"
    echo "Create a Personal Access Token with 'repo' scope at: https://github.com/settings/tokens"
    exit 1
fi

# Set default values for GitHub configuration
GITHUB_REPO_OWNER=${GITHUB_REPO_OWNER:-"yyl"}
GITHUB_REPO_NAME=${GITHUB_REPO_NAME:-"blog"}
GITHUB_TARGET_BRANCH=${GITHUB_TARGET_BRANCH:-"main"}

echo "GitHub Repository: $GITHUB_REPO_OWNER/$GITHUB_REPO_NAME"
echo "Target Branch: $GITHUB_TARGET_BRANCH"

# Create deployment directory
echo "Preparing deployment package..."
DEPLOY_DIR="deploy_temp"
rm -rf $DEPLOY_DIR
mkdir -p $DEPLOY_DIR

# Export requirements using UV
echo "Exporting requirements with UV..."
uv export --format requirements-txt --no-hashes > $DEPLOY_DIR/requirements.txt

# Copy source files to deployment directory
echo "Copying source files..."
cp -r src/readwise_digest/* $DEPLOY_DIR/
cp src/readwise_digest/__init__.py $DEPLOY_DIR/ 2>/dev/null || true

# Copy main.py from root directory (Cloud Functions expects it in root)
if [ -f "main.py" ]; then
    cp main.py $DEPLOY_DIR/
    echo "Copied main.py to deployment directory"
else
    echo "Error: main.py not found in root directory"
    echo "Please ensure main.py exists in the project root directory"
    exit 1
fi

echo "Deployment package prepared in $DEPLOY_DIR/"

# Enable required APIs
echo "Enabling required Google Cloud APIs..."
gcloud services enable cloudfunctions.googleapis.com --project=$PROJECT_ID
gcloud services enable cloudscheduler.googleapis.com --project=$PROJECT_ID
gcloud services enable pubsub.googleapis.com --project=$PROJECT_ID

# Create or verify Pub/Sub topic
echo "Setting up Pub/Sub topic: $TOPIC_NAME"
if gcloud pubsub topics describe $TOPIC_NAME --project=$PROJECT_ID &>/dev/null; then
    echo "✓ Pub/Sub topic already exists"
else
    echo "Creating new Pub/Sub topic..."
    gcloud pubsub topics create $TOPIC_NAME --project=$PROJECT_ID
    echo "✓ Pub/Sub topic created"
fi

# Deploy the Cloud Function
echo "Deploying Cloud Function: $FUNCTION_NAME"
gcloud functions deploy $FUNCTION_NAME \
    --gen2 \
    --runtime=python311 \
    --region=$REGION \
    --source=$DEPLOY_DIR \
    --entry-point=weekly_digest_generator \
    --trigger-topic=$TOPIC_NAME \
    --timeout=540s \
    --memory=256Mi \
    --set-env-vars=READWISE_ACCESS_TOKEN="$READWISE_ACCESS_TOKEN",GITHUB_TOKEN="$GITHUB_TOKEN",GITHUB_REPO_OWNER="$GITHUB_REPO_OWNER",GITHUB_REPO_NAME="$GITHUB_REPO_NAME",GITHUB_TARGET_BRANCH="$GITHUB_TARGET_BRANCH" \
    --project=$PROJECT_ID

# Create or update Cloud Scheduler job
echo "Setting up Cloud Scheduler job: $JOB_NAME"
if gcloud scheduler jobs describe $JOB_NAME --location=$REGION --project=$PROJECT_ID &>/dev/null; then
    echo "Updating existing scheduler job..."
    gcloud scheduler jobs update pubsub $JOB_NAME \
        --location=$REGION \
        --schedule="$SCHEDULE" \
        --topic=$TOPIC_NAME \
        --message-body='{"trigger":"weekly-digest"}' \
        --project=$PROJECT_ID \
        --time-zone="UTC"
    echo "✓ Scheduler job updated"
else
    echo "Creating new scheduler job..."
    gcloud scheduler jobs create pubsub $JOB_NAME \
        --location=$REGION \
        --schedule="$SCHEDULE" \
        --topic=$TOPIC_NAME \
        --message-body='{"trigger":"weekly-digest"}' \
        --project=$PROJECT_ID \
        --time-zone="UTC"
    echo "✓ Scheduler job created"
fi

# Clean up deployment directory
echo "Cleaning up deployment files..."
rm -rf $DEPLOY_DIR

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✓ Deployment completed successfully!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Function URL: https://console.cloud.google.com/functions/details/$REGION/$FUNCTION_NAME?project=$PROJECT_ID"
echo "Scheduler Job: https://console.cloud.google.com/cloudscheduler/jobs/edit/$REGION/$JOB_NAME?project=$PROJECT_ID"
echo ""
echo "The function will run every Monday at midnight UTC."
echo ""
echo "Manual testing:"
echo "  gcloud scheduler jobs run $JOB_NAME --location=$REGION --project=$PROJECT_ID"
echo ""
echo "View logs:"
echo "  gcloud functions logs read $FUNCTION_NAME --region=$REGION --project=$PROJECT_ID --limit=50"
echo ""