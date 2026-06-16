# Havilah OS — Railway Deployment Guide

## Quick Deploy (Recommended)

1. Go to [railway.app](https://railway.app) and sign up with GitHub
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select `Ogienomo/havilah`
4. Railway auto-detects the Dockerfile

## Environment Variables

Set these in Railway → Project → Variables:

### Required
```
HAVILAH_SECRET_KEY=<generate-a-strong-secret>
HAVILAH_OPENAI_API_KEY=<your-openai-key>
```

### Optional (with defaults)
```
HAVILAH_ENV=production
HAVILAH_DEBUG=false
HAVILAH_OPENAI_MODEL=gpt-4o
HAVILAH_OPENAI_BASE_URL=
HAVILAH_HERMES_ENABLED=true
HAVILAH_WHATSAPP_ENABLED=false
HAVILAH_WHATSAPP_VERIFY_TOKEN=
HAVILAH_WHATSAPP_ACCESS_TOKEN=
HAVILAH_WHATSAPP_PHONE_NUMBER_ID=
```

### Database
Railway will auto-provision PostgreSQL. The connection vars are:
```
HAVILAH_DB_HOST=<from-railway-postgres>
HAVILAH_DB_PORT=5432
HAVILAH_DB_NAME=havilah
HAVILAH_DB_USER=<from-railway-postgres>
HAVILAH_DB_PASSWORD=<from-railway-postgres>
```

## Steps

1. **Add PostgreSQL**: In Railway, click "+ New" → "Database" → "PostgreSQL"
2. **Link variables**: Railway auto-creates `DATABASE_URL`. Map it to `HAVILAH_DB_*` vars.
3. **Run migrations**: After first deploy, open Railway shell and run:
   ```bash
   alembic upgrade head
   ```
4. **Create first admin user**: 
   ```bash
   curl -X POST https://<your-app>.up.railway.app/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","email":"admin@havilah.os","password":"<strong-password>"}'
   ```

## Custom Domain (Optional)
In Railway → Settings → Custom Domain, add your domain.

## Cost
- Free tier: $5 credit/month (enough for development)
- Hobby plan: $5/month (recommended for production)
