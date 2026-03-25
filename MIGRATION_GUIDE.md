# FURNIVA CRM - Migration Guide for New Chat

## INSTRUCTIONS FOR NEW AGENT
Paste this entire document into the new chat after loading the MAIN branch. This contains ALL changes that need to be re-applied from the previous development session.

---

## PROJECT OVERVIEW
FURNIVA CRM is a custom-built furniture e-commerce business CRM with React frontend + FastAPI backend + MongoDB. The following changes were developed on a side branch and need to be re-applied to the main branch.

---

## CHANGE SUMMARY

### Phase 1: Critical Bug Fixes
1. **Return reason sync** - When creating a return, the reason is now saved to both `return_requests` collection AND synced to the `orders` collection (`cancellation_reason` field)
2. **Return classification logic** - New `classify_return_category()` function that properly categorizes returns as: `pfc` (pre-fulfillment cancel), `resolved`, `refunded`, or `fraud` - never returns "unknown"
3. **Loss calculation config exposed to frontend** - New `/api/financials/loss/config` GET and PATCH endpoints + Settings page UI to manage 7 configurable variables
4. **Image uploads working** - New `/api/uploads/` routes for local file storage (damage images), single + bulk upload, with file serving
5. **Mandatory cancellation reason** - Backend validates that `cancellation_reason` is required when changing order status to "cancelled"

### Quick Fixes
6. **Order status undo** - New `PATCH /api/orders/{id}/undo-status` endpoint + UI button to revert order to `previous_status`
7. **Conditional Return button** - "Create Return Request" only shows when order is `dispatched` or `delivered`
8. **Conditional Cancel button** - "Cancel Order" only shows for `pending` or `confirmed` orders
9. **Pre-dispatch cancellation flow** - New `PATCH /api/orders/{id}/cancel` endpoint that only allows cancellation for pre-dispatch orders, with mandatory reason + Cancel modal UI

### Phase 2: Complete Return Workflow
10. **11-stage return process** with status enum: `requested -> feedback_check -> claim_filed -> authorized -> return_initiated -> in_transit -> warehouse_received -> qc_inspection -> claim_filing -> claim_status -> refund_processed -> closed` (+ `rejected`, `cancelled`)
11. **Workflow advance endpoint** - `PATCH /api/returns/{id}/workflow/advance` with stage-specific optional fields
12. **Workflow stages query** - `GET /api/returns/{id}/workflow-stages` returns allowed next transitions
13. **ReturnDetail.js** - Full page with visual stepper, advance modal with stage-specific forms, QC image upload, status history display

### Phase 3: Loss Calculation & Edit History
14. **Loss calculation endpoint** - `POST /api/financials/loss/calculate/{order_id}` with auto/manual modes
15. **Loss data endpoint** - `GET /api/financials/loss/{order_id}`
16. **Settings page** - `/settings` route with form to manage all 7 loss config variables
17. **Loss Calculation card on OrderDetail** - Shows breakdown with edit capability
18. **Edit History card on OrderDetail** - Shows field change history (expandable)

### Phase 4: Backend Foundation (Replacements & Claims)
19. **Replacement models** - `ReplacementStatus` enum (10 stages), `ReplacementRequest`, `ReplacementRequestCreate`
20. **Replacement routes** - Full CRUD + workflow advance + workflow stages query + image management
21. **Claims models** - `ClaimStatus` enum (8 stages), `ClaimType` enum, `Claim`, `ClaimCreate`
22. **Claims routes** - Full CRUD + status update + document management + correspondence + analytics

---

## NEW FILES TO CREATE

### Backend Files

#### 1. `/app/backend/routes/upload_routes.py` (NEW)
Local file storage for damage images. Endpoints:
- `POST /api/uploads/damage-image` - Single image upload (max 5MB, jpg/png/gif/webp/heic)
- `POST /api/uploads/damage-images/bulk` - Bulk upload (max 10 files)
- `GET /api/uploads/damage-image/{filename}` - Serve image
- `DELETE /api/uploads/damage-image/{filename}` - Delete image
- Stores files in `/app/backend/uploads/damage_images/`
- Returns URL paths like `/api/uploads/damage-image/{uuid}.jpg`

