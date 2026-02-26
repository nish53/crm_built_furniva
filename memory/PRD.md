# Furniva Operations Hub - Product Requirements Document

## Overview
A comprehensive e-commerce operations management platform for Furniva furniture business, centralizing order management from multiple sales channels (Amazon, Flipkart, WhatsApp, Website).

## Core Requirements

### Phase 1 - Core Features (COMPLETED)
- **Order Management**: Central dashboard to view, manage, and track all orders
- **Multi-Channel Support**: Amazon, Flipkart, WhatsApp, Website, Phone orders
- **CSV/TXT Import**: Import orders from marketplaces (Amazon TXT, Flipkart CSV)
- **Customer Communication**: WhatsApp Business API integration (webhook blocked by Meta - needs custom domain)
- **Task Management**: Assign tasks to team members
- **Dashboard Analytics**: Stats overview with recent orders
- **User Authentication**: JWT-based login/registration with roles

### Phase 2 - Inventory & Financial (COMPLETED - Feb 2026)
- **Master SKU Management**: Central product identifier with full CRUD
  - Platform-specific SKU mapping (Amazon SKU/ASIN/FNSKU, Flipkart SKU/FSN, Website SKU)
  - Category, dimensions, weight, cost/selling price
- **Platform Listings**: Multiple listings per platform per Master SKU
  - Add/remove listings with platform selector
  - ASIN, FSN, FNSKU tracking per listing
- **Procurement Batches**: Track inventory procurement with batch-level costing
  - Weighted average cost calculation (FIFO, LIFO, Weighted)
  - Batch number, quantity, unit cost, supplier, notes
  - Total stock aggregation across batches
- **Returns Management**: Full return workflow
  - Create returns from Order Detail page
  - Return reasons, damage categories, installation-related flag
  - Status workflow: Requested > Approved > Pickup > In Transit > Received > Inspected > Refunded/Replaced
  - Return analytics by reason and by product
- **Financial Control**: Per-order profitability tracking
  - Product cost, shipping, packaging, installation inputs
  - Auto-calculated: marketplace commission, TCS/TDS, gateway fees
  - Gross profit, profit margin, contribution margin
  - Settlement tracking and leakage detection
  - Aggregated profit analysis dashboard

### Phase 3 - Advanced Features (PLANNED)
- Financial Control Layer UI enhancements
- Installation Management (installer assignments, ratings)
- Quality Control (pre-dispatch QC checklists with photo proof)
- Escalation System (auto-flag high-value orders, late deliveries)
- Advanced Courier Intelligence (RTO%, damage%, claim rates)
- Marketplace Health Monitoring (ASIN suppressions, listing health)
- Inventory Intelligence Reports (dead stock, slow-moving SKUs)
- CRM & Risk Management (problematic customer flagging)
- Auditing (user activity logs, data export)

## Technical Architecture

### Stack
- **Frontend**: React 18, Tailwind CSS, Shadcn UI
- **Backend**: FastAPI (Python 3.11)
- **Database**: MongoDB (Motor async driver)
- **Auth**: JWT tokens

### Key API Endpoints
- `POST /api/auth/login` - User authentication
- `POST /api/auth/register` - User registration
- `GET/POST /api/orders/` - Orders CRUD
- `POST /api/orders/import-csv` - Import CSV/TXT orders
- `GET/POST /api/master-sku/` - Master SKU CRUD
- `GET/POST /api/platform-listings/` - Platform listings CRUD
- `GET /api/platform-listings/by-master-sku/{sku}` - Listings by Master SKU
- `GET/POST /api/procurement-batches/` - Procurement batch CRUD
- `GET /api/procurement-batches/average-cost/{sku}` - Average cost calculation
- `GET/POST /api/returns/` - Returns CRUD
- `PATCH /api/returns/{id}/status` - Update return status
- `POST /api/financials/calculate/{order_id}` - Calculate order financials
- `GET /api/financials/profit-analysis` - Aggregated profit analysis
- `GET /api/financials/leakage-report` - Leakage detection

### Database Models
- **users**: id, email, name, role, hashed_password
- **orders**: id, order_number, customer_name, channel, status, sku, master_sku, price, dates, tracking, communication flags
- **master_sku_mappings**: id, master_sku, product_name, category, amazon_sku/asin/fnsku, flipkart_sku/fsn, website_sku, dimensions, weight, cost_price, selling_price
- **platform_listings**: id, master_sku, platform, platform_sku, platform_product_id, platform_fnsku, is_active
- **procurement_batches**: id, master_sku, batch_number, procurement_date, quantity, unit_cost, total_cost, supplier
- **return_requests**: id, order_id, order_number, customer_name, return_reason, return_status, damage_category, dates
- **order_financials**: id, order_id, selling_price, marketplace_commission, net_revenue, costs, gross_profit, profit_margin
- **tasks**: id, title, assigned_to, due_date, status

## What's Been Implemented

### Completed (Feb 26, 2026)
1. Full-stack application with Furniva branding
2. User authentication (JWT)
3. Dashboard with stats and recent orders
4. Orders CRUD with filtering and search
5. Amazon TXT/CSV and Flipkart CSV import with date parsing (ISO 8601 support)
6. **Inventory Page** - Complete Master SKU management with:
   - Master SKU cards with stats (listings count, stock, avg cost)
   - Create/Edit Master SKU modal with all platform fields
   - Platform Listings modal (add/remove per platform)
   - Procurement Batches modal (add batches, view history, weighted avg cost)
7. **Order Detail Page** - Enhanced with:
   - All order fields displayed (SKU, ASIN, tracking, master status, etc.)
   - Delivery timeline card
   - Communication checklist (DC1, CP, DNP-3/2/1, delivery, install, review)
   - "Create Return" button with full return form
   - "Calculate Financials" button with cost input modal
   - Financial summary display
8. **Returns Management** - Full page with:
   - Returns list with search and status filter
   - Detail modal with status progression workflow
   - Approve/Reject, Pickup, Transit, Receive, Inspect, Refund/Replace
9. **Costing Page** - Financial control dashboard with:
   - 4 KPI cards (Revenue, Net Revenue, Costs, Profit)
   - Leakage report
   - How It Works guide
10. Clean navigation sidebar (10 sections)
11. Tasks management
12. Channels management
13. WhatsApp CRM (configured, webhook blocked by Meta)
14. Analytics page

### Bug Fixes (Feb 26, 2026)
1. Fixed corrupted models.py - duplicate class fields in ProcurementBatchCreate and ChannelCreate
2. Made sku and product_name optional in OrderBase to handle imported orders without these fields
3. Fixed frontend compilation issues

## Known Issues
1. WhatsApp webhook blocked by Meta (external - needs custom domain)
2. Some imported orders have incomplete data (no customer name, ₹0 price)

## Next Steps (Priority Order)
1. P1 - Installation Management module
2. P1 - Quality Control tracking
3. P2 - Escalation System
4. P2 - Advanced Courier Intelligence
5. P2 - Marketplace Health Monitoring
6. P3 - CRM & Risk Management
7. P3 - Inventory Intelligence Reports
