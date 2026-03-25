# FURNIVA CRM - COMPLETE STATUS & ROADMAP
**Last Updated:** March 2026  
**Purpose:** Comprehensive status of all features and clear roadmap for workflow redesign  
**CRITICAL:** This document consolidates ALL information for the next agent

---

## 🚨 URGENT: 4 CRITICAL BUGS TO FIX FIRST

**BEFORE doing anything else, read and fix:** `/app/CRITICAL_BUGS_REMAINING.md`

These bugs block the workflow from functioning:
1. ❌ DamageCategory enum validation error (5 mins to fix)
2. ❌ Failed to fetch replacements (10 mins to fix)
3. ❌ Damage images required for all replacement reasons on backend (10 mins to fix)
4. ❌ Open Returns page shows all historical data + analytics (15 mins to fix)

**Estimated fix time: 60 minutes total**

**After fixing these, continue with the roadmap below.**

---

## 📊 CURRENT STATE SUMMARY

### ✅ FULLY IMPLEMENTED & WORKING (Tested by testing agent)
1. **Core Order Management** - CRUD operations, pagination, filters, search
2. **Amazon/Flipkart/Historical Import** - CSV/TXT imports with comprehensive field mapping
3. **Master SKU System** - SKU mapping, sync with orders, bulk operations
4. **Channel Management** - Amazon, Flipkart, WhatsApp, Website, Phone + custom channels
5. **Inventory Management** - Basic inventory tracking
6. **Task Management** - CRUD, bulk operations, photo upload, order linking
7. **Financial Tracking** - P&L calculation, profit analysis
8. **WhatsApp CRM** - API integration (Meta webhook issue remains)
9. **Analytics Dashboard** - Stats, charts, recent orders
10. **Priority Dashboards** - Dispatch pending, delayed orders, unmapped SKUs
11. **Upload System** - `/api/uploads/damage-image` for damage photo uploads
12. **Edit History** - Backend tracking all changes + frontend display card
13. **Loss Calculation** - Config page with 7 variables, per-order calculation (auto/manual)
14. **Order Cancel/Undo** - Pre-dispatch cancel endpoint, undo status functionality
15. **Claims Management** - Full CRUD + status + documents + correspondence + analytics
16. **Bulk Operations** - Orders and Tasks (bulk delete, bulk update status)

### ⚠️ EXISTS BUT NEEDS COMPLETE REWRITE (Per User's New Requirements)
These exist but follow the OLD workflow and MUST be redesigned:
1. **Return Request System** - Currently uses 12-stage workflow (WRONG)
2. **Replacement System** - Currently basic workflow (WRONG)
3. **ReturnDetail.js** - Frontend page needs rewrite for 3-type workflow
4. **Replacements.js / ReplacementDetail.js** - Frontend needs rewrite for new flow
5. **Return Reason Enums** - Current ReturnReason enum doesn't match new taxonomy
6. **Cancellation Reasons** - Not context-dependent (not based on order status)

### ❌ NOT YET BUILT (User's Requirements)
1. **Cancelled Orders Page** - New main menu page showing all cancelled orders grouped by reason
2. **Resolved Orders Page** - New main menu page for delivered orders with resolved issues
3. **Context-Dependent Cancel/Return/Replacement Buttons** - OrderDetail.js action buttons based on order status
4. **3-Type Return Workflow** - Pre-dispatch, In-transit RTO, Post-delivery
5. **Full/Partial Replacement Workflow** - With pickup tracking + new shipment tracking
6. **Historical Import Reason Mapping** - "Live Status" + "Reason for Cancellation/Replacement" column mapping
7. **"Pickup Not Required" Option** - For severely damaged items (both return + replacement)

---

## 🔴 CRITICAL WORKFLOW REDESIGN (User's Priority #1)

### 📋 REASON TAXONOMY (Context-Dependent)

