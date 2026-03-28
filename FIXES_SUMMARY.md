# Bug Fixes & New Features Summary

## Issues Fixed

### 1. ✅ Historical Order Auto-Confirmation Bug
**Problem:** Orders imported with "Order Conf Calling" marked as done were showing status as "pending" and asking to confirm order again.

**Root Cause:** Status mapping was setting default to "delivered" before checking order confirmation status.

**Fix Applied:**
- Added "pending": "pending" to status_mapping dictionary
- Changed default status from "delivered" to "pending"
- Auto-confirmation logic now properly upgrades status from "pending" to "confirmed" when order_conf_calling is true
- Added note in internal_notes: "Auto-confirmed: Order confirmation call marked as done"

**Files Modified:**
- `/app/backend/routes/order_routes.py` (lines 431-462)

---

### 2. ✅ Replacement Original Tracking Details Bug
**Problem:** Replacement overview page not showing original tracking number and courier from the original order.

**Root Cause:** Field name mismatch - code was looking for "courier_name" but orders have "courier_partner" field.

**Fix Applied:**
- Updated replacement creation to capture `original_tracking_number` and `original_courier` from order
- Fixed field name from `courier_name` to `courier_partner` (with fallback to courier_name)
- Added enrichment logic to populate existing replacements with original shipment details
- Updated frontend to display both original shipment details (blue box) and new replacement tracking (green box)

**Files Modified:**
- `/app/backend/routes/replacement_routes.py` (lines 75-77, 177-194)
- `/app/frontend/src/pages/Replacements.js` (lines 398-427)

---

### 3. ✅ SKU Mapping Not Updating Orders
**Problem:** After importing SKU/ASIN mappings via CSV, they showed in listings but orders still displayed "SKU Not Mapped" and dashboard showed "120 SKU(s) need Master SKU assignment".

**Fix Applied:**
- Added automatic SKU sync after CSV import
- Maps platform_product_id (ASIN) to master_sku
- Updates all orders with matching ASINs
- Returns count of orders synced in import response
- Added new endpoint: `POST /api/inventory/sync-skus-to-orders` for manual sync anytime

**Files Modified:**
- `/app/backend/routes/inventory_routes.py` (lines 146-182, 220-267)

**Usage:**
```bash
# Import SKU CSV - automatically syncs orders
POST /api/inventory/bulk-import-csv

# Manual sync anytime
POST /api/inventory/sync-skus-to-orders
```

---

### 4. ✅ Initial Stock Entry Feature (NEW)
**Problem:** No way to add previous procurement or current stock manually for historical inventory tracking.

**Solution:** Added new endpoint to manually enter initial stock/procurement.

**Endpoint:** `POST /api/inventory/initial-stock-entry`

**Parameters:**
- `master_sku` (required): The SKU to add stock for
- `warehouse_code` (required): Warehouse code (e.g., WH-MAIN)
- `initial_quantity` (required): Stock quantity to add
- `procurement_date` (optional): Date of procurement
- `procurement_cost` (optional): Cost per unit
- `supplier` (optional): Supplier name
- `notes` (optional): Additional notes

**Features:**
- Creates procurement record marked as "initial stock"
- Updates warehouse stock (adds to existing quantity)
- Creates audit log entry for tracking
- Returns updated stock levels

**Example:**
```bash
POST /api/inventory/initial-stock-entry?master_sku=FRN-CHAIR-001&warehouse_code=WH-MAIN&initial_quantity=500&procurement_date=2025-01-01&supplier=Previous%20Stock&notes=Opening%20stock%20from%20old%20system
```

**Files Modified:**
- `/app/backend/routes/inventory_routes.py` (lines 1590-1682)

---

### 5. ✅ Delayed Orders Dashboard Tile (NEW)
**Problem:** No visibility for orders that are dispatched but past their delivery date.

**Solution:** Added "Delayed Orders" tile to dashboard.

**Features:**
- Shows count of orders with status="dispatched" and delivery_by date in the past
- Purple/fuchsia colored tile for high visibility
- Clickable - navigates to dispatched orders page
- Updates in real-time with dashboard stats

**Files Modified:**
- `/app/backend/models.py` (line 892)
- `/app/backend/routes/dashboard_routes.py` (lines 46-52, 78)
- `/app/frontend/src/pages/Dashboard.js` (lines 148-158)

---

## Testing Instructions

### Test 1: Auto-Confirmation
1. Import a CSV with: Order Number=TEST-001, Order Conf Calling=Yes, Live Status=Pending
2. Check order - status should be "confirmed" (not pending)
3. Check internal_notes - should mention "Auto-confirmed"

### Test 2: Replacement Tracking
1. Create a replacement request for an order that has tracking_number and courier_partner
2. View replacement on /replacements page
3. Should see blue box with "Original Shipment Details" showing original tracking and courier

### Test 3: SKU Sync
1. Import SKU CSV with ASINs matching your orders
2. Check response - should show "orders_synced" count
3. Visit dashboard - "Unmapped SKUs" count should decrease
4. View orders - should show master_sku instead of "SKU Not Mapped"
5. Can also manually sync: POST /api/inventory/sync-skus-to-orders

### Test 4: Initial Stock Entry
1. Make sure you have a warehouse (create one if needed)
2. POST /api/inventory/initial-stock-entry with SKU, warehouse, quantity
3. Check warehouse stock - should show the quantity
4. Check audit log - should show "Initial stock entry"
5. Delivered orders will deduct from this stock

### Test 5: Delayed Orders
1. View dashboard
2. Look for "Delayed Orders" tile (purple/fuchsia color)
3. Shows count of dispatched orders past delivery date
4. Click tile - goes to dispatched orders page

---

## API Endpoints Summary

### New Endpoints:
1. `POST /api/inventory/sync-skus-to-orders` - Manually sync SKUs to orders
2. `POST /api/inventory/initial-stock-entry` - Add historical/opening stock

### Modified Endpoints:
1. `POST /api/inventory/bulk-import-csv` - Now auto-syncs orders after import
2. `GET /api/dashboard/stats` - Now includes `delayed_orders` count
3. `POST /api/orders/import-historical` - Auto-confirms orders with confirmation call done
4. `POST /api/replacement-requests/` - Captures original tracking/courier
5. `GET /api/replacement-requests/` - Enriches with original shipment details

---

## Database Fields Added

### Replacement Requests Collection:
- `original_tracking_number`: String (from order.tracking_number)
- `original_courier`: String (from order.courier_partner)

### Procurements Collection (New):
- `is_initial_stock`: Boolean (marks initial stock entries)

---

## Known Working Features
- CSV template download for inventory (fixed in Phase 4)
- Multi-warehouse management UI (completed in Phase 4)
- Cycle counts UI (completed in Phase 4)
- Shrinkage detection UI (completed in Phase 4)
- Audit log UI (completed in Phase 4)

---

## Next Steps for User

1. **Test Historical Order Import:**
   - Import orders with "Order Conf Calling" = Yes
   - Verify they show as "confirmed"

2. **Test SKU Sync:**
   - Import your SKU/ASIN mappings CSV
   - Check if orders get mapped automatically
   - If needed, call sync endpoint manually

3. **Add Initial Stock:**
   - Create warehouses if not done
   - Use initial-stock-entry endpoint to add opening stock
   - This sets the baseline for stock calculations

4. **Monitor Delayed Orders:**
   - Check dashboard tile daily
   - Track dispatched orders past delivery date

5. **Verify Replacements:**
   - Create/view replacement requests
   - Confirm original tracking details appear

---

**All fixes are deployed and backend is running. Frontend hot reload will pick up changes automatically.**
