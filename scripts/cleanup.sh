#!/bin/bash
# Nettoyage des fichiers inutiles

echo "🧹 Nettoyage des fichiers inutiles..."

# Scripts obsolètes
rm -f scripts/deploy_pipeline.sh
rm -f scripts/dashboard_setup.sh
rm -f scripts/quick_deploy.sh
rm -f scripts/example_full_deployment.py
rm -f scripts/improve_pipeline.py
rm -f scripts/analyze_architecture.py
rm -f scripts/generate_architecture.py
rm -f scripts/generate_uml.py

# Scripts anciens
rm -f deploy/enable_agent.sh
rm -f deploy/start_agent.sh
rm -f deploy/stop_agent.sh

# Documentation obsolète
rm -f REFACTORING_PLAN.md
rm -f IMPLEMENTATION_SUMMARY.md

# Build artifacts
rm -rf dist/
rm -rf htmlcov/
rm -rf src/ids_agent.egg-info/
find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Docker inutile
rm -rf docker_monolithic/
rm -f docker-compose.test.yml
rm -f Dockerfile.test

# Architecture docs
rm -rf architecture_docs/
rm -rf docs/uml/

echo "✅ Nettoyage terminé!"
