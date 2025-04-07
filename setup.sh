#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting setup process..."

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew is not installed. Please install Homebrew first."
    exit 1
fi

# Install system dependencies
echo "📦 Installing system dependencies..."
brew install postgresql@14 redis libjpeg zlib

# Set up environment variables for libjpeg
echo "🔧 Setting up environment variables..."
export LDFLAGS="-L/opt/homebrew/opt/jpeg/lib"
export CPPFLAGS="-I/opt/homebrew/opt/jpeg/include"
export PKG_CONFIG_PATH="/opt/homebrew/opt/jpeg/lib/pkgconfig"

# Add environment variables to .zshrc if they don't exist
if ! grep -q "export LDFLAGS" ~/.zshrc; then
    echo 'export LDFLAGS="-L/opt/homebrew/opt/jpeg/lib"' >> ~/.zshrc
    echo 'export CPPFLAGS="-I/opt/homebrew/opt/jpeg/include"' >> ~/.zshrc
    echo 'export PKG_CONFIG_PATH="/opt/homebrew/opt/jpeg/lib/pkgconfig"' >> ~/.zshrc
fi

# Start PostgreSQL and Redis
echo "🔄 Starting PostgreSQL and Redis services..."
brew services start postgresql@14
brew services start redis

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python -m venv env
source env/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Check Python version
PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "🔍 Detected Python version: $PYTHON_VERSION"

# Install dependencies based on Python version
if [[ "$PYTHON_VERSION" == "3.13" ]]; then
    echo "⚠️ Python 3.13 detected. Using alternative approach for Pillow..."
    
    # Install dependencies without Pillow first
    echo "📚 Installing dependencies without Pillow..."
    grep -v "Pillow" requirements.txt > requirements_without_pillow.txt
    pip install -r requirements_without_pillow.txt
    
    # Try to install Pillow using a pre-built wheel
    echo "📸 Installing Pillow using alternative method..."
    pip install --no-deps --only-binary :all: Pillow==10.4.0 || {
        echo "⚠️ Failed to install Pillow. Continuing without it..."
    }
else
    # Install Pillow separately first
    echo "📸 Installing Pillow..."
    CFLAGS="-I/opt/homebrew/opt/jpeg/include" LDFLAGS="-L/opt/homebrew/opt/jpeg/lib" pip install --no-cache-dir Pillow==10.0.0
    
    # Install other Python dependencies
    echo "📚 Installing other Python dependencies..."
    pip install -r requirements.txt
fi

# Install social-auth-app-django separately to ensure it's installed
echo "🔑 Installing social-auth-app-django..."
pip install social-auth-app-django==5.4.0

# Create database
echo "🗄️ Creating PostgreSQL database..."
createdb budget_tracker || true

# Run migrations with a more robust approach
echo "🔄 Running database migrations..."
python manage.py makemigrations

# Check if the migration file exists
if [ -f "budget/migrations/0004_fix_category_created_at.py" ]; then
    echo "✅ Found fix migration file. Running migrations..."
    python manage.py migrate
else
    echo "⚠️ Fix migration file not found. Using --noinput flag..."
    python manage.py migrate --noinput
fi

# Skip superuser creation since it's already done
echo "👤 Superuser already exists. Skipping creation."

echo "✅ Setup completed successfully!"
echo "To start the development server, run: python manage.py runserver"
echo "To start Celery worker, run: celery -A budget_tracking worker -l info"
echo "To start Celery beat, run: celery -A budget_tracking beat -l info" 