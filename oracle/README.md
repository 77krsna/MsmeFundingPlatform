# MSME Finance Platform - Backend API

Oracle-driven blockchain financing platform for MSMEs using government orders as collateral.

## Features

- ✅ GeM Portal Monitoring (automated order detection)
- ✅ GSTN Invoice Verification (automated compliance)
- ✅ Blockchain Integration (smart contract creation)
- ✅ RESTful API (FastAPI with auto-docs)
- ✅ Background Tasks (Celery worker)
- ✅ Real-time Status Dashboard

## Technology Stack

- **Backend**: Python 3.11, FastAPI
- **Database**: PostgreSQL 18
- **Queue**: Redis
- **Tasks**: Celery
- **Blockchain**: Web3.py (Polygon ready)

## Quick Start

### 1. Prerequisites

- Python 3.11+
- PostgreSQL 18+
- Redis (or use SQLite broker)
- Node.js (for frontend later)

### 2. Installation

```bash
cd C:\MsmeFundingPlatform\oracle

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Initialize database
python init_database.py