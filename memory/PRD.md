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

### Phase 3 - Returns & Replacements System (Mar 28, 2026)
1. **12-Stage Return Workflow** supporting:
   - Post-delivery returns (customer returns after receiving)
   - RTO/In-transit returns (return to origin during delivery)
   - Pre-dispatch cancellations
   - Returns after unsatisfactory replacement
2. **Dual-Approval Replacement System**:
   - Pickup Approval (approve old item pickup)
   - Replacement Approval (approve sending new item)
   - Dual status badges on overview tiles (🔄 Pickup | 📦 Shipment)
   - Independent pickup and shipment tracking
3. **Counter Cards for Replacements** (7 tiles):
   - Open Replacements, Replacement Approval, Pickup Approval
   - Pickups Pending, Pickups In Transit
   - Shipments Pending, Shipments In Transit
4. **Smart CSV Import Duplicate Check**:
   - Multi-item orders (same order_id, different SKUs) → import correctly
   - True duplicates (same order_id + same SKU) → skip automatically
5. **Unified Order History & Status Card** (Order Detail):
   - Single consolidated card for all return/replacement milestones
   - Removed redundant cards (Return Info sidebar, separate Status card)
   - Timeline card now only shows order lifecycle (not return dates)
   - Clear separation: Return Timeline + Replacement Timeline (Pickup + Shipment tracks)
6. **Streamlined Post-Delivery Return Workflow**:
   - Removed redundant "pickup_in_transit" step
   - Flow: Requested → Accepted → Picked Up (In Transit) → Warehouse Received → Refund Processed → Closed

### Phase 4 - Inventory Intelligence System (Mar 28, 2026) ✅ PHASE 1, 2 & 3 COMPLETE

**Phase 1 - Core Analytics:**
1. **Bulk CSV Import** (supports MULTIPLE listings per master SKU)
2. **Real-Time Stock Buckets** (Reserved, Available, In Transit, Damaged)
3. **Inventory Aging Analysis** (5 age buckets with suggested actions)
4. **Stockout Alerts** (7-day threshold with priority levels)

**Phase 2 - Intelligence:**
5. **Demand Forecasting** (30-day, seasonal multipliers, weighted moving average)
6. **Purchase Intelligence** (smart order qty formula, urgency levels)
7. **Return & Damage Analysis** (SKU-level return rates, problem detection)

**Phase 3 - Automation:**
8. **Auto-Create Purchase Orders** (one-click PO from suggestions)
9. **Purchase Order Management** (track PO status: pending → confirmed → shipped → received)
10. **Liquidation Suggestions** (age-based, discount recommendations, priority levels)
11. **Smart Alerts Dashboard** (combines stockout + dead stock + high returns alerts)
12. **Multiple Platform Listings per SKU** (same master SKU → multiple Amazon ASINs, Flipkart FSNs, etc.)

**Dashboard - 10 tabs:** Dashboard, Stock, Aging, Stockout, Forecast, Purchase, Returns, Liquidate, All Alerts, POs

**CSV Import Format (NEW):**
- Supports multiple rows per master_sku for different platform listings
- Columns: master_sku, product_name, category, platform, platform_sku, platform_product_id, listing_title, cost_price, selling_price
- Example: FRN-001 can have multiple Amazon listings with different ASINs, plus Flipkart listings

### Bug Fixes (Feb 26, 2026)
1. Fixed corrupted models.py - duplicate class fields in ProcurementBatchCreate and ChannelCreate
2. Made sku and product_name optional in OrderBase for imported orders
3. Simplified MasterSKU form per user feedback
4. Added box-level procurement tracking (weight, dimensions)
5. Return workflow with mandatory field validation and undo

### Bug Fixes (Mar 28, 2026)
1. Added 'test' as valid OrderChannel for test data compatibility
2. Fixed replacement timeline graphics not highlighting correctly
3. Removed approval/reject buttons from Replacements overview page (approvals only in detail view)
4. Fixed order_id filter for return-requests and replacement-requests endpoints

