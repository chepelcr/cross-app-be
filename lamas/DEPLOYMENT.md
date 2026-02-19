# GitHub Pages Deployment Guide

This guide will help you deploy your portfolio website to your GitHub Pages repository with custom domain.

## Quick Setup

### Option 1: Automatic Deployment (Recommended)

1. **Push to your GitHub Pages repository:**
   ```bash
   # Initialize git if not already done
   git init
   
   # Add your GitHub repository as origin
   git remote add origin https://github.com/chepelcr/chepelcr.github.io.git
   ```

2. **Push your code to GitHub:**
   ```bash
   git add .
   git commit -m "Portfolio website deployment"
   git push -u origin dev
   ```

3. **Enable GitHub Pages:**
   - Go to your repository on GitHub
   - Navigate to Settings → Pages
   - Set Source to "GitHub Actions"
   - Navigate to Settings → Actions → General
   - Under "Workflow permissions", select "Read and write permissions"
   - Check "Allow GitHub Actions to create and approve pull requests"
   - The workflow will automatically deploy your site

4. **Your site will be available at:**
   `https://jcampos.dev/`

### Option 2: Manual Build

1. **Build the static files:**
   ```bash
   ./build-gh-pages.sh
   ```

2. **Deploy the `dist/gh-pages` folder to your GitHub Pages repository**

## Configuration Details

### GitHub Actions Workflow
- Located in `.github/workflows/deploy.yml`
- Automatically builds and deploys on push to dev branch
- Uses optimized build configuration for static hosting

### Build Configuration
- Uses `vite.config.gh-pages.ts` for GitHub Pages specific settings
- Sets base path to `/` for root domain deployment
- Removes server-side dependencies
- Optimizes for static hosting
- Includes CNAME file for custom domain (jcampos.dev)

## Features Available on GitHub Pages

✅ **Available:**
- Complete portfolio website
- Responsive design
- Dark/light mode
- Language switching (Spanish/English)
- PDF CV generation
- All animations and interactions

❌ **Not Available (Static Hosting Limitations):**
- Contact form email sending (backend required)
- Database functionality
- Server-side features

## Customization

### Change Domain
If you want to use a different domain, update the CNAME file in `client/public/CNAME`:

```
yourdomain.com
```

### Custom Domain
To use a custom domain:
1. Add a `CNAME` file to the `client/public` folder with your domain
2. Configure DNS settings with your domain provider
3. Enable custom domain in GitHub Pages settings

## Troubleshooting

### Permission Issues
If you see "Permission denied" or "403" errors during deployment:
1. Go to your repository on GitHub
2. Navigate to Settings → Actions → General
3. Under "Workflow permissions", select "Read and write permissions"  
4. Check "Allow GitHub Actions to create and approve pull requests"
5. Re-run the failed workflow from the Actions tab

### Build Fails
- Check that all dependencies are installed: `npm install`
- Ensure Node.js version 18+ is being used

### Site Not Loading
- Verify the base path matches your repository name
- Check GitHub Pages settings are configured correctly
- Wait a few minutes for DNS propagation

### Assets Not Loading
- Ensure all assets use relative paths
- Check that the base path is correctly set in the build configuration

## Manual Deployment Alternative

If you prefer manual deployment:

1. Build locally: `./build-gh-pages.sh`
2. Create a new branch called `gh-pages`
3. Copy contents of `dist/gh-pages` to the root of the `gh-pages` branch
4. Push the `gh-pages` branch to GitHub
5. Set GitHub Pages source to "Deploy from a branch" → `gh-pages`