#### 2. `/app/backend/routes/replacement_routes.py` (NEW)
Replacement workflow management. Endpoints:
- `POST /api/replacements/` - Create replacement request
- `GET /api/replacements/` - List with filters (status, search)
- `GET /api/replacements/{id}` - Get single replacement
- `PATCH /api/replacements/{id}/advance` - Advance workflow (requested -> approved -> parts_arranged -> dispatched -> in_transit -> delivered -> installed -> resolved)
- `GET /api/replacements/{id}/workflow-stages` - Get next allowed transitions
- `PATCH /api/replacements/{id}/images` - Add damage images

#### 3. `/app/backend/routes/claims_routes.py` (NEW)
Claims management. Endpoints:
- `POST /api/claims/` - Create claim
- `GET /api/claims/` - List with filters (status, type, search)
- `GET /api/claims/{id}` - Get single claim
- `PATCH /api/claims/{id}/status` - Update status with approval/rejection details
- `PATCH /api/claims/{id}/documents` - Add supporting documents or evidence
- `POST /api/claims/{id}/correspondence` - Add communication entry
- `GET /api/claims/analytics/by-type` - Analytics by claim type
- `GET /api/claims/analytics/by-status` - Analytics by status

### Frontend Files

#### 4. `/app/frontend/src/pages/ReturnDetail.js` (NEW)
Full return detail page with:
- Visual 12-stage stepper (horizontal progress bar)
- Current stage highlighted, completed stages checked
- "Advance Workflow" button that opens modal with stage-specific forms
- QC image upload during inspection stages
- Return info display (order number, customer, reason, category)
- Status history timeline
- Undo button

#### 5. `/app/frontend/src/pages/Settings.js` (NEW)
Settings page with:
- Loss Calculation Configuration card
- 7 editable fields: resolved_cost_percentage, default_outbound_logistics, default_return_logistics, refund_processing_fee, qc_inspection_cost, restocking_fee_percentage, fraud_investigation_cost
- Save and Reset to defaults buttons
- "Using default values" indicator

---

## EXISTING FILES TO MODIFY

### Backend Modifications

#### 6. `/app/backend/models.py` - ADD these new models/enums:
- `ReturnStatus` enum: Add new workflow statuses (requested, feedback_check, claim_filed, authorized, return_initiated, in_transit, warehouse_received, qc_inspection, claim_filing, claim_status, refund_processed, closed, rejected, cancelled + legacy statuses for backward compatibility)
- `DamageCategory` enum: scratch, crack, dent, broken, missing_parts, packaging_damage, no_damage
- Expand `ReturnRequest` model with: previous_status, status_history, and 30+ stage-specific fields (feedback, claim, authorization, shipping, warehouse, QC, claim filing, refund, closure fields)
- `ReplacementStatus` enum: requested, approved, rejected, parts_arranged, dispatched, in_transit, delivered, installed, resolved, cancelled
- `ReplacementRequest` model with full workflow fields
- `ReplacementRequestCreate` model
- `ClaimStatus` enum: draft, filed, under_review, approved, partially_approved, rejected, appealed, closed
- `ClaimType` enum: courier_damage, marketplace_a_to_z, marketplace_safe_t, insurance, warranty, other
- `Claim` model with full claim management fields
- `ClaimCreate` model
- Add `previous_status` and `cancellation_reason` to Order model

#### 7. `/app/backend/routes/return_routes.py` - MAJOR CHANGES:
- Add `classify_return_category()` function at top
- In `create_return_request`: sync return_reason to order's cancellation_reason field, classify category
- Add `PATCH /{return_id}/workflow/advance` - Full workflow progression with validation rules and stage-specific data
- Add `PATCH /{return_id}/qc-images` - Add QC images
- Add `GET /{return_id}/workflow-stages` - Get allowed transitions
- Add `PATCH /{return_id}/undo` - Undo last status change
- Add `POST /{return_id}/add-image` - Add single damage image
- Add return analytics endpoints (by-reason, by-product, by-category)

#### 8. `/app/backend/routes/order_routes.py` - ADD:
- In `update_order`: Validate cancellation_reason is required when status = cancelled, track previous_status
- Add `PATCH /{order_id}/undo-status` endpoint
- Add `PATCH /{order_id}/cancel` endpoint (pre-dispatch only, requires reason)

