# Troubleshooting Guide

## Common Issues and Solutions

### NumPy 2.0 Compatibility Error

**Error Message:**
```
AttributeError: `np.float_` was removed in the NumPy 2.0 release. Use `np.float64` instead.
```

**Cause:**
ChromaDB 0.4.22 uses deprecated NumPy types that were removed in NumPy 2.0.

**Solution:**
The `requirements.txt` file has been updated to pin NumPy to a version before 2.0:
```
numpy<2.0.0  # ChromaDB 0.4.22 is not compatible with NumPy 2.0
```

After updating, rebuild the Docker container:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Environment Variable Issues

**Error:** Missing ANTHROPIC_API_KEY

**Solution:**
1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your Anthropic API key:
   ```env
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```

3. Restart the container:
   ```bash
   docker-compose restart
   ```

### Vector Store Empty Error

**Error:** "Vector store is empty. Please call /index endpoint first."

**Solution:**
This is expected on first run. Index the paper by calling:
```bash
curl -X POST http://localhost:8000/index
```

This will:
- Download the paper from arXiv
- Extract and chunk the text
- Generate embeddings
- Store in ChromaDB

The indexing process takes 30-60 seconds on first run.

### Port Already in Use

**Error:** Port 8000 is already allocated

**Solution:**
Either stop the conflicting service or change the port in `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Use port 8001 instead
```

### Docker Build Failures

**Error:** Various build errors

**Solution:**
1. Clean up Docker:
   ```bash
   docker-compose down -v
   docker system prune -f
   ```

2. Rebuild from scratch:
   ```bash
   docker-compose build --no-cache
   docker-compose up -d
   ```

### Slow Response Times

**Issue:** Questions take a long time to answer

**Possible Causes and Solutions:**

1. **First request after startup:** The embedding model needs to warm up. Subsequent requests will be faster.

2. **Too many context chunks:** Reduce `TOP_K_RESULTS` in `.env`:
   ```env
   TOP_K_RESULTS=3  # Default is 5
   ```

3. **Large max tokens:** Reduce `MAX_TOKENS` in `.env`:
   ```env
   MAX_TOKENS=2048  # Default is 4096
   ```

### Memory Issues

**Error:** Container killed or OOM errors

**Solution:**
Increase Docker memory allocation:
- Docker Desktop: Settings → Resources → Memory (set to at least 4GB)

Or reduce model size by using a smaller embedding model in `.env`:
```env
EMBEDDING_MODEL=all-MiniLM-L6-v2  # Smaller and faster
```

## Checking Logs

View real-time logs:
```bash
docker-compose logs -f
```

View last 50 log lines:
```bash
docker-compose logs --tail=50
```

## Health Checks

Check if the service is running:
```bash
curl http://localhost:8000/health
```

Check system status:
```bash
curl http://localhost:8000/status
```

## Testing the System

Run the integration test script:
```bash
python test_system.py
```

This will:
1. Check health
2. Check status
3. Index the paper (if needed)
4. Ask sample questions
5. Display results

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Getting Help

If issues persist:
1. Check logs: `docker-compose logs -f`
2. Verify environment variables: `docker-compose config`
3. Check Docker resources: `docker stats`
4. Review this troubleshooting guide
5. Open an issue in the repository
