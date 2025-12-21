#!/bin/bash
# CyberX GCP Deployment Script
# Run this script on your GCP VM after SSHing into it

set -e  # Exit on any error

echo "=========================================="
echo "  CyberX GCP Deployment Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/atf-inc/dec25_intern_C_security.git"
PROJECT_DIR="$HOME/dec25_intern_C_security"
BACKEND_PORT=8000

echo -e "${YELLOW}Step 1: Cloning repository...${NC}"
cd ~
if [ -d "$PROJECT_DIR" ]; then
    echo "Project directory exists. Pulling latest changes..."
    cd "$PROJECT_DIR"
    git fetch origin develop
    git checkout develop
    git pull origin develop
else
    echo "Cloning fresh repository..."
    git clone "$REPO_URL"
    cd "$PROJECT_DIR"
    git checkout develop
fi
echo -e "${GREEN}✓ Repository ready${NC}"

echo -e "${YELLOW}Step 2: Setting up Backend...${NC}"
cd "$PROJECT_DIR/backend"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip and install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOF
GEMINI_API_KEY=your_api_key_here
DATABASE_URL=sqlite:///./cyber_defense.db
EOF
    echo -e "${YELLOW}⚠ Please update .env with your actual GEMINI_API_KEY${NC}"
fi

# Create uploads directory
mkdir -p uploads/voice

echo -e "${GREEN}✓ Backend setup complete${NC}"

echo -e "${YELLOW}Step 3: Setting up Frontend...${NC}"
cd "$PROJECT_DIR/frontend"

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install

# Build production version
echo "Building frontend for production..."
npm run build

echo -e "${GREEN}✓ Frontend build complete${NC}"

echo -e "${YELLOW}Step 4: Setting up Nginx...${NC}"

# Install nginx if not present
if ! command -v nginx &> /dev/null; then
    echo "Installing nginx..."
    sudo apt install -y nginx
fi

# Copy frontend build to nginx
echo "Deploying frontend to nginx..."
sudo rm -rf /var/www/html/*
sudo cp -r "$PROJECT_DIR/frontend/dist/"* /var/www/html/

# Create nginx configuration
echo "Configuring nginx..."
sudo tee /etc/nginx/sites-available/default > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    root /var/www/html;
    index index.html;

    # Frontend - React SPA
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend API proxy
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 50M;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8000/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
EOF

# Test nginx configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
sudo systemctl enable nginx

echo -e "${GREEN}✓ Nginx configured${NC}"

echo -e "${YELLOW}Step 5: Creating Backend Service...${NC}"

# Get current username
CURRENT_USER=$(whoami)

# Create systemd service for backend
sudo tee /etc/systemd/system/cyberx-backend.service > /dev/null << EOF
[Unit]
Description=CyberX Backend API
After=network.target

[Service]
User=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR/backend
Environment="PATH=$PROJECT_DIR/backend/venv/bin"
ExecStart=$PROJECT_DIR/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start service
sudo systemctl daemon-reload
sudo systemctl enable cyberx-backend
sudo systemctl restart cyberx-backend

echo -e "${GREEN}✓ Backend service created and started${NC}"

echo -e "${YELLOW}Step 6: Verifying deployment...${NC}"

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 10

# Check backend health
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is running${NC}"
else
    echo -e "${RED}✗ Backend health check failed. Checking logs...${NC}"
    sudo journalctl -u cyberx-backend -n 20 --no-pager
fi

# Check nginx
if curl -s http://localhost > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend is accessible${NC}"
else
    echo -e "${RED}✗ Frontend not accessible${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}  Deployment Complete!${NC}"
echo "=========================================="
echo ""
echo "Access your application:"
echo "  Frontend: http://$(curl -s ifconfig.me)"
echo "  Backend API: http://$(curl -s ifconfig.me)/api/v1/voice/health"
echo "  API Docs: http://$(curl -s ifconfig.me):8000/docs"
echo ""
echo "Useful commands:"
echo "  View backend logs: sudo journalctl -u cyberx-backend -f"
echo "  Restart backend:   sudo systemctl restart cyberx-backend"
echo "  Restart nginx:     sudo systemctl restart nginx"
echo "  Backend status:    sudo systemctl status cyberx-backend"
echo ""
echo -e "${YELLOW}Note: First API call may take 30-60 seconds as ML models load.${NC}"

