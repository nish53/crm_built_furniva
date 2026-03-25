# FURNIVA CRM - COMPLETE WORKFLOW SPECIFICATION & ROADMAP
**Last Updated:** July 2025  
**Status:** Phase 1 (Workflow Redesign) - NOT YET IMPLEMENTED  
**Purpose:** This document is the SINGLE SOURCE OF TRUTH for all workflow logic. Any new agent must follow this exactly.

---

## TABLE OF CONTENTS
1. [What's Done (Current State)](#whats-done)
2. [New Navigation Structure](#navigation)
3. [Cancellation Reason Taxonomy](#reason-taxonomy)
4. [Historical Import Mapping](#historical-import)
5. [Order Action Flow (Context-Dependent)](#order-action-flow)
6. [Return Workflows (3 Types)](#return-workflows)
7. [Replacement Workflows](#replacement-workflows)
8. [Resolved Orders](#resolved-orders)
9. [Cancelled Orders Page](#cancelled-orders)
10. [Backend Model Changes Required](#backend-models)
11. [Backend Route Changes Required](#backend-routes)
12. [Frontend Changes Required](#frontend-changes)
13. [Future Phases (After Workflow)](#future-phases)

---

## 1. WHAT'S DONE (Current State) <a name="whats-done"></a>

### ✅ Completed & Working
- **Core CRM**: Orders CRUD, import (CSV/historical), pagination, search, filters
- **Master SKU**: SKU management, sync with orders
- **Channels**: Amazon, Flipkart, WhatsApp, Website, Phone channel management
- **Inventory**: Basic inventory tracking
- **Costing**: Order costing/pricing
- **Analytics**: Basic analytics dashboard
- **Tasks**: Task management
- **WhatsApp CRM**: WhatsApp integration
- **Upload Routes**: `/api/uploads/damage-image` - local file storage for images (single + bulk upload)
- **Edit History**: Backend tracks all order field changes, frontend card on OrderDetail
- **Loss Calculation Config**: Settings page with 7 configurable variables
- **Loss Calculation**: Calculate per-order loss with auto/manual modes
- **Order Cancel/Undo**: Cancel endpoint (pre-dispatch), undo status endpoint, previous_status tracking
- **Claims Backend**: Full CRUD + status management + documents + correspondence + analytics

### ⚠️ EXISTS BUT NEEDS COMPLETE REWRITE (per this spec)
- **Return Request System** - Current 12-stage workflow is WRONG. Must be replaced with 3-type workflow below.
- **Replacement System** - Current workflow stages are WRONG. Must be replaced with workflow below.
- **ReturnDetail.js** - Must be rewritten for new 3-type workflow.
- **Replacements.js / ReplacementDetail.js** - Must be rewritten for new replacement flow.
- **Return reasons/enums** - Must be replaced with context-dependent reasons below.
- **Claims.js** - Built but may need adjustment after workflow redesign.

### ❌ NOT YET BUILT
- **Cancelled Orders page** (new main menu item)
- **Resolved Orders page** (new main menu item)
- **Context-dependent cancel/return/replacement buttons on OrderDetail**
- **3-type return workflow** (pre-dispatch, in-transit, post-delivery)
- **Full replacement workflow** (full vs partial, pickup + new shipment tracking)

---

## 2. NEW NAVIGATION STRUCTURE <a name="navigation"></a>

Left sidebar menu (in order):
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

## 3. CANCELLATION REASON TAXONOMY <a name="reason-taxonomy"></a>

Reasons are CONTEXT-DEPENDENT based on order status at time of filing:

### A. Post-Delivery Cancellation/Return Reasons (order status = "delivered")
These are for orders that were shipped, delivered, and now being returned:
1. `damage` - "Damage"
2. `customer_issues_except_quality` - "Customer Issues (Except Quality)"
3. `hardware_missing` - "Hardware Missing"
4. `defective_product` - "Defective Product"
5. `fraud_customer` - "Fraud Customer"
6. `wrong_product_sent` - "Wrong Product Sent"
7. `customer_quality_issues` - "Customer Quality Issues"
8. `product_delayed_customer_accepted` - "Product Delayed & Customer Accepted"

### B. In-Transit Cancellation/RTO Reasons (order status = "dispatched" / "in_transit")
These are for orders shipped but NOT yet delivered — Return to Origin:
1. `customer_refused_doorstep` - "Customer Refused at Doorstep"
2. `customer_unavailable` - "Customer Unavailable"
3. `delay` - "Delay"

### C. Pre-Dispatch Cancellation Reasons (order status = "pending" / "confirmed")
These are for orders NOT yet shipped:
1. `change_of_mind` - "Change of Mind"
2. `found_better_pricing` - "Found Better Pricing"
3. `ordered_mistakenly` - "Ordered Mistakenly"
4. `wants_to_customize` - "Wants to Customize"
5. `did_not_specify` - "Did Not Specify"
6. `customer_not_available` - "Customer not Available"

### D. Replacement Filing Reasons
1. `damaged` - "Damaged" → sub-options: Full Replacement / Partial Replacement
2. `quality` - "Quality" → sub-options: Full Replacement / Partial Replacement
3. `wrong_product_sent` - "Wrong Product Sent" → Full Replacement only
4. `customer_change_of_mind` - "Customer Change of Mind" → Full Replacement only + difference amount field (upsell)

### ALL filing forms include a "Notes" text field for additional details.

---

## 4. HISTORICAL IMPORT MAPPING <a name="historical-import"></a>

When importing historical orders from CSV:

| Live Status Column | Reason for Cancellation/Replacement Column | Maps To |
|---|---|---|
| `cancelled` | Empty / blank | **Cancelled Orders → "No Status"** group |
| `cancelled` | "Status Pending" | **Cancelled Orders → "No Status"** group |
| `cancelled` | "PFC" or "PFC (DNPC)" | **Cancelled Orders → "Did Not Specify"** group (pre-dispatch cancel, no valid reason available for historical) |
| `cancelled` | "Damage" | **Cancelled Orders → "Damage"** group |
| `cancelled` | "Customer Issues (Except Quality)" | **Cancelled Orders → "Customer Issues (Except Quality)"** group |
| `cancelled` | "Hardware Missing" | **Cancelled Orders → "Hardware Missing"** group |
| `cancelled` | "Defective Product" | **Cancelled Orders → "Defective Product"** group |
| `cancelled` | "Fraud Customer" | **Cancelled Orders → "Fraud Customer"** group |
| `cancelled` | "Wrong Product Sent" | **Cancelled Orders → "Wrong Product Sent"** group |
| `cancelled` | "Customer Quality Issues" | **Cancelled Orders → "Customer Quality Issues"** group |
| `cancelled` | "Product Delayed & Customer Accepted" | **Cancelled Orders → "Product Delayed & Customer Accepted"** group |
| `delivered` | "Part Damage" / "Full Damage" / "Hardware Missing" / "Minimal Installation Issue" / etc. | **Resolved Orders** (issues resolved with minimal charges/carpenter/replacement) |
| `delivered` | Empty | Normal delivered order (no action) |

**IMPORTANT:** The historical import code in `order_routes.py` must map the "Reason for Cancellation/Replacement" column to the correct cancellation_reason enum value and route the order to the correct page.

---

## 5. ORDER ACTION FLOW (Context-Dependent) <a name="order-action-flow"></a>

On the **OrderDetail.js** page, action buttons shown depend on current order status:

### Order Status: `pending` or `confirmed` (Pre-Dispatch)
**Show:** "Cancel Order" button
- Opens modal with PRE-DISPATCH reasons (Section 3C above)
- Mandatory reason selection + optional notes
- On submit: Creates cancellation record, moves order to Cancelled Orders

### Order Status: `dispatched` or `in_transit` (In Transit)
**Show:** "Cancel / RTO" button
- Opens modal with IN-TRANSIT reasons (Section 3B above)
- Mandatory reason selection + optional notes
- On submit: Creates RTO (Return to Origin) request

### Order Status: `delivered` (Post-Delivery)
**Show TWO buttons:**
1. **"Create Return Request"** button
   - Opens modal with POST-DELIVERY return reasons (Section 3A above)
   - Mandatory reason selection + optional notes
   - On submit: Creates return request
   
2. **"Create Replacement Request"** button
   - Opens modal with REPLACEMENT reasons (Section 3D above)
   - For Damaged/Quality: Sub-choice of Full vs Partial replacement
   - For Customer Change of Mind: Difference amount field
   - Mandatory reason + optional notes
   - On submit: Creates replacement request

---

## 6. RETURN WORKFLOWS (3 Types) <a name="return-workflows"></a>

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

**IMPORTANT:** In ALL pickup scenarios (return + replacement), there must be an option to mark **"Pickup Not Required"** — for cases where damage is huge and pickup is not worth it. When marked, flow skips to closed.

---

## 7. REPLACEMENT WORKFLOWS <a name="replacement-workflows"></a>

### Filing a Replacement
**Reasons & Sub-options:**
| Reason | Replacement Type | Extra Fields |
|---|---|---|
| Damaged | Full Replacement OR Partial Replacement | - |
| Quality | Full Replacement OR Partial Replacement | - |
| Wrong Product Sent | Full Replacement only | - |
| Customer Change of Mind | Full Replacement only | Difference amount (upsell) |

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
  ↓ DONE
```

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
  ↓ DONE
```

### Replacement Statuses:
`requested` → `approved` | `rejected` → `pickup_scheduled` → `pickup_in_transit` → `warehouse_received` → `new_shipment_dispatched` → `delivered` → `resolved`

With optional: `pickup_not_required` flag that skips pickup phases.

---

## 8. RESOLVED ORDERS <a name="resolved-orders"></a>

**New page:** `/resolved-orders`  
**Nav item:** "Resolved Orders" in left menu

**What goes here:**
- Orders with `status = "delivered"` AND have a value in `cancellation_reason` / `Reason for Cancellation/Replacement` that indicates the issue was resolved:
  - "Part Damage" → resolved with partial replacement/carpenter
  - "Full Damage" → resolved with full replacement
  - "Hardware Missing" → resolved by sending hardware
  - "Minimal Installation Issue" → resolved with carpenter visit
  - Any similar resolved-with-service reasons

**Display:** List of resolved orders with:
- Order number, customer, reason, resolution method
- Cost of resolution (if tracked)
- Date resolved

---

## 9. CANCELLED ORDERS PAGE <a name="cancelled-orders"></a>

**New page:** `/cancelled-orders`  
**Nav item:** "Cancelled Orders" in left menu

**What goes here:** All orders with `status = "cancelled"` (from any source — historical import or manually cancelled)

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

**Each group shows:** Order count, list of orders with details, reason, notes, date cancelled

---

## 10. BACKEND MODEL CHANGES REQUIRED <a name="backend-models"></a>

### Replace `ReturnReason` enum:
```python
# REMOVE the old ReturnReason enum entirely
# REPLACE with context-dependent reason enums:

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

### Replace `ReturnStatus` enum:
```python
class ReturnStatus(str, Enum):
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

### Replace `ReplacementStatus` enum:
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
    DELIVERED = "delivered"
    RESOLVED = "resolved"
```

### Update `ReturnRequest` model:
Add fields:
- `return_type`: "pre_dispatch" | "in_transit" | "post_delivery"
- `cancellation_reason`: string (the actual reason from the appropriate enum)
- `notes`: string
- `pickup_not_required`: boolean (default false)
- `pickup_date`, `pickup_tracking_id`, `pickup_courier`
- `warehouse_received_date`
- `received_condition`: "mint" | "damaged"
- `condition_notes`: string
- `rto_tracking_number`, `rto_courier` (for in-transit RTO)

### Update `ReplacementRequest` model:
Add fields:
- `replacement_type`: "full_replacement" | "partial_replacement"
- `replacement_reason`: from ReplacementReason enum
- `difference_amount`: float (for customer change of mind upsell)
- `pickup_not_required`: boolean
- `pickup_date`, `pickup_tracking_id`, `pickup_courier`
- `warehouse_received_date`, `received_condition`, `condition_notes`
- `new_tracking_id`, `new_courier`, `items_sent_description`
- `parts_description` (for partial: what parts being sent)
- `parts_tracking_id`, `parts_courier` (for partial)
- `delivered_date`, `delivery_confirmed`: boolean

---

## 11. BACKEND ROUTE CHANGES REQUIRED <a name="backend-routes"></a>

### `/api/return-requests/` — REWRITE
- `POST /` — Create return request. Backend must:
  1. Check order status to determine return_type (pre_dispatch/in_transit/post_delivery)
  2. Validate reason matches the order status context
  3. Store return_type on the request
- `GET /` — List with filters (return_type, status, reason)
- `GET /{id}` — Get single
- `PATCH /{id}/workflow/advance` — Advance with context-aware validation:
  - Pre-dispatch: only allow requested → approved/closed/rejected
  - In-transit: requested → approved/closed/rejected → rto_in_transit → warehouse_received → closed
  - Post-delivery: requested → accepted/closed/rejected → pickup_scheduled → pickup_in_transit → warehouse_received → condition_checked → closed
  - Handle `pickup_not_required` flag to skip pickup phases
- `GET /{id}/workflow-stages` — Return allowed next transitions based on return_type + current status

### `/api/replacement-requests/` — REWRITE
- `POST /` — Create replacement. Validate:
  - Reason determines if full/partial choice is available
  - For customer_change_of_mind: require difference_amount field
- `PATCH /{id}/advance` — Advance through: approved → pickup → warehouse → new_shipment → delivered → resolved
  - Handle pickup_not_required
  - Handle partial vs full shipment tracking

### `/api/orders/` — UPDATE
- Historical import must map "Reason for Cancellation/Replacement" column to correct reason enum
- Map "PFC"/"PFC (DNPC)" → "did_not_specify" for pre-dispatch
- Map delivered + damage reasons → resolved orders

### NEW: `/api/cancelled-orders/` 
- `GET /` — List cancelled orders grouped by reason
- `GET /stats` — Counts per reason group

### NEW: `/api/resolved-orders/`
- `GET /` — List resolved orders
- `GET /stats` — Counts and resolution cost summary

---

## 12. FRONTEND CHANGES REQUIRED <a name="frontend-changes"></a>

### New Pages:
1. **`CancelledOrders.js`** — `/cancelled-orders` — Tabbed view grouped by cancellation reason
2. **`ResolvedOrders.js`** — `/resolved-orders` — List of resolved orders with resolution details

### Rewrite Pages:
3. **`ReturnDetail.js`** — Rewrite for 3-type workflow with context-aware stepper
4. **`ReplacementDetail.js`** — Rewrite for full/partial replacement flow with pickup + shipment tracking
5. **`Replacements.js`** — Update for new replacement statuses and flow

### Modify Pages:
6. **`OrderDetail.js`** — Replace action buttons:
   - Pre-dispatch: Show "Cancel Order" with pre-dispatch reasons
   - In-transit: Show "Cancel / RTO" with in-transit reasons
   - Delivered: Show "Create Return" AND "Create Replacement" buttons with respective reasons
   - ALL filing modals must include reason dropdown (context-appropriate) + notes field
7. **`Returns.js`** — Update status labels and filters for new workflow
8. **`App.js`** — Add routes for `/cancelled-orders`, `/resolved-orders`
9. **`Layout.js`** — Add "Cancelled Orders" and "Resolved Orders" nav items

---

## 13. FUTURE PHASES (After Workflow Redesign) <a name="future-phases"></a>

These should ONLY be started AFTER the workflow redesign above is fully implemented and tested:

### Phase 2: Claims System Enhancement
- Link claims to specific return/replacement requests
- Auto-file courier damage claims when QC shows damage
- Track claim amounts vs approved amounts

### Phase 3: Loss Calculation Refinement
- Per-order loss calculation tied to new return/replacement workflows
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

### Phase 7: Courier Intelligence (Deferred)
- Courier performance scoring
- Damage rate per courier
- Auto-route based on courier reliability

---

## IMPLEMENTATION ORDER (for next agent)

**MUST follow this order:**

1. **Backend models** — Replace enums and update models (Section 10)
2. **Backend routes: return_routes.py** — Rewrite with 3-type workflow (Section 11)
3. **Backend routes: replacement_routes.py** — Rewrite with full/partial flow (Section 11)
4. **Backend routes: order_routes.py** — Update historical import mapping + action validation
5. **Backend: new routes** — cancelled-orders, resolved-orders endpoints
6. **Test all backend endpoints** before touching frontend
7. **Frontend: OrderDetail.js** — Context-dependent action buttons
8. **Frontend: ReturnDetail.js** — 3-type workflow stepper
9. **Frontend: ReplacementDetail.js** — Full/partial replacement flow
10. **Frontend: CancelledOrders.js** — New page
11. **Frontend: ResolvedOrders.js** — New page  
12. **Frontend: App.js + Layout.js** — Routes and nav
13. **Test everything end-to-end**

---

## FILES REFERENCE

### Backend Files to Modify:
- `/app/backend/models.py` — Enums and model changes
- `/app/backend/routes/return_routes.py` — Full rewrite
- `/app/backend/routes/replacement_routes.py` — Full rewrite
- `/app/backend/routes/order_routes.py` — Import mapping + action validation

### Backend Files to Create:
- (Cancelled/Resolved orders can use existing order_routes with new query endpoints)

### Frontend Files to Modify:
- `/app/frontend/src/pages/OrderDetail.js`
- `/app/frontend/src/pages/ReturnDetail.js`
- `/app/frontend/src/pages/Returns.js`
- `/app/frontend/src/pages/Replacements.js`
- `/app/frontend/src/pages/ReplacementDetail.js`
- `/app/frontend/src/App.js`
- `/app/frontend/src/components/Layout.js`

### Frontend Files to Create:
- `/app/frontend/src/pages/CancelledOrders.js`
- `/app/frontend/src/pages/ResolvedOrders.js`
