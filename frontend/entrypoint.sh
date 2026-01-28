#!/bin/sh

# Target file
ENV_FILE="/usr/share/nginx/html/assets/env.js"

# Create assets directory if not exists
mkdir -p /usr/share/nginx/html/assets

# Start writing file
echo "window.__env = {" > $ENV_FILE

# Inject specific environment variables
# Add more variables here as needed
echo "  apiUrl: '${API_URL:-http://localhost:8000/api}'," >> $ENV_FILE
echo "  linktreeUrl: '${LINKTREE_URL:-http://localhost:8000}'," >> $ENV_FILE

# Close object
echo "};" >> $ENV_FILE

echo "Generated env.js with content:"
cat $ENV_FILE