#### A. POST-DELIVERY Return Reasons (status = "delivered")
When order is already delivered and customer wants to return:
1. `damage` - "Damage"
2. `customer_issues_except_quality` - "Customer Issues (Except Quality)"
3. `hardware_missing` - "Hardware Missing"
4. `defective_product` - "Defective Product"
5. `fraud_customer` - "Fraud Customer"
6. `wrong_product_sent` - "Wrong Product Sent"
7. `customer_quality_issues` - "Customer Quality Issues"
8. `product_delayed_customer_accepted` - "Product Delayed & Customer Accepted"

#### B. IN-TRANSIT Cancel/RTO Reasons (status = "dispatched" / "in_transit")
When order is shipped but not yet delivered (Return to Origin):
1. `customer_refused_doorstep` - "Customer Refused at Doorstep"
2. `customer_unavailable` - "Customer Unavailable"
3. `delay` - "Delay"

#### C. PRE-DISPATCH Cancel Reasons (status = "pending" / "confirmed")
When order has not yet been shipped:
1. `change_of_mind` - "Change of Mind"
2. `found_better_pricing` - "Found Better Pricing"
3. `ordered_mistakenly` - "Ordered Mistakenly"
4. `wants_to_customize` - "Wants to Customize"
5. `did_not_specify` - "Did Not Specify"
6. `customer_not_available` - "Customer not Available"

#### D. REPLACEMENT Reasons
1. `damaged` - "Damaged" → **Sub-options: Full Replacement / Partial Replacement**
2. `quality` - "Quality" → **Sub-options: Full Replacement / Partial Replacement**
3. `wrong_product_sent` - "Wrong Product Sent" → **Full Replacement only**
4. `customer_change_of_mind` - "Customer Change of Mind" → **Full Replacement only + difference amount field (upsell)**

**ALL filing forms MUST include a "Notes" text field for additional details.**

---

## 🗂️ HISTORICAL IMPORT MAPPING RULES

When importing historical orders from CSV, map columns as follows:

| Live Status | Reason for Cancellation/Replacement | Destination Page | Cancellation Reason Value |
|-------------|-------------------------------------|------------------|---------------------------|
| `cancelled` | Empty / blank | **Cancelled Orders → "No Status"** | null |
| `cancelled` | "Status Pending" | **Cancelled Orders → "No Status"** | null |
| `cancelled` | "PFC" or "PFC (DNPC)" | **Cancelled Orders → "Did Not Specify"** | "did_not_specify" |
| `cancelled` | "Damage" | **Cancelled Orders → "Damage"** | "damage" |
| `cancelled` | "Customer Issues (Except Quality)" | **Cancelled Orders → "Customer Issues"** | "customer_issues_except_quality" |
| `cancelled` | "Hardware Missing" | **Cancelled Orders → "Hardware Missing"** | "hardware_missing" |
| `cancelled` | "Defective Product" | **Cancelled Orders → "Defective Product"** | "defective_product" |
| `cancelled` | "Fraud Customer" | **Cancelled Orders → "Fraud Customer"** | "fraud_customer" |
| `cancelled` | "Wrong Product Sent" | **Cancelled Orders → "Wrong Product Sent"** | "wrong_product_sent" |
| `cancelled` | "Customer Quality Issues" | **Cancelled Orders → "Customer Quality Issues"** | "customer_quality_issues" |
| `cancelled` | "Product Delayed & Customer Accepted" | **Cancelled Orders → "Product Delayed"** | "product_delayed_customer_accepted" |
| `delivered` | "Part Damage" / "Full Damage" / "Hardware Missing" / "Minimal Installation Issue" | **Resolved Orders** | Store in special field |
| `delivered` | Empty | Normal Orders (no action) | null |

**CRITICAL:** Historical import code in `/app/backend/routes/order_routes.py` must be updated to handle this mapping.

---

## 🎯 ORDER ACTION FLOW (Context-Dependent Buttons)

On **OrderDetail.js** page, show different action buttons based on current order status:

