#!/bin/bash

# Production Deployment Script for Panacare Healthcare Backend
# This script helps you deploy the application to production

set -e  # Exit on error

echo "======================================"
echo "Panacare Production Deployment Script"
echo "======================================"
echo ""

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo "Error: .env.production file not found!"
    echo "Please create it from .env.production.example:"
    echo "  cp .env.production.example .env.production"
    echo "  nano .env.production"
    exit 1
fi

# Check if firebase-service-account.json exists
if [ ! -f firebase-service-account.json ]; then
    echo "Warning: firebase-service-account.json not found!"
    echo "Make sure to add your production Firebase credentials."
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Function to display menu
show_menu() {
    echo ""
    echo "Select deployment action:"
    echo "1) Initial deployment (build + start)"
    echo "2) Update deployment (pull + rebuild + restart)"
    echo "3) Run database migrations"
    echo "4) Create superuser"
    echo "5) Collect static files"
    echo "6) View logs"
    echo "7) Check status"
    echo "8) Backup database"
    echo "9) Stop services"
    echo "0) Exit"
    echo ""
}

# Function for initial deployment
initial_deploy() {
    echo "Starting initial deployment..."

    # Set Docker API version if needed
    export DOCKER_API_VERSION=1.44

    # Build images
    echo "Building Docker images..."
    docker compose -f docker-compose.prod.yml build

    # Start services
    echo "Starting services..."
    docker compose -f docker-compose.prod.yml up -d

    # Wait for database
    echo "Waiting for database to be ready..."
    sleep 10

    # Run migrations
    echo "Running database migrations..."
    docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate

    # Collect static files
    echo "Collecting static files..."
    docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

    echo ""
    echo "✅ Initial deployment complete!"
    echo ""
    echo "Next steps:"
    echo "1. Create a superuser: ./deploy-production.sh (option 4)"
    echo "2. Set up SSL certificate (see PRODUCTION-DEPLOYMENT.md)"
    echo "3. Configure your domain DNS"
    echo ""
}

# Function to update deployment
update_deploy() {
    echo "Updating deployment..."

    export DOCKER_API_VERSION=1.44

    # Pull latest code
    echo "Pulling latest code from git..."
    git pull origin main

    # Rebuild images
    echo "Rebuilding Docker images..."
    docker compose -f docker-compose.prod.yml build

    # Restart services
    echo "Restarting services..."
    docker compose -f docker-compose.prod.yml up -d

    # Run migrations
    echo "Running database migrations..."
    docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate

    # Collect static files
    echo "Collecting static files..."
    docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

    echo "✅ Deployment updated!"
}

# Function to run migrations
run_migrations() {
    echo "Running database migrations..."
    export DOCKER_API_VERSION=1.44
    docker compose -f docker-compose.prod.yml exec web python manage.py migrate
    echo "✅ Migrations complete!"
}

# Function to create superuser
create_superuser() {
    echo "Creating superuser..."
    export DOCKER_API_VERSION=1.44
    docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
}

# Function to collect static files
collect_static() {
    echo "Collecting static files..."
    export DOCKER_API_VERSION=1.44
    docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
    echo "✅ Static files collected!"
}

# Function to view logs
view_logs() {
    echo "Viewing logs (Ctrl+C to exit)..."
    export DOCKER_API_VERSION=1.44
    docker compose -f docker-compose.prod.yml logs -f
}

# Function to check status
check_status() {
    echo "Checking service status..."
    export DOCKER_API_VERSION=1.44
    docker compose -f docker-compose.prod.yml ps
    echo ""
    echo "Container resource usage:"
    docker stats --no-stream $(docker compose -f docker-compose.prod.yml ps -q)
}

# Function to backup database
backup_database() {
    echo "Backing up database..."
    export DOCKER_API_VERSION=1.44

    BACKUP_DIR="backups"
    mkdir -p $BACKUP_DIR

    DATE=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/panacare_db_$DATE.sql"

    docker compose -f docker-compose.prod.yml exec -T db pg_dump -U panacare_prod panacare_production > $BACKUP_FILE

    # Compress backup
    gzip $BACKUP_FILE

    echo "✅ Database backup saved to: ${BACKUP_FILE}.gz"
    echo ""
    echo "Tip: Upload to cloud storage for safety:"
    echo "  aws s3 cp ${BACKUP_FILE}.gz s3://your-backup-bucket/"
}

# Function to stop services
stop_services() {
    echo "Stopping services..."
    export DOCKER_API_VERSION=1.44
    docker compose -f docker-compose.prod.yml down
    echo "✅ Services stopped!"
}

# Main menu loop
while true; do
    show_menu
    read -p "Enter your choice [0-9]: " choice

    case $choice in
        1)
            initial_deploy
            ;;
        2)
            update_deploy
            ;;
        3)
            run_migrations
            ;;
        4)
            create_superuser
            ;;
        5)
            collect_static
            ;;
        6)
            view_logs
            ;;
        7)
            check_status
            ;;
        8)
            backup_database
            ;;
        9)
            stop_services
            ;;
        0)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "Invalid option. Please try again."
            ;;
    esac

    read -p "Press Enter to continue..."
done
