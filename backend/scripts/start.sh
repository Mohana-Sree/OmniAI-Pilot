#!/bin/bash
# OmniTrust AI Backend Development Server Starter

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║          OmniTrust AI - Backend Development Setup          ║"
echo "╚════════════════════════════════════════════════════════════╝"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠ .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ .env created. Please review and update with your settings.${NC}"
fi

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo -e "${GREEN}✓ Python ${PYTHON_VERSION} found${NC}"

# Create virtual environment if not exists
if [ ! -d venv ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate 2>/dev/null

# Install requirements
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Initialize database
echo -e "${YELLOW}Initializing database...${NC}"
python scripts/init_app.py
echo -e "${GREEN}✓ Database initialized${NC}"

# Summary
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              Setup Complete - Ready to Run                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}To start development server, run in separate terminals:${NC}"
echo ""
echo "Terminal 1 - FastAPI Server:"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "Terminal 2 - Celery Worker:"
echo "  source venv/bin/activate"
echo "  celery -A app.workers.celery_app worker --loglevel=info"
echo ""
echo "Terminal 3 - Celery Beat:"
echo "  source venv/bin/activate"
echo "  celery -A app.workers.celery_app beat --loglevel=info"
echo ""
echo -e "${GREEN}API Documentation:${NC}"
echo "  http://localhost:8000/docs"
echo ""
echo -e "${GREEN}Demo Credentials:${NC}"
echo "  Email: admin@demo.local"
echo "  Password: admin123"
echo ""