### Order Status: `pending` or `confirmed` (Pre-Dispatch)
**Show Button:** "Cancel Order"
- Opens modal with PRE-DISPATCH reasons (Section C above)
- Mandatory reason selection + optional notes
- On submit: Creates cancellation record, moves order to Cancelled Orders

### Order Status: `dispatched` or `in_transit` (In Transit)
**Show Button:** "Cancel / RTO" (Return to Origin)
- Opens modal with IN-TRANSIT reasons (Section B above)
- Mandatory reason selection + optional notes
- On submit: Creates RTO (Return to Origin) request

### Order Status: `delivered` (Post-Delivery)
**Show TWO Buttons:**
1. **"Create Return Request"**
   - Opens modal with POST-DELIVERY return reasons (Section A above)
   - Mandatory reason selection + optional notes
   - On submit: Creates return request

2. **"Create Replacement Request"**
   - Opens modal with REPLACEMENT reasons (Section D above)
   - For Damaged/Quality: Sub-choice of Full vs Partial replacement
   - For Customer Change of Mind: Difference amount field (upsell)
   - Mandatory reason + optional notes
   - On submit: Creates replacement request

---

## 🔄 RETURN WORKFLOWS (3 Types)

### Type 1: Pre-Dispatch Cancellation
**Trigger:** Order not yet shipped (pending/confirmed)  
**Flow:**
```
Request Raised → Approve / Close / Reject → DONE
```
**Statuses:** `requested` → `approved` | `closed` | `rejected`  
**Fields:** reason, notes, approved_by, approved_date

---

### Type 2: In-Transit RTO (Return to Origin)
**Trigger:** Order shipped but not delivered (dispatched/in_transit)  
**Flow:**
```
Request Raised → Approve / Close / Reject
  ↓ (if Approved)
RTO Tracking Details (tracking number, courier, rerouting confirmation)
  ↓
Delivered to Warehouse (date)
  ↓ DONE
```
**Statuses:** `requested` → `approved` | `closed` | `rejected` → `rto_in_transit` → `warehouse_received` → `closed`  
**Fields:** reason, notes, rto_tracking_number, rto_courier, warehouse_received_date

---

### Type 3: Post-Delivery Return
**Trigger:** Order delivered  
**Flow:**
```
Return Request Raised → Accept / Close / Reject
  ↓ (if Accepted)
Pickup Details:
  - Pickup Date
  - Pickup Tracking ID
  - Courier
  - OR mark "Pickup Not Required" (for severely damaged items)
  ↓
Pickup Delivered to Warehouse (date)
  ↓
Condition Check: Mint Condition / Damaged Condition
  ↓ DONE (moves to Cancelled Orders with reason)
```
**Statuses:** `requested` → `accepted` | `closed` | `rejected` → `pickup_scheduled` → `pickup_in_transit` → `warehouse_received` → `condition_checked` → `closed`  
**Fields:** reason, notes, pickup_date, pickup_tracking_id, pickup_courier, pickup_not_required (boolean), warehouse_received_date, received_condition (mint/damaged), condition_notes

**IMPORTANT:** "Pickup Not Required" checkbox must skip all pickup phases and go directly to closed.

---

## 📦 REPLACEMENT WORKFLOWS

### Filing a Replacement
**Reasons & Options:**

| Reason | Replacement Type | Extra Fields |
|--------|------------------|--------------|
| Damaged | Full Replacement **OR** Partial Replacement | - |
| Quality | Full Replacement **OR** Partial Replacement | - |
| Wrong Product Sent | Full Replacement **only** | - |
| Customer Change of Mind | Full Replacement **only** | Difference amount (upsell) |

---

### Replacement Flow (Full Replacement):
```
Request Created (reason + full/partial + notes)
  ↓
Pickup Phase:
  - Pickup Date, Pickup Tracking ID, Pickup Courier
  - OR mark "Pickup Not Required"
  ↓
Pickup Status:
  - Delivered to warehouse? (date)
  - In what condition? (mint/damaged)
  ↓
New Shipment Phase:
  - New Tracking ID
  - What is being sent (product details)
  - Courier
  ↓
Replacement Delivered to Customer? (date, confirmation)
  ↓ DONE (Resolved)
```