## Key API Endpoints

### Authentication
- `POST /api/auth/login` - Authentication

### Orders
- `GET/POST /api/orders/` - Orders CRUD
- `POST /api/orders/import-csv` - Import CSV/TXT
- `POST /api/import/with-mapping` - Smart import with duplicate check (order_number + SKU)

### Inventory - Master SKU & Listings
- `GET/POST /api/master-sku/` - Master SKU CRUD
- `GET/POST /api/platform-listings/` - Platform listings CRUD
- `GET/POST /api/procurement-batches/` - Procurement with box details
- `GET /api/procurement-batches/average-cost/{sku}` - Weighted avg cost

### Returns & Replacements
- `GET/POST /api/return-requests/` - Returns CRUD (supports ?order_id filter)
- `POST /api/return-requests/{id}/advance` - Advance return workflow
- `POST /api/return-requests/{id}/undo` - Undo last status change
- `GET/POST /api/replacement-requests/` - Replacements CRUD (supports ?order_id, ?filter_type filters)
- `POST /api/replacement-requests/{id}/approve-pickup` - Approve pickup
- `POST /api/replacement-requests/{id}/approve-replacement` - Approve replacement shipment
- `POST /api/replacement-requests/{id}/advance-pickup` - Advance pickup workflow
- `POST /api/replacement-requests/{id}/advance-shipment` - Advance shipment workflow
- `GET /api/replacement-requests/analytics/counts-v2` - Dashboard counters

### Financials
- `POST /api/financials/calculate/{order_id}` - Per-order financials
- `GET /api/financials/profit-analysis` - Aggregated analysis

### Inventory Intelligence (NEW)
- `POST /api/inventory/bulk-import-csv` - Bulk import SKUs with multiple listings
- `GET /api/inventory/csv-template` - Get CSV template for import
- `GET /api/inventory/stock-summary` - Real-time stock buckets
- `GET /api/inventory/aging-analysis` - Inventory aging (5 buckets)
- `GET /api/inventory/stockout-alerts` - Stockout alerts with priority
- `GET /api/inventory/demand-forecast` - 30-day demand forecasting
- `GET /api/inventory/purchase-suggestions` - Smart PO suggestions
- `GET /api/inventory/return-analysis` - SKU-level return analysis
- `GET /api/inventory/courier-damage-analysis` - Courier damage rates
- `GET /api/inventory/liquidation-suggestions` - Dead stock liquidation
- `GET /api/inventory/smart-alerts` - Combined alerts dashboard
- `POST /api/inventory/auto-create-po` - Auto-create purchase order
- `GET /api/inventory/purchase-orders` - List purchase orders
- `PATCH /api/inventory/purchase-orders/{po_id}/status` - Update PO status
- `GET /api/inventory/listings-by-sku/{master_sku}` - Get all listings for SKU
- `GET /api/inventory/dashboard` - Inventory dashboard summary

## Known Issues
1. WhatsApp webhook blocked by Meta (external - needs custom domain for production)
2. Communication checklist currently read-only; will be automated via WhatsApp CRM integration

## Next Steps - Phase 4: Advanced Inventory Features
1. **Multi-Warehouse Support** - Warehouse CRUD, warehouse-wise stock tracking, transfer orders
2. **Cycle Counts** - Partial inventory checks, variance detection, random SKU selection
3. **Shrinkage Detection** - Expected vs actual stock, shrinkage alerts
4. **Stock Adjustments** - Manual adjustments with reason codes, approval workflows
5. **Audit Logs** - All stock movements with user accountability

## Future Phases
1. P1 - Installation Management module (installer assignments, scheduling, ratings)
2. P1 - Quality Control tracking (pre-dispatch QC checklists with photo proof)
3. P2 - Escalation System (auto-flag high-value orders, late deliveries)
4. P2 - Advanced Courier Intelligence (RTO%, damage%, claim rates)
5. P2 - Marketplace Health Monitoring
6. P3 - CRM & Risk Management
