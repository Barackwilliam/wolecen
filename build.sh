#!/usr/bin/env bash
# build.sh — Render Build Script for JamiiTek
set -o errexit  # exit on error

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🗄️ Running migrations..."
python manage.py migrate --no-input

echo "📁 Collecting static files..."
python manage.py collectstatic --no-input --clear

echo "✅ Build complete!"