---

### Replacement Flow (Partial Replacement):
```
Request Created (reason + partial + what parts needed + notes)
  ↓
Pickup Phase (same as above, OR "Pickup Not Required")
  ↓
Pickup Status (same as above)
  ↓
Parts Shipment Phase:
  - What parts are being sent (description)
  - New Tracking ID for parts
  - Courier for parts
  ↓
Parts Delivered to Customer? (date, confirmation)
  ↓ DONE (Resolved)
```

### Replacement Statuses:
`requested` → `approved` | `rejected` → `pickup_scheduled` → `pickup_in_transit` → `warehouse_received` → `new_shipment_dispatched` → `delivered` → `resolved`

**With optional:** `pickup_not_required` flag that skips pickup phases.

---

## 📄 NEW PAGES REQUIRED

### 1. Cancelled Orders Page (`/cancelled-orders`)
**New left menu item:** "Cancelled Orders"  
**What:** All orders with `status = "cancelled"` (from any source — historical import or manually cancelled)

**Grouping/Tabs:**
1. **No Status** — cancelled with no reason or "Status Pending"
2. **Damage**
3. **Customer Issues (Except Quality)**
4. **Hardware Missing**
5. **Defective Product**
6. **Fraud Customer**
7. **Wrong Product Sent**
8. **Customer Quality Issues**
9. **Product Delayed & Customer Accepted**
10. **Did Not Specify** — includes PFC / PFC (DNPC) from historical imports
11. **Pre-Dispatch** — Change of Mind, Found Better Pricing, Ordered Mistakenly, etc.
12. **In-Transit** — Customer Refused, Unavailable, Delay

**Display:** Order count per group, list of orders with details, reason, notes, date cancelled

---

### 2. Resolved Orders Page (`/resolved-orders`)
**New left menu item:** "Resolved Orders"  
**What:** Orders with `status = "delivered"` AND have a value in cancellation_reason/resolution field indicating issue was resolved:
- "Part Damage" → resolved with partial replacement/carpenter
- "Full Damage" → resolved with full replacement
- "Hardware Missing" → resolved by sending hardware
- "Minimal Installation Issue" → resolved with carpenter visit

**Display:** List of resolved orders with:
- Order number, customer, reason, resolution method
- Cost of resolution (if tracked)
- Date resolved

---

## 🔧 BACKEND CHANGES REQUIRED

### 1. Replace Enums in `/app/backend/models.py`

**REMOVE Current:**
```python
class ReturnReason(str, Enum):
    # Current 8 reasons (lines 434-443)
```

**REPLACE WITH:**
```python
class PostDeliveryReturnReason(str, Enum):
    DAMAGE = "damage"
    CUSTOMER_ISSUES_EXCEPT_QUALITY = "customer_issues_except_quality"
    HARDWARE_MISSING = "hardware_missing"
    DEFECTIVE_PRODUCT = "defective_product"
    FRAUD_CUSTOMER = "fraud_customer"
    WRONG_PRODUCT_SENT = "wrong_product_sent"
    CUSTOMER_QUALITY_ISSUES = "customer_quality_issues"
    PRODUCT_DELAYED_CUSTOMER_ACCEPTED = "product_delayed_customer_accepted"

class InTransitCancelReason(str, Enum):
    CUSTOMER_REFUSED_DOORSTEP = "customer_refused_doorstep"
    CUSTOMER_UNAVAILABLE = "customer_unavailable"
    DELAY = "delay"

class PreDispatchCancelReason(str, Enum):
    CHANGE_OF_MIND = "change_of_mind"
    FOUND_BETTER_PRICING = "found_better_pricing"
    ORDERED_MISTAKENLY = "ordered_mistakenly"
    WANTS_TO_CUSTOMIZE = "wants_to_customize"
    DID_NOT_SPECIFY = "did_not_specify"
    CUSTOMER_NOT_AVAILABLE = "customer_not_available"

class ReplacementReason(str, Enum):
    DAMAGED = "damaged"
    QUALITY = "quality"
    WRONG_PRODUCT_SENT = "wrong_product_sent"
    CUSTOMER_CHANGE_OF_MIND = "customer_change_of_mind"

class ReplacementType(str, Enum):
    FULL = "full_replacement"
    PARTIAL = "partial_replacement"
```

