#!/bin/bash
# OmniTrust AI - Production Deployment Guide

cat << 'EOF'

╔═════════════════════════════════════════════════════════════════════╗
║                 OmniTrust AI - Production Deployment              ║
║                        Complete Guide 2024                         ║
╚═════════════════════════════════════════════════════════════════════╝

## Table of Contents
1. Pre-Deployment Checklist
2. Infrastructure Setup
3. Database Configuration
4. Application Deployment
5. Security Hardening
6. Monitoring & Alerting
7. Scaling Considerations
8. Disaster Recovery

## 1. PRE-DEPLOYMENT CHECKLIST

### Prerequisites
□ Kubernetes cluster or compute instances ready
□ PostgreSQL 15+ instance provisioned
□ Redis 7+ instance provisioned
□ MinIO or S3 bucket configured
□ Elasticsearch 8+ cluster ready
□ Domain name and SSL certificate
□ Container registry access
□ Monitoring tools deployed

### Code & Security
□ All tests passing (pytest coverage > 80%)
□ Code review completed
□ Security scan run (dependabot, trivy)
□ Environment variables configured
□ Database backups configured
□ Log aggregation configured

## 2. INFRASTRUCTURE SETUP

### Option A: Docker Compose (Single Server)

```bash
# Prerequisites
docker --version  # 20.10+
docker-compose --version  # 2.0+

# Setup
git clone <repo> /opt/omnitrust
cd /opt/omnitrust/backend

# Configure environment
cp .env.example .env.prod
# Edit with production values

# Deploy
docker-compose -f docker-compose.yml up -d

# Monitor
docker-compose logs -f app
docker-compose ps
```

### Option B: Kubernetes

```bash
# Create namespace
kubectl create namespace omnitrust-prod

# Create secrets
kubectl create secret generic app-secrets \
  --from-literal=database-url="postgresql://..." \
  --from-literal=secret-key="..." \
  -n omnitrust-prod

# Deploy
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Check status
kubectl -n omnitrust-prod get pods
kubectl -n omnitrust-prod logs -f deployment/omnitrust-app
```

### Option C: AWS ECS

```bash
# Push image to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com
docker tag omnitrust:latest <account>.dkr.ecr.<region>.amazonaws.com/omnitrust:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/omnitrust:latest

# Create ECS task definition and service
aws ecs create-service --cluster omnitrust-prod --service-name omnitrust-api \
  --task-definition omnitrust-app \
  --desired-count 3 \
  --load-balancers targetGroupArn=<arn>,containerName=app,containerPort=8000
```

## 3. DATABASE CONFIGURATION

### PostgreSQL Setup

```sql
-- Create database user
CREATE ROLE omniadmin WITH LOGIN PASSWORD 'secure_password_here';
ALTER ROLE omniadmin WITH CREATEDB;

-- Create database
CREATE DATABASE omnitrust_db OWNER omniadmin;

-- Create extensions
\c omnitrust_db
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For full-text search

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE omnitrust_db TO omniadmin;
```

### Backup Configuration

```bash
# Automated daily backup
0 2 * * * pg_dump -U omniadmin -d omnitrust_db > /backups/omnitrust_$(date +\%Y\%m\%d).sql

# Backup to S3
aws s3 cp /backups/omnitrust_*.sql s3://omnitrust-backups/
```

### Connection Pooling

```
# PgBouncer config
[databases]
omnitrust_db = host=db.example.com port=5432 dbname=omnitrust_db user=omniadmin password=xxx

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
min_pool_size = 10
```

## 4. APPLICATION DEPLOYMENT

### Multi-Instance Setup

```bash
# Load Balancer Configuration (Nginx)
upstream omnitrust_backend {
    server app1:8000 weight=1;
    server app2:8000 weight=1;
    server app3:8000 weight=1;
}

server {
    listen 443 ssl http2;
    server_name api.omnitrust.ai;

    ssl_certificate /etc/ssl/certs/omnitrust.crt;
    ssl_certificate_key /etc/ssl/private/omnitrust.key;

    location / {
        proxy_pass http://omnitrust_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Rate limiting
        limit_req zone=api burst=100 nodelay;
    }

    location /metrics {
        auth_basic "Metrics";
        auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://omnitrust_backend;
    }
}
```

### Celery Scaling

```bash
# Run multiple worker instances
celery -A app.workers.celery_app worker --loglevel=info -n worker1@%h -Q default,high_priority &
celery -A app.workers.celery_app worker --loglevel=info -n worker2@%h -Q default &
celery -A app.workers.celery_app worker --loglevel=info -n worker3@%h -Q low_priority &

# Run Beat (scheduler) on single instance
celery -A app.workers.celery_app beat --loglevel=info
```

