# Getting Started with the Improved Platform Leveling System

Welcome! This guide will get you up and running with all the new improvements.

## 🎉 What's New

Your Platform Leveling System now includes:
- ✅ **Security**: API authentication, CORS protection, input validation, rate limiting
- ✅ **Performance**: Redis caching, optimized calculations
- ✅ **Reliability**: Error handling, structured logging, database persistence
- ✅ **Monitoring**: Prometheus metrics, health checks
- ✅ **DevOps**: Docker setup, CI/CD pipeline, automated testing

## 🚀 Quick Start (Recommended)

### Option 1: Docker Compose (Easiest)

```bash
# Start all services (Backend + Frontend + Redis)
docker-compose up

# The services will be available at:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Metrics: http://localhost:8000/metrics
```

That's it! Everything is configured and ready to use.

### Option 2: Manual Setup (For Development)

#### 1. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements-dev.txt

# The .env file is already configured, but you can customize it
nano .env

# Start the backend
python api.py
```

Backend will be available at `http://localhost:8000`

#### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm start
```

Frontend will be available at `http://localhost:3000`

#### 3. Optional: Redis (for caching)

```bash
# Install and start Redis
docker run -d -p 6379:6379 redis:7-alpine

# Or use your system's Redis
redis-server
```

## 📚 Using the New Features

### 1. API Authentication

If you need to use authenticated endpoints, include the API key:

```javascript
// In JavaScript
fetch('http://localhost:8000/config', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'dev-api-key-change-in-production'
  },
  body: JSON.stringify(newConfig)
});
```

```bash
# Using curl
curl -X POST http://localhost:8000/config \
  -H "X-API-Key: dev-api-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{"base_radius": 130}'
```

**Note:** The API key is in `.env` file. Change it for production!

### 2. Viewing Logs

```bash
# Structured JSON logs
tail -f backend/logs/api.log

# Error logs only
tail -f backend/logs/error.log

# In Docker
docker logs -f leveling-backend
```

### 3. Monitoring Metrics

Visit `http://localhost:8000/metrics` to see Prometheus metrics:
- Request counts
- Response times
- Error rates
- Cache hit rates

### 4. Health Checks

```bash
# Simple health check
curl http://localhost:8000/health

# Response includes service status:
{
  "status": "healthy",
  "version": "2.0.0",
  "environment": "development",
  "services": {
    "api": "healthy",
    "cache": "enabled",
    "database": "enabled",
    "cache_stats": {
      "enabled": true,
      "hit_rate": 85.5
    }
  }
}
```

### 5. Using the Cache

The cache is automatic! Repeated requests with the same parameters will be served from cache:

```bash
# First request - calculates and caches
curl -X POST http://localhost:8000/calculate \
  -H "Content-Type: application/json" \
  -d '{"x": 0, "y": 0, "z": 10, "roll": 5, "pitch": -3, "yaw": 0, "configuration": "6-3"}'

# Second request - served from cache (much faster!)
# Same request will include "cached": true in response
```

Cache TTL: 5 minutes (configurable in `backend/cache.py`)

### 6. Database Queries

All calculations are logged to the database:

```python
# Connect to database
from database import SessionLocal, CalculationLog

db = SessionLocal()

# Get recent calculations
recent = db.query(CalculationLog).order_by(CalculationLog.timestamp.desc()).limit(10).all()

# Get calculations for a specific configuration
config_calcs = db.query(CalculationLog).filter(
    CalculationLog.configuration == "6-3"
).all()

# Get invalid calculations
invalid = db.query(CalculationLog).filter(
    CalculationLog.result_valid == False
).all()
```

## 🧪 Running Tests

### Backend Tests

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov

# Run specific test
pytest tests/test_api.py::test_health_check -v
```

### Integration Tests

```bash
# Make sure backend is running first
python test-integration.py
```

### Frontend Tests (when available)

```bash
cd frontend
npm test
```

## 🔧 Configuration

### Backend Environment Variables

Edit `backend/.env`:

```bash
# Server
API_HOST=0.0.0.0
API_PORT=8000

# Security
API_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:3000,https://yourapp.com

