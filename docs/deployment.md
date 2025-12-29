# Deployment Guide

This guide covers deploying FastAuth applications to production environments with best practices for security, scalability, and reliability.

## Table of Contents

- [Production Checklist](#production-checklist)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Deployment Platforms](#deployment-platforms)
- [Security Hardening](#security-hardening)
- [Monitoring and Logging](#monitoring-and-logging)
- [Performance Optimization](#performance-optimization)

## Production Checklist

Before deploying to production, ensure you've completed these steps:

### Security
- [ ] Generate strong JWT secret key (32+ bytes)
- [ ] Enable HTTPS/TLS for all connections
- [ ] Configure CORS properly
- [ ] Enable email verification
- [ ] Set up secure password reset flow
- [ ] Configure rate limiting
- [ ] Use environment variables for secrets
- [ ] Enable security headers
- [ ] Review and test authentication flows

### Database
- [ ] Use production database (PostgreSQL/MySQL)
- [ ] Set up database backups
- [ ] Configure connection pooling
- [ ] Run database migrations
- [ ] Set up database monitoring
- [ ] Configure read replicas (if needed)

### Email
- [ ] Configure production email provider (SMTP/SendGrid/SES)
- [ ] Test email delivery
- [ ] Set up email templates
- [ ] Configure SPF/DKIM/DMARC records

### Monitoring
- [ ] Set up application logging
- [ ] Configure error tracking (Sentry)
- [ ] Set up uptime monitoring
- [ ] Configure performance monitoring (APM)
- [ ] Set up alerts for critical issues

### Testing
- [ ] All tests passing (85%+ coverage)
- [ ] Load testing completed
- [ ] Security audit passed
- [ ] OAuth flows tested end-to-end

## Environment Configuration

### Production Environment Variables

Create a production `.env` file or configure environment variables:

```bash
# Application
ENV=production
DEBUG=false

# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# JWT Configuration
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email Configuration
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@yourdomain.com
SMTP_FROM_NAME=Your App Name

# Email Verification
REQUIRE_EMAIL_VERIFICATION=true
EMAIL_VERIFICATION_EXPIRE_MINUTES=1440

# OAuth (if using)
OAUTH_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
OAUTH_GOOGLE_CLIENT_SECRET=your-client-secret
OAUTH_GOOGLE_REDIRECT_URI=https://yourdomain.com/auth/oauth/google/callback

# CORS
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Security
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SECURE_COOKIES=true
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=lax
```

### Secrets Management

**Never commit secrets to version control.**

#### AWS Secrets Manager

```python
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

secrets = get_secret('prod/fastauth')
JWT_SECRET_KEY = secrets['JWT_SECRET_KEY']
```

#### HashiCorp Vault

```python
import hvac

client = hvac.Client(url='https://vault.example.com')
client.token = os.getenv('VAULT_TOKEN')
secrets = client.secrets.kv.v2.read_secret_version(path='prod/fastauth')
JWT_SECRET_KEY = secrets['data']['data']['JWT_SECRET_KEY']
```

#### Docker Secrets

```yaml
# docker-compose.yml
services:
  app:
    secrets:
      - jwt_secret_key
      - db_password

secrets:
  jwt_secret_key:
    external: true
  db_password:
    external: true
```

## Database Setup

### PostgreSQL (Recommended)

#### Installation

```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql
```

#### Configuration

```bash
# Create database and user
sudo -u postgres psql

postgres=# CREATE DATABASE fastauth_prod;
postgres=# CREATE USER fastauth_user WITH ENCRYPTED PASSWORD 'strong_password';
postgres=# GRANT ALL PRIVILEGES ON DATABASE fastauth_prod TO fastauth_user;
postgres=# \q
```

#### Connection String

```bash
DATABASE_URL=postgresql://fastauth_user:strong_password@localhost:5432/fastauth_prod
```

### Database Migrations

Use Alembic for database migrations:

```bash
# Install Alembic
pip install alembic

# Initialize Alembic
alembic init alembic

# Configure alembic.ini
sqlalchemy.url = postgresql://user:password@localhost/dbname

# Create migration
alembic revision --autogenerate -m "Add FastAuth models"

# Apply migration
alembic upgrade head
```

### Connection Pooling

Configure SQLAlchemy connection pool:

```python
from sqlmodel import create_engine

engine = create_engine(
    DATABASE_URL,
    pool_size=20,          # Max connections in pool
    max_overflow=10,       # Extra connections when pool full
    pool_timeout=30,       # Seconds to wait for connection
    pool_recycle=3600,     # Recycle connections after 1 hour
    pool_pre_ping=True,    # Test connections before using
)
```

### Backups

**Automated PostgreSQL Backups:**

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/fastauth_$TIMESTAMP.sql.gz"

# Create backup
pg_dump -U fastauth_user fastauth_prod | gzip > $BACKUP_FILE

# Keep only last 7 days
find $BACKUP_DIR -name "fastauth_*.sql.gz" -mtime +7 -delete

# Upload to S3 (optional)
aws s3 cp $BACKUP_FILE s3://your-backup-bucket/postgres/
```

**Cron job:**

```bash
# Run daily at 2 AM
0 2 * * * /path/to/backup.sh
```

## Deployment Platforms

### Docker

#### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run with Gunicorn
CMD ["gunicorn", "main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/fastauth
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=fastauth
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
```

### AWS EC2

#### Deploy with Gunicorn

```bash
# Install dependencies
sudo apt-get update
sudo apt-get install python3-pip python3-venv nginx

# Clone repository
git clone https://github.com/yourusername/your-app.git
cd your-app

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install application
pip install poetry
poetry install --no-dev

# Create systemd service
sudo nano /etc/systemd/system/fastauth.service
```

**fastauth.service:**

```ini
[Unit]
Description=FastAuth Application
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/your-app
Environment="PATH=/home/ubuntu/your-app/venv/bin"
EnvironmentFile=/home/ubuntu/your-app/.env
ExecStart=/home/ubuntu/your-app/venv/bin/gunicorn \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    -b 0.0.0.0:8000 \
    main:app

Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Start service
sudo systemctl daemon-reload
sudo systemctl start fastauth
sudo systemctl enable fastauth
```

### AWS ECS/Fargate

```json
{
  "family": "fastauth",
  "taskRoleArn": "arn:aws:iam::123456789:role/ecsTaskRole",
  "networkMode": "awsvpc",
  "containerDefinitions": [
    {
      "name": "fastauth-app",
      "image": "your-ecr-repo/fastauth:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://..."
        }
      ],
      "secrets": [
        {
          "name": "JWT_SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:jwt-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/fastauth",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ],
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512"
}
```

### Heroku

```bash
# Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login
heroku login

# Create app
heroku create your-app-name

# Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Set environment variables
heroku config:set JWT_SECRET_KEY=$(openssl rand -hex 32)
heroku config:set REQUIRE_EMAIL_VERIFICATION=true

# Deploy
git push heroku main

# Run migrations
heroku run alembic upgrade head
```

**Procfile:**

```
web: gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

### Vercel/Railway

These platforms work well with FastAPI but require serverless-friendly configurations.

## Security Hardening

### HTTPS/TLS

**Always use HTTPS in production.**

#### Let's Encrypt with Nginx

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal (cron)
sudo certbot renew --dry-run
```

#### Nginx SSL Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

### CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://www.yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600,
)
```

### Rate Limiting

FastAuth includes built-in rate limiting, but consider additional layers:

**Nginx rate limiting:**

```nginx
# Define rate limit zone
limit_req_zone $binary_remote_addr zone=auth:10m rate=10r/s;

location /auth {
    limit_req zone=auth burst=20 nodelay;
    proxy_pass http://localhost:8000;
}
```

**CloudFlare:** Configure rate limiting rules in CloudFlare dashboard.

### Security Headers

```python
from fastapi import FastAPI
from starlette.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI()

# Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["yourdomain.com", "www.yourdomain.com"]
)

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

## Monitoring and Logging

### Application Logging

```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            'app.log',
            maxBytes=10485760,  # 10MB
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Log authentication events
@app.post("/auth/login")
def login(payload: LoginRequest):
    try:
        result = authenticate_user(...)
        logger.info(f"User login successful: {payload.email}")
        return result
    except InvalidCredentialsError:
        logger.warning(f"Failed login attempt: {payload.email}")
        raise
```

### Error Tracking with Sentry

```bash
pip install sentry-sdk[fastapi]
```

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="https://your-dsn@sentry.io/project-id",
    integrations=[FastApiIntegration()],
    environment="production",
    traces_sample_rate=0.1,  # 10% of transactions
)
```

### Health Checks

```python
@app.get("/health")
def health_check():
    # Check database connection
    try:
        with Session(engine) as session:
            session.exec(select(1))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "version": "1.0.0"
    }
