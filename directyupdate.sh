#!/bin/bash

echo "🔧 Updating VolexSwarm folder structure..."

# Agent folders
AGENTS=(research signal strategy execution risk compliance meta)

for agent in "${AGENTS[@]}"; do
  mkdir -p "agents/$agent"
  touch "agents/$agent/__init__.py"
done

# Common utilities
mkdir -p common
touch common/__init__.py

# Data folders
mkdir -p data/{raw,processed,backtests,strategies}
mkdir -p logs/agents
mkdir -p scripts
mkdir -p webui/components
mkdir -p docker

# .env and README placeholders
touch .env
touch README.md

# Docker Compose exists at root; ensure it's not overwritten
if [ ! -f docker-compose.yml ]; then
  echo "version: '3.8'" > docker-compose.yml
  echo "services:" >> docker-compose.yml
fi

echo "✅ Folder structure updated successfully."