**Update ReturnStatus enum (lines 449-472):**
```python
class ReturnStatus(str, Enum):
    # Core statuses
    REQUESTED = "requested"
    APPROVED = "approved"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CLOSED = "closed"
    # In-transit RTO
    RTO_IN_TRANSIT = "rto_in_transit"
    # Post-delivery pickup
    PICKUP_SCHEDULED = "pickup_scheduled"
    PICKUP_IN_TRANSIT = "pickup_in_transit"
    PICKUP_NOT_REQUIRED = "pickup_not_required"
    # Warehouse
    WAREHOUSE_RECEIVED = "warehouse_received"
    CONDITION_CHECKED = "condition_checked"
```

**Update ReplacementStatus enum (lines 591-598):**
```python
class ReplacementStatus(str, Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    PICKUP_SCHEDULED = "pickup_scheduled"
    PICKUP_IN_TRANSIT = "pickup_in_transit"
    PICKUP_NOT_REQUIRED = "pickup_not_required"
    WAREHOUSE_RECEIVED = "warehouse_received"
    NEW_SHIPMENT_DISPATCHED = "new_shipment_dispatched"
    PARTS_SHIPPED = "parts_shipped"  # For partial replacement
    DELIVERED = "delivered"
    RESOLVED = "resolved"
```

---

### 2. Update ReturnRequest Model (lines 485-574)

**Add these fields:**
```python
class ReturnRequest(BaseModel):
    # ... existing fields ...
    
    # NEW FIELDS:
    return_type: str  # "pre_dispatch" | "in_transit" | "post_delivery"
    cancellation_reason: Optional[str] = None  # Actual reason value from appropriate enum
    notes: Optional[str] = None
    
    # Pickup phase (post-delivery only)
    pickup_not_required: bool = False
    pickup_date: Optional[datetime] = None
    pickup_tracking_id: Optional[str] = None
    pickup_courier: Optional[str] = None
    
    # Warehouse phase
    warehouse_received_date: Optional[datetime] = None
    received_condition: Optional[str] = None  # "mint" | "damaged"
    condition_notes: Optional[str] = None
    
    # RTO phase (in-transit only)
    rto_tracking_number: Optional[str] = None
    rto_courier: Optional[str] = None
```

---

### 3. Update ReplacementRequest Model (lines 600-626)

**Add these fields:**
```python
class ReplacementRequest(BaseModel):
    # ... existing fields ...
    
    # NEW FIELDS:
    replacement_type: str  # "full_replacement" | "partial_replacement"
    replacement_reason: str  # from ReplacementReason enum
    difference_amount: Optional[float] = None  # For customer change of mind upsell
    notes: Optional[str] = None
    
    # Pickup phase
    pickup_not_required: bool = False
    pickup_date: Optional[datetime] = None
    pickup_tracking_id: Optional[str] = None
    pickup_courier: Optional[str] = None
    warehouse_received_date: Optional[datetime] = None
    received_condition: Optional[str] = None  # "mint" | "damaged"
    condition_notes: Optional[str] = None
    
    # New shipment phase
    new_tracking_id: Optional[str] = None
    new_courier: Optional[str] = None
    items_sent_description: Optional[str] = None
    
    # Partial replacement specific
    parts_description: Optional[str] = None
    parts_tracking_id: Optional[str] = None
    parts_courier: Optional[str] = None
    
    # Delivery phase
    delivered_date: Optional[datetime] = None
    delivery_confirmed: bool = False
```