```

### Monitoring with Prometheus

```bash
pip install prometheus-fastapi-instrumentator
```

```python
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app)
```

## Performance Optimization

### Caching

**Redis caching for sessions:**

```python
from redis import asyncio as aioredis

redis = await aioredis.from_url("redis://localhost")

# Cache user sessions
await redis.setex(f"session:{session_id}", 3600, user_data)
cached = await redis.get(f"session:{session_id}")
```

### Database Optimization

**Indexes:**

```python
from sqlmodel import Field, Index

class User(SQLModel, table=True):
    email: str = Field(index=True, unique=True)
    created_at: datetime = Field(index=True)

    __table_args__ = (
        Index('idx_user_email_active', 'email', 'is_active'),
    )
```

**Query optimization:**

```python
# Use select() for efficient querying
from sqlmodel import select

# Good - only fetch needed columns
statement = select(User.id, User.email).where(User.is_active == True)

# Avoid - fetches all columns
users = session.exec(select(User)).all()
```

### Load Balancing

**Nginx upstream:**

```nginx
upstream fastauth_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

server {
    location / {
        proxy_pass http://fastauth_backend;
    }
}
```

### Gunicorn Workers

```bash
# Calculate workers: (2 x CPU cores) + 1
gunicorn -w 9 -k uvicorn.workers.UvicornWorker main:app
```

## Continuous Deployment

### GitHub Actions

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

      - name: Deploy to EC2
        env:
          SSH_PRIVATE_KEY: ${{ secrets.SSH_PRIVATE_KEY }}
        run: |
          echo "$SSH_PRIVATE_KEY" > key.pem
          chmod 600 key.pem
          ssh -i key.pem ubuntu@your-server.com << 'EOF'
            cd /app
            git pull origin main
            source venv/bin/activate
            pip install -r requirements.txt
            sudo systemctl restart fastauth
          EOF
```

## Troubleshooting

### Common Production Issues

**High memory usage:**
- Reduce Gunicorn workers
- Enable connection pooling
- Add caching layer

**Slow database queries:**
- Add database indexes
- Use connection pooling
- Enable query logging
- Consider read replicas

**OAuth redirect errors:**
- Verify redirect URIs match exactly
- Ensure HTTPS is configured
- Check CORS settings

## Checklist Before Going Live

- [ ] All secrets in environment variables/secrets manager
- [ ] HTTPS enabled with valid certificate
- [ ] Database backups automated
- [ ] Monitoring and alerting configured
- [ ] Error tracking (Sentry) set up
- [ ] Load testing completed
- [ ] Security audit passed
- [ ] Documentation updated
- [ ] Rollback plan documented
- [ ] Team trained on deployment process

---

**Your FastAuth application is now production-ready!** 🚀
