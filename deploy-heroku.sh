#!/bin/bash

# Professional Heroku Container Deployment Script
# Usage: ./deploy-heroku.sh [app-name] [google-maps-api-key]

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are installed
check_requirements() {
    log_info "Checking requirements..."
    
    if ! command -v heroku &> /dev/null; then
        log_error "Heroku CLI is not installed. Please install it from https://devcenter.heroku.com/articles/heroku-cli"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install it from https://www.docker.com/get-started"
        exit 1
    fi
    
    if ! command -v git &> /dev/null; then
        log_error "Git is not installed. Please install Git."
        exit 1
    fi
    
    log_success "All requirements satisfied"
}

# Get app name from user or parameter
get_app_name() {
    if [ -z "$1" ]; then
        read -p "Enter your Heroku app name: " APP_NAME
    else
        APP_NAME="$1"
    fi
    
    if [ -z "$APP_NAME" ]; then
        log_error "App name is required"
        exit 1
    fi
    
    log_info "Using app name: $APP_NAME"
}

# Get Google Maps API key from user or parameter
get_api_key() {
    if [ -z "$1" ]; then
        read -p "Enter your Google Maps API key: " GOOGLE_MAPS_API_KEY
    else
        GOOGLE_MAPS_API_KEY="$1"
    fi
    
    if [ -z "$GOOGLE_MAPS_API_KEY" ]; then
        log_warning "No Google Maps API key provided. Maps functionality may not work."
    else
        log_info "Google Maps API key provided"
    fi
}

# Check if logged into Heroku
check_heroku_auth() {
    log_info "Checking Heroku authentication..."
    
    if ! heroku auth:whoami &> /dev/null; then
        log_warning "Not logged into Heroku. Please login."
        heroku login
    fi
    
    log_success "Heroku authentication verified"
}

# Create or verify Heroku app
setup_heroku_app() {
    log_info "Setting up Heroku app: $APP_NAME"
    
    # Check if app exists
    if heroku apps:info -a "$APP_NAME" &> /dev/null; then
        log_success "App $APP_NAME already exists"
    else
        log_info "Creating new Heroku app: $APP_NAME"
        heroku create "$APP_NAME"
        log_success "Created app $APP_NAME"
    fi
    
    # Set stack to container
    log_info "Setting stack to container"
    heroku stack:set container -a "$APP_NAME"
    
    # Add git remote if it doesn't exist
    if ! git remote get-url heroku &> /dev/null; then
        heroku git:remote -a "$APP_NAME"
        log_success "Added Heroku git remote"
    fi
}

# Configure environment variables
configure_environment() {
    log_info "Configuring environment variables..."
    
    # Generate Django secret key
    SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    
    # Set required environment variables
    heroku config:set DJANGO_SECRET_KEY="$SECRET_KEY" -a "$APP_NAME"
    heroku config:set DEBUG=false -a "$APP_NAME"
    heroku config:set ENVIRONMENT=production -a "$APP_NAME"
    
    if [ -n "$GOOGLE_MAPS_API_KEY" ]; then
        heroku config:set GOOGLE_MAPS_API_KEY="$GOOGLE_MAPS_API_KEY" -a "$APP_NAME"
    fi
    
    log_success "Environment variables configured"
}

# Add PostgreSQL database
setup_database() {
    log_info "Setting up PostgreSQL database..."
    
    # Check if PostgreSQL addon already exists
    if heroku addons --app "$APP_NAME" | grep -q "heroku-postgresql"; then
        log_success "PostgreSQL addon already exists"
    else
        log_info "Adding PostgreSQL addon"
        heroku addons:create heroku-postgresql:essential-0 -a "$APP_NAME"
        log_success "PostgreSQL addon added"
    fi
    
    # Wait for database to be available
    log_info "Waiting for database to be ready..."
    sleep 10
    
    # Enable PostGIS extension
    log_info "Enabling PostGIS extension..."
    heroku pg:psql -a "$APP_NAME" -c "CREATE EXTENSION IF NOT EXISTS postgis;" || log_warning "PostGIS extension setup may have failed"
    
    log_success "Database setup completed"
}

# Deploy the application
deploy_application() {
    log_info "Deploying application..."
    
    # Ensure we're on the main branch
    CURRENT_BRANCH=$(git branch --show-current)
    if [ "$CURRENT_BRANCH" != "main" ] && [ "$CURRENT_BRANCH" != "master" ]; then
        log_warning "Not on main/master branch. Current branch: $CURRENT_BRANCH"
        read -p "Continue with current branch? (y/N): " CONTINUE
        if [ "$CONTINUE" != "y" ] && [ "$CONTINUE" != "Y" ]; then
            log_error "Deployment cancelled"
            exit 1
        fi
    fi
    
    # Add and commit any changes
    if ! git diff --quiet; then
        log_info "Committing local changes..."
        git add .
        git commit -m "Prepare for Heroku deployment" || log_warning "No changes to commit"
    fi
    
    # Push to Heroku
    log_info "Pushing to Heroku..."
    git push heroku HEAD:main
    
    log_success "Application deployed successfully"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Wait a moment for the app to start
    sleep 5
    
    # Check if app is running
    APP_URL="https://$APP_NAME.herokuapp.com"
    log_info "Checking app health at $APP_URL/health/"
    
    if curl -s "$APP_URL/health/" | grep -q "healthy"; then
        log_success "Application is healthy and running"
        log_success "App URL: $APP_URL"
    else
        log_warning "Health check failed or app may still be starting"
        log_info "Check logs with: heroku logs --tail -a $APP_NAME"
    fi
    
    # Show logs
    log_info "Recent logs:"
    heroku logs --num 20 -a "$APP_NAME"
}

# Provide post-deployment information
show_post_deployment_info() {
    echo ""
    log_success "🚀 Deployment completed!"
    echo ""
    echo "App URL: https://$APP_NAME.herokuapp.com"
    echo "Health Check: https://$APP_NAME.herokuapp.com/health/"
    echo "Admin: https://$APP_NAME.herokuapp.com/admin/"
    echo ""
    echo "Useful commands:"
    echo "  View logs: heroku logs --tail -a $APP_NAME"
    echo "  Open app: heroku open -a $APP_NAME"
    echo "  Run shell: heroku run python manage.py shell -a $APP_NAME"
    echo "  Run migrations: heroku run python manage.py migrate -a $APP_NAME"
    echo "  Import data: heroku run python manage.py import_shelters -a $APP_NAME"
    echo ""
    echo "Configuration:"
    echo "  View config: heroku config -a $APP_NAME"
    echo "  Set variable: heroku config:set KEY=value -a $APP_NAME"
    echo ""
}

# Main execution
main() {
    echo "🐳 Professional Heroku Container Deployment"
    echo "=============================================="
    
    check_requirements
    get_app_name "$1"
    get_api_key "$2"
    check_heroku_auth
    setup_heroku_app
    configure_environment
    setup_database
    deploy_application
    verify_deployment
    show_post_deployment_info
}

# Run main function with all arguments
main "$@"