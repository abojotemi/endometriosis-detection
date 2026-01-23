# Railway Deployment Guide

## Prerequisites
- Railway account (create at https://railway.app)
- GitHub account with your repository
- Git installed locally

## Step-by-Step Deployment

### 1. Connect GitHub to Railway
1. Go to [railway.app](https://railway.app) and sign up/login
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Authorize Railway to access your GitHub account
5. Select the `endometriosis-detection` repository

### 2. Railway Will Auto-Detect
Railway will automatically detect:
- Python project (via `requirements.txt`)
- Flask application
- Procfile configuration

### 3. Configure Environment Variables
In Railway project settings, add:

```
SECRET_KEY=your-secure-random-key-here
FLASK_ENV=production
DATABASE_URL=sqlite:///endometriosis.db
```

To generate a secure SECRET_KEY, use Python:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Auto-Deploy
Railway will automatically:
- Install Python 3.10
- Install all dependencies from `requirements.txt`
- Run `gunicorn app:app` (from Procfile)
- Initialize the database
- Deploy your app

### 5. Access Your App
Once deployed, Railway provides a public URL like:
```
https://endometriosis-detection-production.up.railway.app
```

View it under the "Deployments" tab in your Railway dashboard.

## Important Notes

### Database
- Uses SQLite (`instance/endometriosis.db`)
- Data persists across deployments on Railway
- For production with multiple users, consider PostgreSQL

### Default Admin Credentials
After first deployment, login with:
- **Email**: admin@hospital.com
- **Password**: admin123

**IMPORTANT**: Change this password immediately in production!

### File Uploads
- Uploaded files are stored in `static/uploads/`
- These persist on Railway's storage

### Monitor Deployments
1. Go to Railway dashboard
2. Select your project
3. View real-time logs and deployment status
4. Check "Metrics" tab for performance monitoring

## Troubleshooting

### If deployment fails:
1. Check Railway logs for error messages
2. Verify all dependencies in `requirements.txt`
3. Ensure `Procfile` is correct
4. Check Python version in `runtime.txt`

### View Live Logs
In Railway dashboard → Project → Deployments → View Logs

### Redeploy
- Push to GitHub main branch (automatic redeploy)
- Or click "Deploy" in Railway dashboard manually

## Update After Deployment

To update your app:
1. Make changes locally
2. Push to GitHub:
   ```bash
   git add .
   git commit -m "Your message"
   git push origin main
   ```
3. Railway automatically redeploys

## Database Backup (Optional)

To backup your SQLite database:
1. Connect via Railway CLI
2. Download the `instance/endometriosis.db` file

## Custom Domain (Optional)

In Railway → Project Settings → Domains:
1. Add custom domain
2. Configure DNS records
3. Enable SSL certificate (automatic)

## Scale Up (Optional)

For higher traffic:
1. Upgrade Railway plan
2. Add more instances
3. Consider PostgreSQL for multi-instance deployments

## Support

For Railway-specific help:
- Visit: https://docs.railway.app
- Check deployment logs in dashboard
- Contact Railway support

---

**Your app is now live on Railway!** 🚀
