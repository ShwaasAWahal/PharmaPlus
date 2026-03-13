# AI-Powered Pharmacy Management System — Backend API

A production-ready Flask REST API for managing a multi-branch pharmacy with JWT auth, inventory tracking, billing, expiry alerts, and ML service integration hooks.

---

## 🏗️ Project Structure

```
backend/
├── app.py                    # App factory & entry point
├── config.py                 # Environment-based config
├── extensions.py             # JWT, Mail singletons
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
│
├── models/
│   ├── user.py               # Users (admin / pharmacist)
│   ├── branch.py             # Pharmacy branches
│   ├── supplier.py           # Medicine suppliers
│   ├── medicine.py           # Medicine master catalog
│   ├── inventory.py          # Batch-level stock with expiry
│   ├── sales.py              # Sales + SaleItems
│   └── prescription.py       # Uploaded prescription images
│
├── routes/
│   ├── auth_routes.py        # /api/auth/*
│   ├── medicine_routes.py    # /api/medicines/* + barcode + suppliers + branches
│   ├── inventory_routes.py   # /api/inventory/*
│   ├── billing_routes.py     # /api/billing/* + prescription upload
│   ├── analytics_routes.py   # /api/analytics/*
│   └── ml_routes.py          # /api/ml/*
│
├── services/
│   ├── inventory_service.py  # Stock queries, expiry/low-stock detection
│   ├── billing_service.py    # Bill creation, invoice generation
│   ├── alert_service.py      # Scheduled alert orchestration
│   └── ml_proxy_service.py   # ML service HTTP proxy + mocks
│
├── utils/
│   ├── jwt_utils.py          # Token helpers, role_required decorator
│   ├── email_utils.py        # Email sending helpers
│   └── scheduler.py         # APScheduler job definitions
│
└── database/
    └── db.py                 # SQLAlchemy init + seed
```

---

## 🚀 Quick Start (Local — SQLite)

### 1. Clone and set up virtual environment

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — at minimum set SECRET_KEY and JWT_SECRET_KEY
```

### 3. Run

```bash
python app.py
# API available at http://localhost:5000
```

On first run, the database is auto-created and seeded with:
- **Branch**: "Main Branch"
- **Admin user**: `admin@pharmacy.com` / `Admin@1234`

---

## 🐳 Docker (with PostgreSQL)

```bash
# Build and start all services
docker-compose up --build

# Stop
docker-compose down
```

The API will be available at `http://localhost:5000`.

---

## 🔑 Authentication Flow

All protected endpoints require `Authorization: Bearer <access_token>`.

```
1. POST /api/auth/login          → { access_token, refresh_token, user }
2. Use access_token in header    → Authorization: Bearer <token>
3. POST /api/auth/refresh        → New access_token (use refresh_token as Bearer)
```

**Default admin credentials:**
- Email: `admin@pharmacy.com`
- Password: `Admin@1234`

---

## 📡 API Endpoints Summary

### Auth — `/api/auth`
| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| POST | `/login` | Public | Get JWT tokens |
| POST | `/register` | Admin | Register new user |
| GET | `/me` | Any | Current user profile |
| PUT | `/me/password` | Any | Change password |
| POST | `/refresh` | Any | Refresh access token |
| GET | `/users` | Admin | List all users |
| PUT | `/users/:id` | Admin | Update user |
| DELETE | `/users/:id` | Admin | Deactivate user |

### Medicines — `/api/medicines`
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List/search medicines |
| POST | `/` | Add medicine |
| GET | `/:id` | Get medicine detail |
| PUT | `/:id` | Update medicine |
| DELETE | `/:id` | Deactivate medicine |
| **POST** | **/barcode/scan** | **Scan barcode → medicine info** |
| GET | `/suppliers` | List suppliers |
| POST | `/suppliers` | Add supplier |
| PUT | `/suppliers/:id` | Update supplier |
| GET | `/branches` | List branches |
| POST | `/branches` | Add branch (Admin) |
| PUT | `/branches/:id` | Update branch (Admin) |

### Inventory — `/api/inventory`
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List inventory (filterable) |
| POST | `/` | Add/restock batch |
| GET | `/:id` | Get batch detail |
| PUT | `/:id` | Update batch |
| DELETE | `/:id` | Deactivate batch |
| POST | `/:id/adjust` | Manual stock adjustment |
| GET | `/alerts/expiring` | Expiring within N days |
| GET | `/alerts/low-stock` | Below threshold |
| GET | `/alerts/expired` | Expired items in stock |

### Billing — `/api/billing`
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/bills` | Create bill (deducts inventory) |
| GET | `/bills` | List bills |
| GET | `/bills/:id` | Get bill detail |
| GET | `/bills/:id/invoice` | Structured invoice JSON |
| **POST** | **/prescription/upload** | **Upload prescription image** |
| GET | `/prescriptions` | List prescriptions |
| GET | `/prescriptions/:id` | Get prescription detail |

### Analytics — `/api/analytics`
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/summary` | Dashboard KPI summary |
| GET | `/top-medicines` | Top selling medicines |
| GET | `/monthly-revenue` | Monthly revenue chart data |
| GET | `/expired-stock` | Expired stock report |
| GET | `/supplier-performance` | Supplier ratings + expired batch count |

### ML Integration — `/api/ml`
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/predict-demand` | Demand forecast (mock/proxy) |
| POST | `/recommend-generic` | Generic alternatives (mock/proxy) |
| POST | `/process-prescription` | OCR prescription parsing (mock/proxy) |
| GET | `/status` | ML service connectivity check |

---

## 📧 Email Alerts

Email alerts are sent automatically by the **daily 8:00 AM scheduled job**. Alerts cover:
- Medicines expiring within 30 days
- Medicines below low-stock threshold

Configure `MAIL_*` vars in `.env`. To test manually:

```python
from flask import create_app
from services.alert_service import run_stock_and_expiry_check
app = create_app()
with app.app_context():
    run_stock_and_expiry_check()
```

---

## 🤖 ML Integration

ML endpoints currently return **structured mock responses**. To connect a real ML service:

1. Set `ML_SERVICE_BASE_URL` in `.env` (e.g. `http://ml-service:8000`)
2. Optionally set `ML_SERVICE_API_KEY`
3. Ensure ML service exposes:
   - `POST /predict-demand`
   - `POST /recommend-generic`
   - `POST /process-prescription`
   - `GET /health`

The proxy in `services/ml_proxy_service.py` will automatically forward requests.

---

## 🗄️ Database Schema (Tables)

| Table | Description |
|-------|-------------|
| `users` | Auth users with roles |
| `branches` | Pharmacy branch locations |
| `suppliers` | Medicine suppliers |
| `medicines` | Master medicine catalog |
| `inventory` | Batch-level stock with expiry |
| `sales` | Sale transactions (bills) |
| `sale_items` | Line items per sale |
| `prescriptions` | Uploaded prescription images |

---

## 🔒 Roles

| Role | Permissions |
|------|-------------|
| `admin` | Full access — manage users, branches, all CRUD |
| `pharmacist` | Medicines, inventory, billing, prescriptions (read/write) |

---

## 🧪 Running Tests

```bash
FLASK_ENV=testing python -m pytest tests/ -v
```

---

## 📦 Production Deployment

```bash
# Set FLASK_ENV=production and DATABASE_URL (PostgreSQL) in .env
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 "app:create_app()"
```