#### 9. `/app/backend/routes/financial_routes.py` - ADD:
- `DEFAULT_LOSS_CONFIG` dictionary with 7 variables
- `GET /api/financials/loss/config` - Get loss config
- `PATCH /api/financials/loss/config` - Update loss config
- `POST /api/financials/loss/calculate/{order_id}` - Calculate loss for order
- `GET /api/financials/loss/{order_id}` - Get stored loss data

#### 10. `/app/backend/server.py` - ADD router imports:
```python
from routes.upload_routes import router as upload_router
from routes.replacement_routes import router as replacement_router
from routes.claims_routes import router as claims_router

app.include_router(upload_router, prefix="/api")
app.include_router(replacement_router, prefix="/api")
app.include_router(claims_router, prefix="/api")
```

### Frontend Modifications

#### 11. `/app/frontend/src/App.js` - ADD routes:
```jsx
import { ReturnDetail } from './pages/ReturnDetail';
import { Settings } from './pages/Settings';

// Inside routes:
<Route path="returns/:id" element={<ReturnDetail />} />
<Route path="settings" element={<Settings />} />
```

#### 12. `/app/frontend/src/components/Layout.js` - ADD nav item:
```jsx
{ name: 'Settings', href: '/settings', icon: Settings }
```
(Import Settings from lucide-react)

#### 13. `/app/frontend/src/pages/OrderDetail.js` - MAJOR CHANGES:
- Add state variables: showCancelModal, cancellationReason, lossData, loadingLoss, editingLoss, lossEditForm, editHistory, showEditHistory
- Add functions: fetchLossData, handleCalculateLoss, fetchEditHistory, handleUndoStatus, handleCancelOrder
- Image upload for returns: Upload via `/api/uploads/damage-images/bulk` before creating return
- Quick Actions card changes:
  - "Create Return Request" button only shows when status is `dispatched` or `delivered`
  - "Cancel Order" button only shows for `pending` or `confirmed`
  - "Undo" button shows when `previous_status` exists
- Add Loss Calculation card in right column (with edit/calculate/recalculate)
- Add Edit History card (expandable, shows field changes)
- Add Cancel Order modal with reason dropdown
- Mandatory cancellation reason validation in edit form

#### 14. `/app/frontend/src/pages/Returns.js` - ADD:
- Navigation to ReturnDetail page (clicking a return row navigates to `/returns/{id}`)
- Updated status labels to include new workflow statuses

---

## DATABASE COLLECTIONS
New collections used:
- `loss_config` - Stores loss calculation configuration (single document)
- `order_losses` - Stores per-order loss calculations
- `replacement_requests` - Replacement workflow data
- `claims` - Claims management data

Existing collections modified:
- `orders` - Now uses `previous_status`, `cancellation_reason`, `cancelled_at`, `cancelled_by`
- `return_requests` - Now uses expanded status workflow, `category`, `status_history`, and 30+ new fields

---

## KNOWN ISSUES IN THE SIDE BRANCH CODE
1. **OrderDetail.js has syntax issues** - The `handleSaveEdit` function and `updateOrderStatus` function have broken braces/nesting. The functions `fetchLossData` and `handleCalculateLoss` are nested inside `updateOrderStatus`. This needs to be fixed when re-implementing.
2. **Some Communication Status UI is duplicated** - There are two Communication Status sections in OrderDetail.js (one expanded and one in the right sidebar checklist). They should be consolidated.
3. **ReturnDetail.js references `/uploads/damage-images/bulk`** but upload routes use `/uploads/damage-images/bulk` - need to verify path matching.

---

## PHASE 4 FRONTEND (NOT YET BUILT - UPCOMING)
The backend for Replacements and Claims is complete but the frontend pages are NOT built yet:
- Need `ReplacementDetail.js` page with visual stepper
- Need `Claims.js` page for claims list + management
- Need routes and navigation links for both

## FUTURE PHASES (NOT STARTED)
- Phase 5: Replacement cost tracking enhancements
- Phase 6: Dashboard enhancements (analytics cards)
- Phase 7: Advanced Analytics Page
- Phase 8: Customer Risk Scoring
- Phase 9: Installation Management
- Courier Intelligence Module (deferred by user)
