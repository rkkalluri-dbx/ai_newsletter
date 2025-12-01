#!/bin/bash

# Quick Config Seeding Script
# Uploads and runs the config seeding notebook in Databricks

set -e

PROFILE="DEFAULT"
NOTEBOOK_PATH="/Workspace/Users/rkalluri@gmail.com/seed_config"
LOCAL_SCRIPT="src/seed_config.py"

echo "=========================================="
echo "CONFIGURATION DATA SEEDING"
echo "=========================================="
echo ""

# Check if local script exists
if [ ! -f "$LOCAL_SCRIPT" ]; then
    echo "❌ Error: $LOCAL_SCRIPT not found"
    echo "   Run this script from the project root directory"
    exit 1
fi

echo "[1/2] Uploading seeding script to Databricks..."
databricks workspace import "$NOTEBOOK_PATH" \
    --file "$LOCAL_SCRIPT" \
    --language PYTHON \
    --overwrite \
    --profile "$PROFILE"

if [ $? -eq 0 ]; then
    echo "✅ Script uploaded successfully"
else
    echo "❌ Failed to upload script"
    exit 1
fi

echo ""
echo "[2/2] Run the notebook in Databricks UI:"
echo "   https://dbc-2647a0d2-b28d.cloud.databricks.com"
echo "   Navigate to: Workspace → Users → rkalluri@gmail.com → seed_config"
echo "   Click 'Run All'"
echo ""
echo "Or use this SQL to view the table after running:"
echo "   SELECT * FROM main.config.search_terms ORDER BY category, term;"
echo ""
echo "=========================================="