# Features
REDIS_ENABLED=true
DATABASE_ENABLED=true
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# Environment
ENVIRONMENT=development  # development, staging, production
DEBUG=true
```

### Frontend Environment Variables

Edit `frontend/.env.development`:

```bash
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws
REACT_APP_ENV=development
REACT_APP_API_KEY=your-secret-key-here
```

## 📊 API Endpoints

### Public Endpoints (No Auth Required)

- `GET /` - Root endpoint
- `GET /health` - Detailed health check
- `GET /configurations` - List available configurations
- `GET /config` - Get current configuration
- `POST /calculate` - Calculate IK (rate limited)
- `POST /level` - Calculate leveling
- `GET /metrics` - Prometheus metrics
- `WS /ws` - WebSocket endpoint

### Protected Endpoints (Require API Key)

- `POST /config` - Update configuration

## 🐛 Troubleshooting

### Backend won't start

```bash
# Check if port 8000 is in use
lsof -i :8000

# Check Redis connection (if enabled)
redis-cli ping

# Check dependencies
pip install -r requirements-dev.txt
```

### Frontend can't connect to backend

1. Check backend is running: `curl http://localhost:8000/health`
2. Check CORS settings in `backend/.env`
3. Verify `REACT_APP_API_URL` in `frontend/.env.development`

### Cache not working

1. Check Redis is running: `redis-cli ping`
2. Verify `REDIS_ENABLED=true` in `backend/.env`
3. Check logs for Redis connection errors

### Rate limiting errors (429)

If you're seeing "Too Many Requests" errors:

1. Wait a minute (default: 60 requests/minute)
2. Increase limit in `.env`: `RATE_LIMIT_PER_MINUTE=120`
3. Disable in development: `RATE_LIMIT_ENABLED=false`

## 🚢 Deployment

### Production Checklist

Before deploying to production:

- [ ] Change `API_KEY` to a strong secret
- [ ] Update `CORS_ORIGINS` to your domain
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `DEBUG=false`
- [ ] Use PostgreSQL instead of SQLite (`DATABASE_URL=postgresql://...`)
- [ ] Enable HTTPS
- [ ] Set up proper logging aggregation
- [ ] Configure Prometheus monitoring
- [ ] Set up Redis persistence
- [ ] Review rate limits

### Environment Variables for Production

```bash
# backend/.env (production)
API_HOST=0.0.0.0
API_PORT=8000
API_KEY=<strong-random-key-here>
CORS_ORIGINS=https://yourapp.com
DATABASE_URL=postgresql://user:pass@host/db
REDIS_URL=redis://redis-host:6379
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
```

## 📖 Additional Documentation

- `README.md` - Main project documentation
- `RECOMMENDATIONS.md` - Detailed improvement guide
- `QUICK_IMPROVEMENTS.md` - Quick wins guide
- `ARCHITECTURE.md` - System architecture
- `IMPLEMENTATION_SUMMARY.md` - What was implemented
- `backend/README.md` - Backend-specific docs
- `frontend/README.md` - Frontend-specific docs

## 💡 Tips & Best Practices

1. **Use Docker for consistency**: `docker-compose up` gives you a complete environment
2. **Enable caching in production**: Significantly improves performance
3. **Monitor metrics**: Set up Grafana to visualize Prometheus metrics
4. **Check logs regularly**: Structured logs make debugging easy
5. **Run tests before deploying**: `pytest tests/ -v`
6. **Keep API keys secret**: Never commit `.env` files
7. **Use environment variables**: Never hardcode configuration

## 🆘 Getting Help

1. Check the logs: `backend/logs/api.log`
2. Run health check: `curl http://localhost:8000/health`
3. Review documentation in this repo
4. Check GitHub issues: https://github.com/thebibbi/LevelingSimulator/issues

## 🎓 Next Steps

Now that everything is set up:

1. **Explore the API**: Visit `http://localhost:8000/docs`
2. **Try the frontend**: Open `http://localhost:3000`
3. **Run the tests**: `pytest tests/ -v`
4. **Check metrics**: `http://localhost:8000/metrics`
5. **Review logs**: `tail -f backend/logs/api.log`

**Happy coding! 🚀**
