#!/bin/bash
# Setup Google Document AI Enterprise OCR Processor
# Run this script: bash scripts/setup_document_ai.sh

GCLOUD=~/google-cloud-sdk/bin/gcloud

echo "=== Document AI Setup ==="
echo ""

# Step 1: Authenticate
echo "Step 1: Authenticating with Google Cloud..."
$GCLOUD auth login

# Step 2: List projects and select
echo ""
echo "Step 2: Your GCP Projects:"
$GCLOUD projects list

echo ""
read -p "Enter your Project ID: " PROJECT_ID
$GCLOUD config set project $PROJECT_ID

# Step 3: Enable Document AI API
echo ""
echo "Step 3: Enabling Document AI API..."
$GCLOUD services enable documentai.googleapis.com

# Step 4: Create Enterprise Document OCR Processor
echo ""
echo "Step 4: Creating Enterprise Document OCR Processor..."
$GCLOUD documentai processors create \
  --display-name="Mindrian-OCR" \
  --type="OCR_PROCESSOR" \
  --location="eu"

# Note: ENTERPRISE_DOCUMENT_OCR might need to be just OCR_PROCESSOR
# The enterprise features are enabled via ProcessOptions in the API call

# Step 5: List processors to get ID
echo ""
echo "Step 5: Your processors:"
$GCLOUD documentai processors list --location=eu

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Add these to Render environment variables:"
echo "  GCP_PROJECT_ID=$PROJECT_ID"
echo "  GCP_LOCATION=eu"
echo "  DOCAI_PROCESSOR_ID=<copy from above>"
echo ""
echo "For authentication, also create a service account:"
echo "  $GCLOUD iam service-accounts create mindrian-docai --display-name='Mindrian Document AI'"
echo "  $GCLOUD projects add-iam-policy-binding $PROJECT_ID --member='serviceAccount:mindrian-docai@$PROJECT_ID.iam.gserviceaccount.com' --role='roles/documentai.apiUser'"
echo "  $GCLOUD iam service-accounts keys create ~/docai-key.json --iam-account=mindrian-docai@$PROJECT_ID.iam.gserviceaccount.com"
echo ""
echo "Then add the contents of ~/docai-key.json to Render as GOOGLE_APPLICATION_CREDENTIALS_JSON"
