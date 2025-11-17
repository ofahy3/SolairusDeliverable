#!/bin/bash

# Solairus Intelligence Report Generator - Google Cloud Deployment Script
# This script automates the deployment to Google Cloud Run

set -e  # Exit on error

echo "==========================================="
echo "Solairus Intelligence Report Deployment"
echo "==========================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first:"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get project ID
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ No Google Cloud project is set. Please run:"
    echo "   gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "📋 Using project: $PROJECT_ID"
echo ""

# Configuration
SERVICE_NAME="solairus-intelligence"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Build the container
echo "🔨 Building Docker container..."
docker build -t $SERVICE_NAME .

# Tag for GCR
echo "🏷️ Tagging image for Google Container Registry..."
docker tag $SERVICE_NAME $IMAGE_NAME

# Enable required APIs
echo "🔧 Enabling required Google Cloud APIs..."
gcloud services enable containerregistry.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Push to GCR
echo "📤 Pushing image to Google Container Registry..."
docker push $IMAGE_NAME

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 600 \
    --max-instances 10 \
    --port 8080

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')

echo ""
echo "==========================================="
echo "✅ Deployment Complete!"
echo "==========================================="
echo ""
echo "🌐 Your service is available at:"
echo "   $SERVICE_URL"
echo ""
echo "📝 Next steps:"
echo "1. Open the URL in your browser"
echo "2. Click 'Generate Intelligence Report'"
echo "3. Download the generated DOCX file"
echo ""
echo "💡 Tips:"
echo "- Use Test Mode for faster generation"
echo "- Check Cloud Run logs for troubleshooting:"
echo "  gcloud run logs read --service=$SERVICE_NAME --region=$REGION"
echo ""
