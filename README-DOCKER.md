# Panacare Healthcare Backend - Docker Setup

This guide explains how to run the Panacare Healthcare Backend Django application using Docker and Docker Compose.

## Prerequisites

Before you begin, ensure you have the following installed:

- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)
- Git (for cloning the repository)

### Verify Installation

```bash
docker --version
docker-compose --version
```

## Project Structure

```
panacare_healthcare_backend/
├── Dockerfile                 # Multi-stage Docker build configuration
├── docker-compose.yml         # Service orchestration
├── docker-entrypoint.sh       # Container startup script
├── .dockerignore             # Files excluded from Docker build
├── .env.example              # Environment variables template
├── requirements.txt          # Python dependencies
├── manage.py                 # Django management script
├── panacare/                 # Main Django project
├── users/                    # User management app
├── doctors/                  # Doctor profiles app
├── healthcare/               # Healthcare facilities app
└── [other Django apps...]
```

## Initial Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Panacare_healthcare_Backend_Django
```

### 2. Create Environment File

Copy the example environment file and customize it with your settings:

```bash
cp .env.example .env
```

Edit the `.env` file with your preferred text editor:

```bash
nano .env
# or
vim .env
```

**Important environment variables to configure:**

- `SECRET_KEY`: Generate a strong secret key for production
- `DEBUG`: Set to `False` for production
- `POSTGRES_PASSWORD`: Change the default password
- Email settings (for SMTP)
- Twilio credentials (for video consultations)
- PesaPal credentials (for payments)
- Firebase credentials path

### 3. Add Firebase Service Account

Place your Firebase service account JSON file in the project root:

```bash
cp /path/to/your/firebase-service-account.json ./
```

The file should be named `firebase-service-account.json` by default, or update the path in `.env`:

```env
FIREBASE_SERVICE_ACCOUNT_PATH=/app/firebase-service-account.json
```

## Building and Running

### Build Docker Images

Build the Docker images (this may take a few minutes the first time):

```bash
docker-compose build
```

For a clean build without cache:

```bash
docker-compose build --no-cache
```

### Start Services

Start all services in detached mode (background):

```bash
docker-compose up -d
```

Or start with logs visible:

```bash
docker-compose up
```

### Check Service Status

Verify that both services are running:

```bash
docker-compose ps
```

You should see:
- `panacare_db` - Status: Up (healthy)
- `panacare_web` - Status: Up

### View Logs

Watch logs in real-time:

```bash
# All services
docker-compose logs -f

# Web service only
docker-compose logs -f web

# Database service only
docker-compose logs -f db
```

## Initial Database Setup

The `docker-entrypoint.sh` script automatically runs database migrations when the container starts. However, you may need to perform additional setup:

### Create a Superuser

```bash
docker-compose exec web python manage.py createsuperuser
```

Follow the prompts to create an admin account.

### Create Default Roles (Optional)

```bash
docker-compose exec web python manage.py shell
```

Then in the Python shell:

```python
from users.models import Role

roles = ['Admin', 'Doctor', 'Patient', 'CHP', 'Staff']
for role_name in roles:
    Role.objects.get_or_create(
        name=role_name,
        defaults={'description': f'{role_name} role'}
    )
print("Roles created successfully!")
exit()
```

### Load Sample Data (Optional)

If you have fixtures:

```bash
docker-compose exec web python manage.py loaddata your_fixture_file.json
```

## Accessing the Application

Once the services are running, you can access:

- **Django API**: http://localhost:8000
- **Django Admin**: http://localhost:8000/admin
- **Swagger API Documentation**: http://localhost:8000/swagger/
- **ReDoc API Documentation**: http://localhost:8000/redoc/
- **PostgreSQL Database**: localhost:5432

### Database Connection (from host)

You can connect to the PostgreSQL database using any database client:

- **Host**: localhost
- **Port**: 5432
- **Database**: panacare_db
- **User**: panacare
- **Password**: (from your `.env` file)

Example using `psql`:

```bash
psql -h localhost -U panacare -d panacare_db
```

Or using Docker:

```bash
docker-compose exec db psql -U panacare -d panacare_db
```

## Common Commands

### Stop Services

```bash
docker-compose down
```

### Stop and Remove Volumes (CAUTION: Deletes database data)

```bash
docker-compose down -v
```

### Restart Services

```bash
docker-compose restart
```

### Restart Specific Service

```bash
docker-compose restart web
```

### Execute Django Management Commands

```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create migrations
docker-compose exec web python manage.py makemigrations

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Access Django shell
docker-compose exec web python manage.py shell

# Run tests
docker-compose exec web python manage.py test

# Check for issues
docker-compose exec web python manage.py check
```

### Access Container Shell

```bash
# Bash shell in web container
docker-compose exec web bash

# PostgreSQL shell
docker-compose exec db psql -U panacare -d panacare_db
```

### Rebuild After Changes

If you modify `requirements.txt` or other Docker configuration:

```bash
docker-compose down
docker-compose build
docker-compose up -d
```

## Development Workflow

### Hot Reload

The development setup includes hot-reload functionality. Any changes you make to Python files will automatically reload the Django development server.

1. Edit a Python file in your project
2. Save the file
3. Check the logs to see Django detecting the change:

```bash
docker-compose logs -f web
```

You should see output like:
```
Watching for file changes with StatReloader
Performing system checks...
```

### Running Migrations

After modifying models:

```bash
# Create migration files
docker-compose exec web python manage.py makemigrations

