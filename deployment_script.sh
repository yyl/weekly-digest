#!/bin/bash

# Readwise Weekly Digest Generator - Deployment Script
# This script deploys the Cloud Function and sets up the Cloud Scheduler

set -e  # Exit on any error

# Configuration variables
PROJECT_ID=${1:-"your-project-id"}
REGION=${2:-"us-central1"}
FUNCTION_NAME="weekly-digest-generator"
TOPIC_NAME="weekly-digest-trigger"
JOB_NAME="weekly-digest-schedule"
SCHEDULE="0 0 * * 1"  # Every Monday at midnight UTC (cron format)

echo "Deploying Readwise Weekly Digest Generator to Google Cloud"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Function: $FUNCTION_NAME"

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

# Enable required APIs
echo "Enabling required Google Cloud APIs..."
gcloud services enable cloudfunctions.googleapis.com --project=$PROJECT_ID
gcloud services enable cloudscheduler.googleapis.com --project=$PROJECT_ID
gcloud services enable pubsub.googleapis.com --project=$PROJECT_ID

# Create Pub/Sub topic if it doesn't exist
echo "Creating Pub/Sub topic: $TOPIC_NAME"
gcloud pubsub topics create $TOPIC_NAME --project=$PROJECT_ID || echo "Topic already exists"

# Deploy the Cloud Function
echo "Deploying Cloud Function: $FUNCTION_NAME"
gcloud functions deploy $FUNCTION_NAME \
    --gen2 \
    --runtime=python311 \
    --region=$REGION \
    --source=. \
    --entry-point=weekly_digest_generator \
    --trigger-topic=$TOPIC_NAME \
    --timeout=540s \
    --memory=256Mi \
    --set-env-vars=READWISE_ACCESS_TOKEN="$READWISE_ACCESS_TOKEN",GITHUB_TOKEN="$GITHUB_TOKEN",GITHUB_REPO_OWNER="$GITHUB_REPO_OWNER",GITHUB_REPO_NAME="$GITHUB_REPO_NAME",GITHUB_TARGET_BRANCH="$GITHUB_TARGET_BRANCH" \
    --project=$PROJECT_ID

# Create Cloud Scheduler job
echo "Creating Cloud Scheduler job: $JOB_NAME"
gcloud scheduler jobs create pubsub $JOB_NAME \
    --location=$REGION \
    --schedule="$SCHEDULE" \
    --topic=$TOPIC_NAME \
    --message-body='{"trigger":"weekly-digest"}' \
    --project=$PROJECT_ID \
    --time-zone="UTC" || echo "Scheduler job already exists, updating..."

# If job already exists, update it
gcloud scheduler jobs update pubsub $JOB_NAME \
    --location=$REGION \
    --schedule="$SCHEDULE" \
    --topic=$TOPIC_NAME \
    --message-body='{"trigger":"weekly-digest"}' \
    --project=$PROJECT_ID \
    --time-zone="UTC" || true

echo ""
echo "Deployment completed successfully!"
echo ""
echo "Function URL: https://console.cloud.google.com/functions/details/$REGION/$FUNCTION_NAME?project=$PROJECT_ID"
echo "Scheduler Job: https://console.cloud.google.com/cloudscheduler/jobs/edit/$REGION/$JOB_NAME?project=$PROJECT_ID"
echo ""
echo "The function will run every Monday at midnight UTC."
echo "You can test it manually by running:"
echo "gcloud scheduler jobs run $JOB_NAME --location=$REGION --project=$PROJECT_ID"
echo ""
echo "To view logs:"
echo "gcloud functions logs read $FUNCTION_NAME --region=$REGION --project=$PROJECT_ID"