---

### 4. Backend Routes to Modify

#### `/app/backend/routes/return_routes.py` - FULL REWRITE REQUIRED
Current: 12-stage workflow (WRONG)  
Required:
- `POST /api/return-requests/` - Create with return_type detection based on order status
- `PATCH /{id}/workflow/advance` - Context-aware validation (3 different flows)
- `GET /{id}/workflow-stages` - Return allowed next transitions based on return_type
- Handle `pickup_not_required` flag to skip pickup phases

#### `/app/backend/routes/replacement_routes.py` - FULL REWRITE REQUIRED
Current: Basic workflow  
Required:
- `POST /api/replacement-requests/` - Validate reason → replacement type options
- `PATCH /{id}/advance` - Handle full vs partial flows, pickup_not_required
- Track pickup phase + new shipment phase separately

#### `/app/backend/routes/order_routes.py` - UPDATE IMPORT LOGIC
Required:
- Update historical import mapping (around line 268-292)
- Map "Reason for Cancellation/Replacement" column to correct reason enum
- Map "PFC"/"PFC (DNPC)" → "did_not_specify"
- Map delivered + damage reasons → mark for Resolved Orders
- Validate cancellation_reason matches order status context

#### **NEW:** `/app/backend/routes/cancelled_orders_routes.py` (or add to order_routes.py)
Required:
- `GET /api/cancelled-orders/` - List all cancelled orders
- `GET /api/cancelled-orders/stats` - Counts per reason group
- `GET /api/cancelled-orders/grouped` - Grouped by cancellation reason

#### **NEW:** `/app/backend/routes/resolved_orders_routes.py` (or add to order_routes.py)
Required:
- `GET /api/resolved-orders/` - List all resolved orders
- `GET /api/resolved-orders/stats` - Counts and resolution cost summary

---

## 🎨 FRONTEND CHANGES REQUIRED

### Pages to CREATE:
1. **`/app/frontend/src/pages/CancelledOrders.js`** 
   - Route: `/cancelled-orders`
   - Tabbed view grouped by cancellation reason (12 tabs)
   - Display order count per tab, list of orders with details

2. **`/app/frontend/src/pages/ResolvedOrders.js`**
   - Route: `/resolved-orders`
   - List of resolved orders with resolution details and costs

### Pages to REWRITE:
3. **`/app/frontend/src/pages/ReturnDetail.js`**
   - Rewrite for 3-type workflow with context-aware stepper
   - Pre-dispatch: Simple approve/reject flow
   - In-transit: RTO tracking flow
   - Post-delivery: Pickup + condition check flow
   - Handle "Pickup Not Required" checkbox

4. **`/app/frontend/src/pages/ReplacementDetail.js`**
   - Rewrite for full/partial replacement flow
   - Pickup phase (with "Pickup Not Required" option)
   - New shipment/parts shipment tracking
   - Delivery confirmation

5. **`/app/frontend/src/pages/Replacements.js`**
   - Update for new replacement statuses and flow

### Pages to MODIFY:
6. **`/app/frontend/src/pages/OrderDetail.js`**
   - Replace action buttons based on order status:
     - Pre-dispatch: Show "Cancel Order" button → modal with pre-dispatch reasons
     - In-transit: Show "Cancel / RTO" button → modal with in-transit reasons
     - Delivered: Show TWO buttons ("Create Return" + "Create Replacement") → respective modals
   - ALL modals must include:
     - Reason dropdown (context-appropriate options)
     - Notes text field (optional)
     - For replacements: Sub-choice for full/partial (if applicable)
     - For customer change of mind: Difference amount field

7. **`/app/frontend/src/pages/Returns.js`**
   - Update status labels for new workflow statuses
   - Add filters for return_type (pre_dispatch, in_transit, post_delivery)