# Apply migrations
docker-compose exec web python manage.py migrate
```

### Adding New Dependencies

1. Add the package to `requirements.txt`
2. Rebuild the Docker image:

```bash
docker-compose build web
docker-compose up -d
```

## Troubleshooting

### Issue: Database Connection Error

**Symptom:**
```
django.db.utils.OperationalError: could not connect to server
```

**Solutions:**
1. Check if PostgreSQL is running:
   ```bash
   docker-compose ps db
   ```

2. Check PostgreSQL logs:
   ```bash
   docker-compose logs db
   ```

3. Verify `DB_HOST=db` in your `.env` file (not `localhost`)

4. Wait for health check:
   ```bash
   docker-compose ps
   ```
   The `db` service should show as "healthy"

### Issue: Permission Denied on Media Files

**Symptom:**
```
PermissionError: [Errno 13] Permission denied: '/app/media/...'
```

**Solutions:**
1. Fix volume permissions:
   ```bash
   docker-compose exec web chown -R django:django /app/media
   ```

2. Or adjust permissions:
   ```bash
   docker-compose exec web chmod -R 755 /app/media
   ```

### Issue: Static Files Not Found

**Symptom:**
```
404 on /static/admin/...
```

**Solutions:**
1. Collect static files:
   ```bash
   docker-compose exec web python manage.py collectstatic --noinput
   ```

2. Verify `STATIC_ROOT` in settings.py

3. Check WhiteNoise middleware is enabled

### Issue: Firebase Initialization Error

**Symptom:**
```
FileNotFoundError: firebase-service-account.json
```

**Solutions:**
1. Ensure `firebase-service-account.json` exists in project root
2. Check volume mount in `docker-compose.yml`
3. Verify `FIREBASE_SERVICE_ACCOUNT_PATH` in `.env`:
   ```env
   FIREBASE_SERVICE_ACCOUNT_PATH=/app/firebase-service-account.json
   ```

### Issue: Code Changes Not Reflecting

**Symptom:**
Changes to Python files don't appear in the running application

**Solutions:**
1. Check volume mount exists:
   ```bash
   docker-compose exec web ls -la /app
   ```

2. Restart Django server:
   ```bash
   docker-compose restart web
   ```

3. Check for Python syntax errors in logs:
   ```bash
   docker-compose logs web
   ```

### Issue: Port Already in Use

**Symptom:**
```
Error: bind: address already in use
```

**Solutions:**
1. Check what's using the port:
   ```bash
   sudo lsof -i :8000
   # or
   sudo lsof -i :5432
   ```

2. Stop the conflicting service or change the port in `docker-compose.yml`

### Issue: Out of Disk Space

**Symptom:**
```
no space left on device
```

**Solutions:**
1. Clean up Docker resources:
   ```bash
   docker system prune -f
   docker volume prune -f
   ```

2. Remove unused images:
   ```bash
   docker image prune -a
   ```

## Performance Optimization

### Build Optimization

Use BuildKit for faster builds:

```bash
DOCKER_BUILDKIT=1 docker-compose build
```

### Parallel Builds

Build multiple services in parallel:

```bash
docker-compose build --parallel
```

### Reduce Build Context

The `.dockerignore` file is configured to exclude unnecessary files. Verify it's working:

```bash
# Check build context size
docker-compose build web 2>&1 | grep "Sending build context"
```

## Data Persistence

### Database Backup

Backup the PostgreSQL database:

```bash
docker-compose exec db pg_dump -U panacare panacare_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore Database

```bash
docker-compose exec -T db psql -U panacare panacare_db < backup_20240101_120000.sql
```

### Media Files Backup

```bash
docker cp $(docker-compose ps -q web):/app/media ./media_backup
```

### Volume Management

List all volumes:

```bash
docker volume ls | grep panacare
```

Inspect a volume:

```bash
docker volume inspect panacare_postgres_data
```

## Production Considerations

This Docker setup is optimized for development. For production deployment, consider:

1. **Environment Variables:**
   - Set `DEBUG=False`
   - Use a strong `SECRET_KEY` (minimum 50 characters)
   - Configure proper `ALLOWED_HOSTS`
   - Restrict `CORS_ALLOWED_ORIGINS`

2. **Database:**
   - Use managed PostgreSQL service (AWS RDS, Railway, etc.)
   - Configure connection pooling
   - Enable SSL connections

3. **Web Server:**
   - Switch from `runserver` to Gunicorn with multiple workers
   - Add Nginx as reverse proxy
   - Configure SSL/TLS certificates

4. **Static Files:**
   - Use CDN or cloud storage (S3, GCS)
   - Or keep WhiteNoise (works well for small to medium apps)

5. **Media Files:**
   - Use cloud storage (S3, GCS, Cloudinary)
   - Don't store in containers (use external volume or storage service)

6. **Security:**
   - Use Docker secrets or external vault for sensitive data
   - Run security scans on images
   - Keep base images updated

7. **Monitoring:**
   - Implement health check endpoints
   - Add logging aggregation
   - Set up monitoring and alerts

8. **Example Production Command:**
   ```bash
   # In Dockerfile, change CMD to:
   CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "panacare.wsgi:application"]
   ```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Django Documentation](https://docs.djangoproject.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## Support

If you encounter issues not covered in this guide:

1. Check the application logs: `docker-compose logs -f`
2. Review the Django settings in `panacare/settings.py`
3. Verify all environment variables are set correctly in `.env`
4. Consult the project's main README for application-specific information

## Quick Reference

```bash
# Start everything
docker-compose up -d

# Stop everything
docker-compose down

# View logs
docker-compose logs -f web

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Access Django shell
docker-compose exec web python manage.py shell

# Rebuild after changes
docker-compose build && docker-compose up -d

# Clean restart (careful - removes data)
docker-compose down -v && docker-compose up -d

# Database backup
docker-compose exec db pg_dump -U panacare panacare_db > backup.sql

# Check service status
docker-compose ps
```