## 5. SECURITY HARDENING

### Environment Secrets Management

```bash
# Using SealedSecrets (Kubernetes)
echo -n 'your-secret-key' | kubectl create secret generic app-secret \
  --dry-run=client --from-file=secret_key=/dev/stdin -o yaml | \
  kubeseal -f - > sealed_secret.yaml

# Using AWS Secrets Manager
aws secretsmanager create-secret --name omnitrust/db-password \
  --secret-string '{"password":"secure_password"}'

# Application reads at runtime
DATABASE_URL=$(aws secretsmanager get-secret-value --secret-id omnitrust/db-url | jq -r .SecretString)
```

### SSL/TLS Configuration

```bash
# Generate self-signed (development only)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365

# Use Let's Encrypt (production)
certbot certonly --standalone -d api.omnitrust.ai
```

### Network Security

- Restrict PostgreSQL access to app servers only
- Restrict Redis access to celery workers only
- Use VPC/Security Groups to isolate services
- Enable WAF for DDoS protection
- Regular security audits and updates

## 6. MONITORING & ALERTING

### Prometheus Scrape Configuration

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

alert_rules:
  - /etc/prometheus/rules.yml

scrape_configs:
  - job_name: 'omnitrust-app'
    static_configs:
      - targets: ['app:8001']

  - job_name: 'postgres'
    static_configs:
      - targets: ['db_exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis_exporter:9121']
```

### Key Alerts

```yaml
groups:
  - name: omnitrust

    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[1m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"

      - alert: DatabaseConnectionPoolExhausted
        expr: db_connection_pool_utilization > 0.9
        for: 1m
        annotations:
          summary: "DB connection pool nearly full"

      - alert: CeleryQueueDepthHigh
        expr: celery_queue_length > 10000
        for: 5m
        annotations:
          summary: "Celery task queue backing up"

      - alert: DiskSpaceWarning
        expr: (node_filesystem_avail / node_filesystem_size) < 0.1
        for: 1m
        annotations:
          summary: "Low disk space warning"
```

## 7. SCALING CONSIDERATIONS

### Horizontal Scaling

1. **Application Tier**
   - Run multiple app instances behind load balancer
   - Use auto-scaling groups (target: 70% CPU)
   - Consider max 3-5 instances per region

2. **Database Tier**
   - PostgreSQL read replicas for read-heavy operations
   - Connection pooling (PgBouncer)
   - Consider sharding for very large deployments

3. **Cache Tier**
   - Redis Cluster for high availability
   - Use persistence (RDB + AOF)
   - Master-slave replication

4. **Queue Tier**
   - Multiple Celery workers
   - Dedicated worker nodes for high-priority tasks
   - Queue sharding by task type

### Performance Optimization

```python
# Database optimization
DATABASE_POOL_SIZE=50  # Increased for high concurrency
DATABASE_MAX_OVERFLOW=10
DATABASE_ECHO=False  # Disable in production

# Caching strategy
CACHE_TTL_DEFAULT=300  # 5 minutes
CACHE_TTL_EVALUATIONS=3600  # 1 hour
CACHE_TTL_POLICIES=1800  # 30 minutes

# Rate limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_PER_MINUTE=60  # Per API key
RATE_LIMIT_BURST=100
```

## 8. DISASTER RECOVERY

### Backup Strategy

```bash
# Daily database backup
0 2 * * * /usr/local/bin/backup-db.sh

# Weekly full backup to remote storage
0 3 * * 0 /usr/local/bin/backup-full.sh

# Test restore monthly
0 4 1 * * /usr/local/bin/test-restore.sh
```

### Failover Procedures

1. **Database Failover**
   - Update connection string to replica
   - Promote replica to primary
   - Repoint backups

2. **Application Failover**
   - Health checks detect down instance
   - Load balancer routes away
   - Auto-scaling spins up replacement

3. **Cache Failover**
   - Redis sentinel monitors primary
   - Auto-failover to replica
   - Minimal data loss with AOF persistence

### RTO/RPO Targets

- **Database**: RTO 5 minutes, RPO < 5 minutes
- **Application**: RTO 2 minutes, RPO N/A (stateless)
- **Cache**: RTO 1 minute, RPO < 1 minute

---

## Deployment Checklist

□ All services running and healthy
□ Database migrations completed
□ SSL certificates valid
□ Monitoring and alerts functional
□ Backup tests successful
□ Load testing completed (>1000 req/s)
□ Security audit passed
□ Documentation updated
□ Team trained on runbooks
□ On-call rotation established

For more information, see README.md

EOF
