#!/bin/bash

echo "🚀 Building portfolio for GitHub Pages..."

# Clean previous build
rm -rf dist/gh-pages

# Build the project using the GitHub Pages vite config
npx vite build --config vite.config.gh-pages.ts

# Copy additional files needed for GitHub Pages
cp client/public/CNAME dist/gh-pages/ 2>/dev/null || true
cp client/public/404.html dist/gh-pages/ 2>/dev/null || true

echo "✅ Build completed!"
echo "📁 Build files are in: dist/gh-pages"
echo ""
echo "🔗 To deploy to GitHub Pages:"
echo "1. Push this code to your chepelcr.github.io repository (dev branch)"
echo "2. Enable GitHub Pages in repository settings"
echo "3. Set source to 'GitHub Actions'"
echo "4. The site will be available at: https://jcampos.dev/"