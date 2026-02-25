# FURNI Operations Hub - Product Requirements Document

## Overview
A comprehensive e-commerce operations management platform for FURNI furniture business, centralizing order management from multiple sales channels (Amazon, Flipkart, WhatsApp, Website).

## Core Requirements

### Phase 1 - Core Features (COMPLETED)
- **Order Management**: Central dashboard to view, manage, and track all orders
- **Multi-Channel Support**: Amazon, Flipkart, WhatsApp, Website, Phone orders
- **CSV/TXT Import**: Import orders from marketplaces (Amazon TXT, Flipkart CSV)
- **Customer Communication**: WhatsApp Business API integration for messaging
- **Task Management**: Assign tasks to team members
- **Inventory Management**: Track stock levels and product details
- **Dashboard Analytics**: Stats overview with recent orders
- **User Authentication**: JWT-based login/registration with roles

### Phase 2 - Advanced Features (PLANNED)
- **Financial Control**: Per-order profit margins, shipping/RTO costs
- **Return Deep-Diagnosis**: Analyze return reasons by SKU/pincode
- **Installation Management**: Track installer assignments and ratings
- **Quality Control**: Pre-dispatch QC checklists with photo proof
- **Escalation System**: Auto-flag high-value orders, late deliveries
- **Advanced Courier Intelligence**: RTO%, damage%, claim rates
- **Marketplace Health**: ASIN suppressions, listing health
- **Inventory Intelligence**: Dead stock, slow-moving SKUs reports
- **CRM & Risk Management**: Problematic customer flagging
- **Auditing**: User activity logs, data export

## Technical Architecture

### Stack
- **Frontend**: React 18, Tailwind CSS, Shadcn UI
- **Backend**: FastAPI (Python 3.11)
- **Database**: MongoDB (Motor async driver)
- **Auth**: JWT tokens

### Key Endpoints
- `POST /api/auth/login` - User authentication
- `POST /api/auth/register` - User registration
- `GET /api/orders/` - List all orders
- `POST /api/orders/` - Create order
- `POST /api/orders/import-csv` - Import CSV/TXT orders
- `GET /api/dashboard/stats` - Dashboard statistics
- `GET /api/dashboard/recent-orders` - Recent orders

### Database Models
- **users**: id, email, name, role, hashed_password
- **orders**: id, order_number, customer_name, channel, status, dates, product info
- **products**: id, sku, name, stock, price
- **tasks**: id, title, assigned_to, due_date, status

## What's Been Implemented (Feb 25, 2026)

### Completed
1. Full-stack application scaffold
2. FURNI branding (logo, colors)
3. User authentication (JWT)
4. Dashboard with stats and recent orders
5. Orders CRUD with filtering
6. Amazon TXT file import (tab-separated)
7. Flipkart CSV import
8. Order creation form
9. Tasks management UI
10. Inventory management UI
11. WhatsApp CRM UI (configured, needs Meta App)
12. Analytics page UI

### Bug Fixes (Feb 25, 2026)
1. Dashboard crash - Invalid date handling (RangeError)
2. API 307 redirects - Added trailing slashes to frontend calls
3. Amazon TXT import - Added tab-delimiter parser
4. Cleaned corrupt data (empty date strings)

## WhatsApp Configuration
```
WHATSAPP_API_TOKEN=EAAMsUYrYPOABQ... (configured)
WHATSAPP_PHONE_NUMBER_ID=786630157876117
WHATSAPP_WEBHOOK_VERIFY_TOKEN=furni_webhook_secret_2024
```

## Next Steps (Priority Order)
1. P0 - Complete Financial Control Layer
2. P1 - Return Deep-Diagnosis Engine
3. P1 - Installation Control Module
4. P1 - Quality Control Tracking
5. P2 - Advanced Courier Intelligence
6. P2 - Escalation System
