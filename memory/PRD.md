# Furniva Operations Hub - Product Requirements Document

## Overview
A comprehensive e-commerce operations management platform for Furniva furniture business, centralizing order management from multiple sales channels (Amazon, Flipkart, WhatsApp, Website).

## Technical Stack
- **Frontend**: React 18, Tailwind CSS, Shadcn UI, Lucide Icons
- **Backend**: FastAPI (Python 3.11), Motor (async MongoDB)
- **Database**: MongoDB
- **Auth**: JWT tokens

## Core Architecture
- **Master SKU**: Central product identifier (no dimensions/weight/costs - those belong in procurement)
- **Platform Listings**: Per-platform SKU/ASIN/FSN/FNSKU mappings under each Master SKU
- **Procurement Batches**: Inventory procurement with per-box weight/dimensions, auto-calculated total weight, weighted avg cost
- **Returns**: Full workflow with mandatory fields, status history, undo capability

## What's Been Implemented

### Phase 1 - Core Features
1. User authentication (JWT) with roles
2. Dashboard with stats and recent orders
3. Orders CRUD with filtering, search, status management
4. Amazon TXT/CSV and Flipkart CSV import with date parsing (ISO 8601)
5. Task management
6. Channels management
7. Analytics page
8. WhatsApp CRM (configured, webhook blocked by Meta - needs custom domain)

### Phase 2 - Inventory & Financial (Feb 26, 2026)
1. **Inventory Page** - Master SKU CRUD with:
   - Simplified form (no FNSKU/dims/weight/costs - just SKU identifiers)
   - Platform Listings modal (add/remove per platform with SKU/ASIN/FSN/FNSKU)
   - Procurement modal with per-box weight + dimensions (L×W×H), auto-calculated total weight
2. **Order Detail** - Enhanced with:
   - All order fields (tracking, master_status, fulfillment, etc.)
   - Delivery timeline card
   - **Read-only** Communication Status (green/red indicators, automated via WhatsApp CRM)
   - Correct checklist order: Order Confirm Call → Message → DNP 1/2/3 → Dispatch → Delivery → Install → Review
   - Always-visible "Create Return Request" button (orange styled)
   - "Calculate Financials" modal
3. **Returns Management** with:
   - Status workflow with **mandatory fields** (Pickup Scheduled → pickup date required, In Transit → tracking required)
   - **Undo/Reverse** capability at every status (reverts to previous state)
   - Full **status history** with timestamps and user info
   - Status history display in detail modal
4. **Costing Page** - Financial control dashboard with:
   - 4 KPI cards (Revenue, Net Revenue, Costs, Profit)
   - Leakage report
   - How It Works guide
5. Clean navigation: Dashboard → Orders → Inventory → Returns → Costing → Channels → Tasks → Analytics → WhatsApp → Team

### Bug Fixes (Feb 26, 2026)
1. Fixed corrupted models.py - duplicate class fields in ProcurementBatchCreate and ChannelCreate
2. Made sku and product_name optional in OrderBase for imported orders
3. Simplified MasterSKU form per user feedback
4. Added box-level procurement tracking (weight, dimensions)
5. Return workflow with mandatory field validation and undo

## Key API Endpoints
- `POST /api/auth/login` - Authentication
- `GET/POST /api/orders/` - Orders CRUD
- `POST /api/orders/import-csv` - Import CSV/TXT
- `GET/POST /api/master-sku/` - Master SKU CRUD
- `GET/POST /api/platform-listings/` - Platform listings CRUD
- `GET/POST /api/procurement-batches/` - Procurement with box details
- `GET /api/procurement-batches/average-cost/{sku}` - Weighted avg cost
- `GET/POST /api/returns/` - Returns CRUD
- `PATCH /api/returns/{id}/status` - Update with mandatory field validation
- `PATCH /api/returns/{id}/undo` - Undo last status change
- `POST /api/financials/calculate/{order_id}` - Per-order financials
- `GET /api/financials/profit-analysis` - Aggregated analysis

## Known Issues
1. WhatsApp webhook blocked by Meta (external - needs custom domain for production)
2. Communication checklist currently read-only; will be automated via WhatsApp CRM integration

## Next Steps (Priority Order)
1. P1 - Installation Management module (installer assignments, scheduling, ratings)
2. P1 - Quality Control tracking (pre-dispatch QC checklists with photo proof)
3. P2 - Escalation System (auto-flag high-value orders, late deliveries)
4. P2 - Advanced Courier Intelligence (RTO%, damage%, claim rates)
5. P2 - Marketplace Health Monitoring
6. P3 - CRM & Risk Management
7. P3 - Inventory Intelligence Reports