8. **`/app/frontend/src/App.js`**
   - Add routes: `/cancelled-orders`, `/resolved-orders`

9. **`/app/frontend/src/components/Layout.js`**
   - Add nav items: "Cancelled Orders" and "Resolved Orders" (after Orders, before Returns)

---

## 📝 NEW NAVIGATION STRUCTURE

Updated left sidebar menu (in order):
```
Dashboard
Orders
Inventory
Cancelled Orders    ← NEW
Resolved Orders     ← NEW
Returns             (reworked)
Replacements        (reworked)
Claims
Costing
Channels
Tasks
Analytics
WhatsApp
Settings
Team
```

---

## ✅ IMPLEMENTATION ORDER (CRITICAL - Must Follow)

**Phase 1: Backend Models (1-2 hours)**
1. Update enums in `/app/backend/models.py` (reason taxonomy)
2. Add new fields to ReturnRequest model
3. Add new fields to ReplacementRequest model
4. Test models can be instantiated

**Phase 2: Backend Routes - Returns (2-3 hours)**
5. Rewrite `/app/backend/routes/return_routes.py` with 3-type workflow
6. Implement context-aware validation (check order status)
7. Implement workflow/advance endpoint with proper state transitions
8. Test all return endpoints with curl/Postman

**Phase 3: Backend Routes - Replacements (2-3 hours)**
9. Rewrite `/app/backend/routes/replacement_routes.py` for full/partial flow
10. Handle pickup_not_required flag
11. Test all replacement endpoints

**Phase 4: Backend Routes - Orders & New Endpoints (1-2 hours)**
12. Update historical import mapping in `/app/backend/routes/order_routes.py`
13. Create cancelled orders endpoints (or add to order_routes)
14. Create resolved orders endpoints (or add to order_routes)
15. Test import with sample CSV

**Phase 5: Backend Testing (1 hour)**
16. Call `deep_testing_backend_v2` to test all backend changes
17. Fix any issues found

**Phase 6: Frontend - OrderDetail Action Buttons (1-2 hours)**
18. Modify `/app/frontend/src/pages/OrderDetail.js`
19. Add context-dependent action buttons
20. Create modals for cancel/return/replacement with appropriate reason dropdowns
21. Test button visibility based on order status

**Phase 7: Frontend - New Pages (2-3 hours)**
22. Create `/app/frontend/src/pages/CancelledOrders.js` with tabs
23. Create `/app/frontend/src/pages/ResolvedOrders.js`
24. Add routes to App.js
25. Add nav items to Layout.js

**Phase 8: Frontend - Rewrite Detail Pages (3-4 hours)**
26. Rewrite `/app/frontend/src/pages/ReturnDetail.js` for 3-type workflow
27. Rewrite `/app/frontend/src/pages/ReplacementDetail.js` for full/partial flow
28. Update `/app/frontend/src/pages/Returns.js` for new statuses
29. Update `/app/frontend/src/pages/Replacements.js` for new statuses

**Phase 9: Frontend Testing (1 hour)**
30. Test end-to-end flows:
    - Pre-dispatch cancel
    - In-transit RTO
    - Post-delivery return
    - Full replacement
    - Partial replacement
31. Test historical import UI
32. Test new pages (Cancelled Orders, Resolved Orders)

**Phase 10: Documentation Update (30 mins)**
33. Update test_result.md with new tasks
34. Mark old workflow as deprecated

**Total Estimated Time: 16-22 hours**

---

## 🚨 CRITICAL NOTES FOR NEXT AGENT

### DO NOT START UNTIL:
1. ✅ User confirms this roadmap
2. ✅ All existing features are tested and working
3. ✅ Dependencies are installed and services running

### WHILE IMPLEMENTING:
1. **Follow the implementation order EXACTLY** - backend first, then frontend
2. **Test each phase before moving to next** - use `deep_testing_backend_v2` after backend changes
3. **DO NOT modify any working features** unless specifically related to workflow redesign
4. **Keep existing URLs and endpoints working** - add new ones, don't break old ones
5. **Handle backward compatibility** - existing returns/replacements should still display

