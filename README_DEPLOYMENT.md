# Quick Deployment Guide

## ⚠️ Important: Django + Cloudflare Limitation

**Django cannot run directly on Cloudflare Pages** because it requires a persistent Python server. However, you have better alternatives!

## 🚀 Recommended: Deploy to Railway (Easiest)

Railway is perfect for Django and offers a generous free tier.

### Step-by-Step Railway Deployment:

1. **Create a GitHub repository** (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/yourusername/blood-donor.git
   git push -u origin main
   ```

2. **Go to [Railway.app](https://railway.app)** and sign in with GitHub

3. **Click "New Project"** → **"Deploy from GitHub repo"**

4. **Select your blood-donor repository**

5. **Add a MySQL Database:**
   - Click "+ New" → "Database" → "Add MySQL"
   - Railway automatically connects it to your app

6. **Set Environment Variables:**
   Click your Django service → "Variables" → Add these:
   ```
   SECRET_KEY=your-super-secret-key-change-this
   DEBUG=False
   ALLOWED_HOSTS=.railway.app
   DJANGO_SETTINGS_MODULE=config.settings
   ```

7. **Deploy automatically starts!** 

8. **Your app will be live at:** `your-app-name.railway.app`

### After First Deploy:

```bash
# Railway CLI (optional but useful)
npm i -g @railway/cli
railway login
railway link

# Run migrations
railway run python manage.py migrate

# Create superuser
railway run python manage.py createsuperuser
```

## 🌐 Alternative: Render.com

1. Go to [Render.com](https://render.com)
2. Create new "Web Service"
3. Connect GitHub repo
4. Render auto-detects Django
5. Add environment variables
6. Deploy!

## ☁️ Using Cloudflare as CDN (After Deploying)

Once your app is on Railway/Render:

1. **Add site to Cloudflare:**
   - Go to Cloudflare dashboard
   - Click "Add a Site"
   - Enter your domain

2. **Update Nameservers** at your domain registrar

3. **Create DNS Record:**
   - Type: CNAME
   - Name: @ (or www)
   - Target: your-app.railway.app
   - Proxy: Enabled (orange cloud)

4. **Update ALLOWED_HOSTS:**
   Add your domain to Railway environment variables:
   ```
   ALLOWED_HOSTS=.railway.app,yourdomain.com,www.yourdomain.com
   ```

## 📋 Pre-Deployment Checklist

- [ ] Push code to GitHub
- [ ] Create Railway/Render account
- [ ] Deploy app
- [ ] Add MySQL database
- [ ] Set environment variables
- [ ] Run migrations
- [ ] Create superuser
- [ ] Test the live site
- [ ] (Optional) Add custom domain via Cloudflare

## 🔧 Local Testing Before Deploy

```bash
# Install dependencies
pip install -r requirements.txt

# Set DEBUG=False in .env
DEBUG=False

# Collect static files
python manage.py collectstatic

# Test locally
python manage.py runserver
```

## 💾 Database Options

### Railway MySQL (Recommended)
- Automatically provisioned
- Free tier available
- No configuration needed

### PlanetScale (MySQL Alternative)
- Generous free tier
- Serverless MySQL
- Great performance

### Supabase (PostgreSQL)
- Free tier
- Real-time capabilities
- Easy to set up

## 📞 Need Help?

- Railway Docs: https://docs.railway.app
- Django Deployment: https://docs.djangoproject.com/en/4.2/howto/deployment/
- This project's guide: See DEPLOYMENT_GUIDE.md

## 🎯 Quick Commands Reference

```bash
# Railway CLI
railway login
railway link
railway up
railway run python manage.py migrate
railway run python manage.py createsuperuser
railway logs

# Git
git add .
git commit -m "Deploy changes"
git push

# Django
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py createsuperuser
```

Good luck with your deployment! 🚀
