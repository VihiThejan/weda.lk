# DEPLOYMENT GUIDE - Hybrid Recommendation System

## Quick Deployment Steps

### 1. Local Development

```bash
# Step 1: Install dependencies
pip install -r requirements.txt

# Step 2: Download BERT model (if not already done)
python download_model.py

# Step 3: Run Jupyter notebook to process data
jupyter notebook hybrid_recommendation_system.ipynb

# Step 4: Test Flask API
python app.py

# Step 5: Test with curl
curl http://localhost:5000/health
```

### 2. Docker Deployment

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Precompute embeddings
RUN python -c "from hybrid_recommendation_system import *" || true

# Expose port
EXPOSE 5000

# Run Flask app
CMD ["python", "app.py"]
```

**Build and Run:**
```bash
docker build -t recommender:latest .
docker run -d -p 5000:5000 \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/data:/app/data \
  --name recommender \
  recommender:latest

# Check logs
docker logs -f recommender
```

### 3. Production Deployment (Linux Server)

#### Using Gunicorn + Nginx

**Install Gunicorn:**
```bash
pip install gunicorn gevent
```

**Create systemd service file** (`/etc/systemd/system/recommender.service`):
```ini
[Unit]
Description=Hybrid Recommendation System
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/opt/recommender
ExecStart=/usr/bin/python -m gunicorn -w 4 -b 127.0.0.1:8000 app:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
KillSignal=SIGTERM
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Start service:**
```bash
sudo systemctl start recommender
sudo systemctl enable recommender
sudo systemctl status recommender
```

**Nginx configuration** (`/etc/nginx/sites-enabled/recommender`):
```nginx
server {
    listen 80;
    server_name recommender.example.com;

    # SSL setup (recommended)
    listen 443 ssl;
    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-running requests
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint (fast, no timeout)
    location /health {
        proxy_pass http://127.0.0.1:8000;
        access_log off;
    }
}
```

**Restart Nginx:**
```bash
sudo nginx -t
sudo systemctl restart nginx
```

### 4. AWS Deployment

**Option A: EC2 + Load Balancer**

```bash
# Launch EC2 instance (t3.large or larger)
# AMI: Ubuntu 22.04 LTS

# Connect to instance
ssh -i key.pem ubuntu@instance-ip

# Setup
sudo apt update && sudo apt install -y python3-pip python3-venv
git clone https://github.com/yourusername/recommender.git
cd recommender
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start service
gunicorn -w 4 -b 0.0.0.0:5000 app:app &
```

**Option B: AWS Lambda + API Gateway**

```python
# For Lambda, wrap app.py with Zappa
pip install zappa

# Deploy
zappa init
zappa deploy production
```

### 5. Google Cloud Deployment

```bash
# Create Cloud Run service
gcloud run deploy recommender \
  --source . \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 1 \
  --timeout 60

# Set environment variables
gcloud run services update recommender \
  --set-env-vars="MODEL_CACHE=/workspace/models"
```

### 6. Performance Tuning

#### Worker Configuration
```bash
# For CPU-intensive tasks (BERT encoding)
gunicorn -w 2 -b 0.0.0.0:5000 app:app

# For I/O-intensive tasks (database queries)
gunicorn -w 8 -b 0.0.0.0:5000 app:app

# With async workers
gunicorn -w 4 -k gevent -b 0.0.0.0:5000 app:app
```

#### Caching Strategy
```python
# Redis caching for queries
import redis
cache = redis.Redis(host='localhost', port=6379)

def cached_recommend(query, user_id):
    key = f"rec:{user_id}:{query}"
    cached = cache.get(key)
    if cached:
        return json.loads(cached)
    
    result = recommender.recommend(query, user_id)
    cache.setex(key, 3600, json.dumps(result))  # 1 hour TTL
    return result
```

### 7. Monitoring & Logging

**Setup Prometheus monitoring:**
```python
from prometheus_client import Counter, Histogram, generate_latest

recommendation_counter = Counter('recommendations_total', 'Total recommendations')
recommendation_latency = Histogram('recommendation_latency_seconds', 'Recommendation latency')

@app.route('/metrics', methods=['GET'])
def metrics():
    return generate_latest()
```

**ELK Stack logging:**
```bash
# Install Filebeat
curl -L -O https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-8.0.0-linux-x86_64.tar.gz
tar xzvf filebeat-8.0.0-linux-x86_64.tar.gz
```

### 8. Load Testing

```bash
# Using Apache Bench
ab -n 1000 -c 10 -p data.json \
  -T "application/json" \
  http://localhost:5000/health

# Using wrk
wrk -t4 -c100 -d30s \
  -s script.lua \
  http://localhost:5000/recommend

# Using Locust
locust -f locustfile.py --host=http://localhost:5000
```

### 9. Database Integration (Optional)

```python
# SQLAlchemy example for storing recommendations
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class Recommendation(Base):
    __tablename__ = 'recommendations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    provider_id = Column(Integer)
    query = Column(String)
    score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

# Log recommendations
engine = create_engine('postgresql://user:password@localhost/recommender')
Session = sessionmaker(bind=engine)
session = Session()

recommendation = Recommendation(
    user_id=123,
    provider_id=42,
    query="web development",
    score=0.8234
)
session.add(recommendation)
session.commit()
```

### 10. Scaling Strategies

**Horizontal Scaling (Multiple instances):**
```bash
# Start multiple API instances
for i in {1..4}; do
  python app.py --port $((5000+i)) &
done

# Use load balancer (Nginx, HAProxy)
# Distribute requests round-robin
```

**Vertical Scaling:**
- Increase CPU: 2→8 cores
- Increase RAM: 4GB→16GB
- Add GPU: Use NVIDIA GPU for BERT inference

**Caching:**
- Cache embeddings (save 80% latency)
- Cache frequent queries (Redis)
- Cache provider metadata

### 11. Backup & Recovery

```bash
# Backup models
tar -czf models_backup.tar.gz models/

# Backup precomputed embeddings
aws s3 cp embeddings.pkl s3://bucket/backups/

# Backup database
pg_dump recommender_db > backup.sql
```

### 12. Monitoring Checklist

- [ ] API response time < 200ms
- [ ] Error rate < 1%
- [ ] CPU usage < 80%
- [ ] Memory usage < 75%
- [ ] Disk space > 20% free
- [ ] Model updates every 24 hours
- [ ] Database backups daily
- [ ] Log retention 30 days

---

**Ready to deploy?** Choose your deployment option above and follow the steps!
