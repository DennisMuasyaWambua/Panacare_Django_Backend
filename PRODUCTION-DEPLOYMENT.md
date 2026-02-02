# Production Deployment Guide

This guide covers deploying the Panacare Healthcare Backend to production environments.

## Table of Contents

1. [Deployment Options](#deployment-options)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Option 1: VPS Deployment (DigitalOcean, AWS EC2, Linode)](#option-1-vps-deployment)
4. [Option 2: Railway Deployment](#option-2-railway-deployment)
5. [Option 3: AWS ECS/Fargate](#option-3-aws-ecsfargate)
6. [Security Hardening](#security-hardening)
7. [SSL/TLS Setup](#ssltls-setup)
8. [Database Management](#database-management)
9. [Static & Media Files](#static--media-files)
10. [Monitoring & Logging](#monitoring--logging)
11. [Backup & Disaster Recovery](#backup--disaster-recovery)
12. [CI/CD Pipeline](#cicd-pipeline)

---

## Deployment Options

### Quick Comparison

| Platform | Difficulty | Cost | Scalability | Best For |
|----------|-----------|------|-------------|----------|
| Railway | Easy | $$ | Medium | Quick deployment, prototypes |
| DigitalOcean/Linode | Medium | $ | High | Full control, cost-effective |
| AWS ECS | Hard | $$$ | Very High | Enterprise, auto-scaling |
| Heroku | Easy | $$$ | Medium | Rapid deployment (deprecated Docker support) |

---

## Pre-Deployment Checklist

Before deploying to production, ensure you have:

### 1. Environment Configuration

- [ ] Copy `.env.production.example` to `.env.production`
- [ ] Set `DEBUG=False`
- [ ] Generate strong `SECRET_KEY` (50+ characters)
- [ ] Configure `ALLOWED_HOSTS` with your domain(s)
- [ ] Set up production database credentials
- [ ] Configure email service (SendGrid, AWS SES, etc.)
- [ ] Set up Firebase production credentials
- [ ] Configure Twilio production account
- [ ] Set up PesaPal production credentials
- [ ] Set `PESAPAL_SANDBOX=False`

### 2. Security

- [ ] Review and enable all security headers
- [ ] Set up SSL/TLS certificates
- [ ] Configure CORS for production domains only
- [ ] Enable secure cookies (`SESSION_COOKIE_SECURE=True`)
- [ ] Review Django security checklist: `python manage.py check --deploy`

### 3. Infrastructure

- [ ] Choose deployment platform
- [ ] Set up production database (managed service recommended)
- [ ] Configure cloud storage for media files (S3, Cloudinary)
- [ ] Set up CDN for static files (optional but recommended)
- [ ] Configure email service
- [ ] Set up monitoring and logging

### 4. Testing

- [ ] Run all tests: `python manage.py test`
- [ ] Test migrations on staging database
- [ ] Load test critical endpoints
- [ ] Test payment integration in sandbox
- [ ] Test email delivery
- [ ] Test video consultation functionality

---

## Option 1: VPS Deployment (DigitalOcean, AWS EC2, Linode)

### Overview

Deploy using Docker Compose with Nginx reverse proxy on a Virtual Private Server.

### Prerequisites

- VPS with Ubuntu 22.04 LTS (minimum 2GB RAM, 2 vCPUs)
- Domain name pointed to your VPS IP
- SSH access to the server

### Step 1: Server Setup

```bash
# SSH into your server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose-plugin -y

# Verify installation
docker --version
docker compose version

# Create application user
adduser panacare
usermod -aG docker panacare
su - panacare
```

### Step 2: Deploy Application

```bash
# Clone repository
git clone <your-repo-url>
cd Panacare_healthcare_Backend_Django

# Create production environment file
cp .env.production.example .env.production

# Edit with your actual values
nano .env.production
```

**Important `.env.production` values:**

```env
DEBUG=False
SECRET_KEY=<generate-using-python-secrets>
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DB_PASSWORD=<strong-password>
POSTGRES_PASSWORD=<strong-password>
```

### Step 3: Configure Domain

```bash
# Update nginx configuration with your domain
nano nginx/conf.d/panacare.conf

# Replace 'your-domain.com' with actual domain
```

### Step 4: Initial SSL Setup (HTTP first)

```bash
# Temporarily modify nginx config for initial SSL setup
# Comment out SSL sections in nginx/conf.d/panacare.conf
# Keep only the HTTP server block (port 80)

# Build and start services
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# Verify services are running
docker compose -f docker-compose.prod.yml ps
```

### Step 5: Obtain SSL Certificate

```bash
# Create certbot directories
mkdir -p certbot/conf certbot/www

# Get SSL certificate
docker compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email \
  -d your-domain.com \
  -d www.your-domain.com

# Uncomment SSL sections in nginx/conf.d/panacare.conf
nano nginx/conf.d/panacare.conf

# Restart nginx to apply SSL
docker compose -f docker-compose.prod.yml restart nginx
```

### Step 6: Database Migrations

```bash
# Run migrations
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# Create superuser
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Collect static files (if not done during build)
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### Step 7: Verify Deployment

```bash
# Check logs
docker compose -f docker-compose.prod.yml logs -f web

# Test endpoints
curl https://your-domain.com/admin/login/
curl https://your-domain.com/swagger/
```

### Step 8: Set Up Auto-Renewal

```bash
# Test renewal
docker compose -f docker-compose.prod.yml run --rm certbot renew --dry-run

# Certbot service will auto-renew every 12 hours
# Verify it's running
docker compose -f docker-compose.prod.yml ps certbot
```

### Step 9: Configure Firewall

```bash
# Switch back to root
exit

# Configure UFW firewall
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
ufw status
```

---

## Option 2: Railway Deployment

### Overview

Railway provides easy Docker deployment with managed PostgreSQL.

### Step 1: Prepare Repository

```bash
# Ensure your repository has:
# - Dockerfile.prod
# - railway.json (create if needed)
```

Create `railway.json`:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile.prod"
  },
  "deploy": {
    "startCommand": "python manage.py migrate && gunicorn --bind 0.0.0.0:$PORT --workers 4 panacare.wsgi:application",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Step 2: Railway Setup

1. Go to [railway.app](https://railway.app)
2. Sign in with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your repository

### Step 3: Add PostgreSQL

1. In your Railway project, click "New"
2. Select "Database" → "PostgreSQL"
3. Railway will create a database and provide `DATABASE_URL`

### Step 4: Configure Environment Variables

In Railway dashboard, add these variables:

```
DEBUG=False
SECRET_KEY=<your-secret-key>
ALLOWED_HOSTS=$RAILWAY_PUBLIC_DOMAIN
DATABASE_URL=${{Postgres.DATABASE_URL}}
FIREBASE_SERVICE_ACCOUNT_PATH=/app/firebase-service-account.json
TWILIO_ACCOUNT_SID=<your-value>
TWILIO_AUTH_TOKEN=<your-value>
PESAPAL_CONSUMER_KEY=<your-value>
PESAPAL_CONSUMER_SECRET=<your-value>
PESAPAL_SANDBOX=False
FRONTEND_URL=https://your-frontend.com
```

### Step 5: Configure Custom Domain

1. In Railway, go to Settings → Domains
2. Add custom domain: `api.your-domain.com`
3. Add CNAME record in your DNS:
   - Name: `api`
   - Value: provided by Railway

### Step 6: Deploy

```bash
# Push to main branch
git add .
git commit -m "Production deployment"
git push origin main

# Railway will automatically build and deploy
```

### Step 7: Run Migrations

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to project
railway link

# Run migrations
railway run python manage.py migrate

# Create superuser
railway run python manage.py createsuperuser
```

---

## Option 3: AWS ECS/Fargate

### Overview

Deploy using AWS ECS (Elastic Container Service) with Fargate for serverless containers.

### Prerequisites

- AWS Account
- AWS CLI installed and configured
- Docker images pushed to ECR (Elastic Container Registry)

### Step 1: Create ECR Repository

```bash
# Create repository
aws ecr create-repository --repository-name panacare-backend

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -f Dockerfile.prod -t panacare-backend:latest .
docker tag panacare-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/panacare-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/panacare-backend:latest
```

### Step 2: Create RDS PostgreSQL Database

1. Go to AWS RDS Console
2. Create PostgreSQL database
3. Choose "Production" template
4. Configure:
   - Instance size: db.t3.small or larger
   - Storage: 20GB GP2 (auto-scaling enabled)
   - Multi-AZ for high availability
5. Note the endpoint and credentials

### Step 3: Create ECS Cluster

```bash
# Create cluster
aws ecs create-cluster --cluster-name panacare-production

# Create task definition (see task-definition.json below)
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

Create `task-definition.json`:

```json
{
  "family": "panacare-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "panacare-web",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/panacare-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "DEBUG", "value": "False"},
        {"name": "DB_ENGINE", "value": "django.db.backends.postgresql"}
      ],
      "secrets": [
        {"name": "SECRET_KEY", "valueFrom": "arn:aws:secretsmanager:..."},
        {"name": "DB_PASSWORD", "valueFrom": "arn:aws:secretsmanager:..."}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/panacare",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "web"
        }
      }
    }
  ]
}
```

### Step 4: Create Load Balancer

1. Go to EC2 → Load Balancers
2. Create Application Load Balancer
3. Configure:
   - Internet-facing
   - HTTPS listener (port 443)
   - Target group: ECS tasks on port 8000
4. Add SSL certificate from ACM

### Step 5: Create ECS Service

```bash
aws ecs create-service \
  --cluster panacare-production \
  --service-name panacare-web \
  --task-definition panacare-backend:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=panacare-web,containerPort=8000"
```

### Step 6: Configure Auto Scaling

```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/panacare-production/panacare-web \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

# Create scaling policy
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/panacare-production/panacare-web \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://scaling-policy.json
```

---

## Security Hardening

### 1. Django Security Settings

Add to `settings.py` for production:

```python
# Security settings
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
```

### 2. Run Security Check

```bash
python manage.py check --deploy
```

### 3. Update Dependencies

```bash
# Check for security vulnerabilities
pip install safety
safety check -r requirements.txt

# Update packages
pip list --outdated
```

### 4. Rate Limiting

Install and configure Django rate limiting:

```bash
pip install django-ratelimit
```

### 5. Database Security

- Use strong passwords (16+ characters)
- Enable SSL connections
- Restrict network access (VPC/Security Groups)
- Regular backups
- Enable audit logging

---

## SSL/TLS Setup

### Let's Encrypt (Free)

Already covered in VPS deployment section above.

### AWS Certificate Manager (ACM)

1. Go to AWS Certificate Manager
2. Request public certificate
3. Validate domain (DNS or email)
4. Attach to Load Balancer

### Cloudflare (Free/Paid)

1. Add domain to Cloudflare
2. Update nameservers
3. Enable "Full (Strict)" SSL mode
4. Enable HSTS, Always Use HTTPS

---

## Database Management

### Migrations in Production

```bash
# Always test migrations on staging first!

# Backup database before migration
docker compose exec db pg_dump -U panacare panacare_production > backup_pre_migration.sql

# Run migrations
docker compose exec web python manage.py migrate

# If issues occur, rollback:
docker compose exec -T db psql -U panacare panacare_production < backup_pre_migration.sql
```

### Connection Pooling

Add to `settings.py`:

```python
DATABASES['default']['CONN_MAX_AGE'] = 600  # 10 minutes
```

For heavy load, use PgBouncer:

```yaml
# Add to docker-compose.prod.yml
pgbouncer:
  image: edoburu/pgbouncer
  environment:
    - DB_USER=panacare
    - DB_PASSWORD=yourpassword
    - DB_HOST=db
    - DB_NAME=panacare_production
    - POOL_MODE=transaction
    - MAX_CLIENT_CONN=1000
```

---

## Static & Media Files

### Option 1: AWS S3

```bash
pip install django-storages boto3
```

Add to `settings.py`:

```python
if not DEBUG:
    # S3 Configuration
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

    # Static files
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'

    # Media files
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
```

### Option 2: Cloudinary

```bash
pip install cloudinary django-cloudinary-storage
```

Add to `settings.py`:

```python
if not DEBUG:
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
        'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
        'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET')
    }

    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
```

### Option 3: Keep WhiteNoise (Simple)

WhiteNoise works well for small to medium applications:

```python
# Already configured in your project
# Just ensure collectstatic runs during deployment
```

---

## Monitoring & Logging

### 1. Sentry (Error Tracking)

```bash
pip install sentry-sdk
```

Add to `settings.py`:

```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

if not DEBUG:
    sentry_sdk.init(
        dsn=os.environ.get('SENTRY_DSN'),
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=True
    )
```

### 2. Application Monitoring

**New Relic:**

```bash
pip install newrelic
newrelic-admin generate-config YOUR_LICENSE_KEY newrelic.ini
```

**DataDog:**

```bash
pip install ddtrace
```

### 3. Log Aggregation

**CloudWatch (AWS):**
- Already configured in ECS task definition
- View logs in CloudWatch console

**Papertrail/Loggly:**

```python
# settings.py
LOGGING = {
    'handlers': {
        'syslog': {
            'class': 'logging.handlers.SysLogHandler',
            'address': ('logs.papertrailapp.com', 12345)
        }
    }
}
```

### 4. Uptime Monitoring

- **UptimeRobot** (free): https://uptimerobot.com
- **Pingdom**
- **StatusCake**

Set up alerts for:
- Website down
- Response time > 2 seconds
- SSL certificate expiring

---

## Backup & Disaster Recovery

### Database Backups

#### Automated Daily Backups (VPS)

Create `/home/panacare/backup.sh`:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/panacare/backups"
mkdir -p $BACKUP_DIR

# Backup database
docker compose exec -T db pg_dump -U panacare panacare_production | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/db_$DATE.sql.gz s3://panacare-backups/database/

# Keep only last 30 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete
```

Add to crontab:

```bash
crontab -e

# Add this line (runs daily at 2 AM)
0 2 * * * /home/panacare/backup.sh
```

#### RDS Automated Backups (AWS)

- Enable automated backups in RDS console
- Set retention period (7-35 days)
- Configure backup window

### Media Files Backup

If using volumes, backup media:

```bash
# Backup media files
tar -czf media_backup_$DATE.tar.gz /var/lib/docker/volumes/panacare_media_prod/_data
aws s3 cp media_backup_$DATE.tar.gz s3://panacare-backups/media/
```

### Disaster Recovery Plan

1. **Regular Testing**: Test restore procedure monthly
2. **Documentation**: Document all recovery steps
3. **RTO/RPO**: Define Recovery Time/Point Objectives
4. **Multi-Region**: Consider multi-region deployment for critical apps

---

## CI/CD Pipeline

### GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Login to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ secrets.REGISTRY_URL }}
          username: ${{ secrets.REGISTRY_USERNAME }}
          password: ${{ secrets.REGISTRY_PASSWORD }}

      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          file: Dockerfile.prod
          push: true
          tags: ${{ secrets.REGISTRY_URL }}/panacare:latest

      - name: Deploy to VPS
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USERNAME }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            cd /home/panacare/Panacare_healthcare_Backend_Django
            git pull origin main
            docker compose -f docker-compose.prod.yml pull
            docker compose -f docker-compose.prod.yml up -d
            docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate
```

### GitLab CI/CD

Create `.gitlab-ci.yml`:

```yaml
stages:
  - test
  - build
  - deploy

test:
  stage: test
  image: python:3.11
  script:
    - pip install -r requirements.txt
    - python manage.py test

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -f Dockerfile.prod -t $CI_REGISTRY_IMAGE:latest .
    - docker push $CI_REGISTRY_IMAGE:latest
  only:
    - main

deploy:
  stage: deploy
  script:
    - ssh user@server "cd /app && docker compose pull && docker compose up -d"
  only:
    - main
```

---

## Performance Optimization

### 1. Database Query Optimization

```python
# Use select_related and prefetch_related
queryset = Patient.objects.select_related('user').prefetch_related('appointments')

# Add database indexes
class Meta:
    indexes = [
        models.Index(fields=['created_at']),
        models.Index(fields=['user', 'status'])
    ]
```

### 2. Caching

Install Redis:

```bash
pip install django-redis
```

Configure in `settings.py`:

```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

Add Redis to `docker-compose.prod.yml`:

```yaml
redis:
  image: redis:alpine
  networks:
    - panacare_network
  restart: always
```

### 3. Gunicorn Workers

Calculate optimal workers:

```
workers = (2 × CPU cores) + 1
```

For 2 CPU cores: `--workers 5`

---

## Troubleshooting Production Issues

### 1. Application Won't Start

```bash
# Check logs
docker compose -f docker-compose.prod.yml logs web

# Common issues:
# - Missing environment variables
# - Database connection failed
# - Port already in use
```

### 2. 502 Bad Gateway

```bash
# Check if application is running
docker compose ps

# Check nginx logs
docker compose logs nginx

# Verify upstream is correct
curl http://web:8000  # from inside nginx container
```

### 3. Static Files Not Loading

```bash
# Collect static files
docker compose exec web python manage.py collectstatic --noinput

# Check nginx static file path
docker compose exec nginx ls /app/staticfiles

# Verify nginx configuration
docker compose exec nginx nginx -t
```

### 4. Database Connection Issues

```bash
# Test database connection
docker compose exec web python manage.py dbshell

# Check database logs
docker compose logs db

# Verify environment variables
docker compose exec web env | grep DB_
```

---

## Post-Deployment

### 1. Verify Deployment

- [ ] Test all critical endpoints
- [ ] Verify SSL certificate
- [ ] Test user registration/login
- [ ] Test payment integration
- [ ] Test video consultation
- [ ] Test email delivery
- [ ] Check error tracking (Sentry)
- [ ] Verify monitoring dashboards

### 2. Set Up Monitoring Alerts

Configure alerts for:
- CPU usage > 80%
- Memory usage > 80%
- Disk usage > 80%
- Response time > 2s
- Error rate > 1%
- SSL certificate expiring in 30 days

### 3. Documentation

Document:
- Deployment process
- Environment variables
- Backup procedures
- Rollback procedures
- Incident response plan
- On-call rotation

---

## Cost Optimization

### VPS Deployment

- **DigitalOcean**: $24/month (4GB RAM, 2 vCPUs)
- **Linode**: $24/month (4GB RAM, 2 vCPUs)
- **AWS RDS**: $30-50/month (db.t3.small)
- **Total**: ~$50-75/month

### Railway

- **Application**: ~$20-30/month
- **PostgreSQL**: ~$10-20/month
- **Total**: ~$30-50/month

### AWS ECS

- **Fargate**: ~$40-60/month (2 tasks)
- **RDS**: ~$40-60/month
- **Load Balancer**: ~$20/month
- **Total**: ~$100-140/month

### Cost Reduction Tips

1. Use reserved instances for predictable workloads
2. Enable auto-scaling to reduce idle costs
3. Use spot instances for non-critical workloads
4. Optimize database instance size
5. Use CDN to reduce bandwidth costs
6. Compress images and static files

---

## Summary

This guide covered three main deployment options:

1. **VPS (Recommended for most)**: Full control, cost-effective
2. **Railway**: Easiest, good for prototypes
3. **AWS ECS**: Most scalable, best for enterprise

Choose based on your:
- Technical expertise
- Budget
- Scalability needs
- Compliance requirements

For questions or issues, refer to:
- Django deployment checklist: https://docs.djangoproject.com/en/stable/howto/deployment/checklist/
- Docker production guide: https://docs.docker.com/compose/production/
- Nginx best practices: https://www.nginx.com/blog/

Good luck with your deployment! 🚀
