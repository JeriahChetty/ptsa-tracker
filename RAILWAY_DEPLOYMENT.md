# 🚀 Deploy PTSA Tracker to Railway (Free)

## Step 1: Create Railway Account
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub (recommended) or email
3. Verify your account

## Step 2: Deploy from GitHub

### Option A: Deploy via GitHub (Recommended)
1. **Push your code to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit with Railway deployment"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/ptsa-tracker.git
   git push -u origin main
   ```

2. **Deploy on Railway**:
   - Go to [railway.app/new](https://railway.app/new)
   - Click "Deploy from GitHub repo"
   - Select your `ptsa-tracker` repository
   - Railway will automatically detect the `railway.json` and `Dockerfile.railway`

### Option B: Deploy via Railway CLI
1. **Install Railway CLI**:
   ```bash
   npm install -g @railway/cli
   # or
   curl -fsSL https://railway.app/install.sh | sh
   ```

2. **Login and Deploy**:
   ```bash
   railway login
   railway init
   railway up
   ```

## Step 3: Configure Environment Variables
After deployment, set these environment variables in Railway dashboard:

```
FLASK_ENV=production
SECRET_KEY=ptsa-railway-secret-key-2024
DATABASE_URL=sqlite:///app.db
PYTHONPATH=/app
```

## Step 4: Access Your Application
- Railway will provide a URL like: `https://your-app-name.up.railway.app`
- Login with: `admin@ptsa.co.za` / `admin123`
- **Change the password immediately after first login!**

## ✅ Features Included
- ✅ Admin profile management
- ✅ Export benchmarking data to Excel
- ✅ Complete PTSA tracking system
- ✅ Database with admin user pre-created
- ✅ All your recent fixes and improvements

## 💡 Railway Free Tier Limits
- 500 hours/month (enough for most projects)
- 1GB RAM
- 1GB storage
- Custom domains available

## 🔧 Troubleshooting
If deployment fails:
1. Check Railway logs in the dashboard
2. Ensure all files are committed to Git
3. Verify Dockerfile.railway syntax
4. Check environment variables are set correctly

## 📞 Need Help?
If you encounter issues, I can help troubleshoot the deployment process!