### TESTING CHECKLIST:
After implementation, test these scenarios:
- [ ] Import historical CSV with cancellation reasons → orders appear in Cancelled Orders page grouped correctly
- [ ] Create new order (pending) → "Cancel Order" button shows → select reason → order moves to Cancelled Orders
- [ ] Mark order as dispatched → "Cancel / RTO" button shows → select in-transit reason → RTO flow works
- [ ] Mark order as delivered → TWO buttons show (Return + Replacement) → both flows work end-to-end
- [ ] Post-delivery return with "Pickup Not Required" → flow skips pickup phases correctly
- [ ] Full replacement flow → pickup + new shipment tracking works
- [ ] Partial replacement flow → pickup + parts shipment tracking works
- [ ] Cancelled Orders page → all groups display correctly with counts
- [ ] Resolved Orders page → orders show correctly

### FILES REFERENCE:
**Backend:**
- `/app/backend/models.py` - Lines 434-598 (enums and models)
- `/app/backend/routes/return_routes.py` - Full rewrite
- `/app/backend/routes/replacement_routes.py` - Full rewrite
- `/app/backend/routes/order_routes.py` - Lines 268-292 (import), add validation

**Frontend:**
- `/app/frontend/src/pages/OrderDetail.js` - Add context buttons
- `/app/frontend/src/pages/ReturnDetail.js` - Full rewrite
- `/app/frontend/src/pages/ReplacementDetail.js` - Full rewrite
- `/app/frontend/src/pages/Returns.js` - Update statuses
- `/app/frontend/src/pages/Replacements.js` - Update statuses
- `/app/frontend/src/App.js` - Add routes
- `/app/frontend/src/components/Layout.js` - Add nav items

**New Files to Create:**
- `/app/frontend/src/pages/CancelledOrders.js`
- `/app/frontend/src/pages/ResolvedOrders.js`

---

## 🔮 FUTURE PHASES (After Workflow Redesign)

These should ONLY be started AFTER the workflow redesign above is fully implemented and tested:

### Phase 2: Claims Enhancement
- Link claims to specific return/replacement requests
- Auto-file courier damage claims when QC shows damage
- Track claim amounts vs approved amounts

### Phase 3: Loss Calculation Refinement
- Tie loss calculation to new return/replacement workflows
- Separate loss tracking for returns vs replacements
- Dashboard showing total losses by category

### Phase 4: Dashboard Enhancements
- Cancelled Orders summary cards
- Resolved Orders summary cards
- Return/Replacement pipeline visualization
- Loss trending charts

### Phase 5: Advanced Analytics
- Return rate by product/SKU
- Cancellation patterns by reason
- Courier damage frequency
- Customer risk scoring

### Phase 6: Installation Management
- Track carpenter visits for resolved orders
- Installation scheduling
- Installation cost tracking

### Phase 7: Courier Intelligence
- Courier performance scoring
- Damage rate per courier
- Auto-route based on courier reliability

---

## 📞 CONTACT & HANDOFF

**For the next agent:**
This document contains EVERYTHING needed to implement the workflow redesign. Please:
1. Read this document completely before starting
2. Read `/app/WORKFLOW_SPECIFICATION.md` for additional context
3. Check `/app/test_result.md` for testing protocol
4. Ask user for confirmation before starting implementation
5. Follow the implementation order strictly
6. Test thoroughly after each phase

**User's Original Request Summary:**
User wants the cancelled/return/replacement workflow completely redesigned to be context-dependent based on order status (pre-dispatch, in-transit, delivered). They want new "Cancelled Orders" and "Resolved Orders" pages. Historical import must map cancellation reasons correctly. Pickup should have "Pickup Not Required" option for severe damage cases. Replacement must support full/partial options.

---

**END OF DOCUMENT**
