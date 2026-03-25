# FURNIVA CRM - BUGS & ROADMAP
**Last Updated:** March 7, 2025
**Status:** Critical bugs need fixing, major features incomplete

---

## 🔴 CRITICAL BUGS (Fix Immediately)

### Bug #1: Return Reason Not Saving
**Problem:** Creating return request through order detail, selecting reason, but dashboard still shows "unspecified cancellations"

**Root Cause:** 
- Return request creates entry in `return_requests` collection
- BUT does NOT update order's `cancellation_reason` field
- Dashboard checks order.cancellation_reason (which remains null/empty)

**Fix Required:**
```python
# In /app/backend/routes/return_routes.py
# After creating return request, also update the order:
await db.orders.update_one(
    {"id": order_id},
    {"$set": {
        "cancellation_reason": return_data.return_reason,
        "return_requested": True,
        "return_date": datetime.now()
    }}
)
```

**Files to Fix:**
- `/app/backend/routes/return_routes.py` - create_return_request endpoint
- Must sync return_reason to order.cancellation_reason

---

### Bug #2: Return Classification Still Showing "Unknown"
**Problem:** Despite classification logic, some returns show as "unknown"

**Root Cause:** Classification logic only checks historical patterns, not new return reasons

**Fix Required:**
Update `classify_return_category()` in `/app/backend/routes/returns_routes.py`:
- Add mapping for new 8 return reasons:
  - "Pre Fulfillment Cancel" → pfc
  - "Damage" → resolved (if delivered) or refunded (if cancelled)
  - "Fraud" → fraud
  - "Customer Refused at Doorstep" → refunded
  - "Delayed" → refunded
  - Others → refunded

---

### Bug #3: Loss Calculation Variables Not Exposed to Frontend
**Problem:** Loss configuration exists in backend, but no UI to edit variables (15%, logistics costs, etc.)

**Fix Required:**
- Create `/settings` or `/configuration` page
- Show current loss config variables
- Allow editing (resolved_cost_percentage, default_logistics, etc.)
- Update button to save

---

## ⚠️ MISSING FEATURES (Major)

### Missing #1: Complete Return Workflow Process
**What's Missing:** Multi-stage return workflow tracking

**Required Workflow Stages:**
1. **Return Requested** → Customer initiates
2. **Feedback Check** → Has customer left negative review? (Amazon/Flipkart)
3. **Claim Filed** → Has customer filed A-Z claim or Safe-T claim?
4. **Authorization** → 
   - Amazon: Auto-authorized by marketplace
   - Self: Manual authorization needed
5. **Return Initiated** → Customer sends product back
6. **Return Tracking** → Track return shipment
7. **Warehouse Received** → Product back in warehouse
8. **QC Inspection** → Check damage level
9. **Claim Filing** → File courier claim if damaged in transit
10. **Claim Status** → Approved/Rejected/Pending
11. **Refund Processed** → Issue refund to customer
12. **Closed** → Return complete

**Tables Needed:**
- `return_workflow_status` (current stage)
- `return_claims` (claim details, courier, amount, status)
- `return_qc` (inspection report, damage photos)

**Implementation Required:**
- New ReturnWorkflow model
- Return workflow routes
- Return detail page (not just list)
- Status update UI
- Claim filing form
- QC report form

---

### Missing #2: Edit History UI
**What Exists:** Backend tracking all changes
**What's Missing:** Frontend to view history

**Required:**
- Edit history card in Order Detail
- Show: Who changed what, when
- Timeline view
- Filter by field or user

**Implementation:**
- Fetch `/api/edit-history/order/{id}`
- Display in collapsible card
- Show field changes in readable format

---

### Missing #3: Loss Calculation Frontend
**What Exists:** Backend API to calculate/edit loss
**What's Missing:** UI in Order Detail to view/edit

**Required:**
- Loss Calculation card in Order Detail
- Show breakdown:
  - Logistics outbound: ₹X
  - Logistics return: ₹X
  - Product cost: ₹X
  - Replacement cost: ₹X
  - Total Loss: ₹X
- Edit button to modify values
- Auto-calculate button
- Track who edited

---

### Missing #4: Replacement Images Not Uploadable
**Problem:** Frontend accepts file input but doesn't upload

**Current Issue:**
```javascript
// Just stores filename, not actual upload
const fileUrls = files.map(f => f.name); // Placeholder
```

**Fix Required:**
- Add image upload endpoint (S3/CloudStorage or local storage)
- Upload files in replacement form
- Store actual URLs
- Display images in replacement detail
- Click to view full image

---

### Missing #5: Mandatory Cancellation Reason
**Problem:** Can still mark order as "cancelled" without selecting reason

**Fix Required:**
- In Order edit form, make cancellation_reason REQUIRED if status = "cancelled"
- Show validation error
- Prevent save without reason

---

## 📋 COMPLETE IMPLEMENTATION ROADMAP

---

## PHASE 1: FIX CRITICAL BUGS ⚡ (2-3 hours)
**Priority:** URGENT

### 1.1 Fix Return Reason Sync
- [ ] Update return_routes.py create endpoint
- [ ] Sync return_reason to order.cancellation_reason
- [ ] Test: Create return → check dashboard alert disappears

### 1.2 Fix Return Classification
- [ ] Update classify_return_category() logic
- [ ] Add mappings for new 8 return reasons
- [ ] Test: All returns classified correctly (no "unknown")

### 1.3 Make Cancellation Reason Mandatory
- [ ] Frontend validation in Order edit form
- [ ] Backend validation in order update endpoint
- [ ] Show error if cancelled without reason

### 1.4 Fix Image Upload for Replacements
- [ ] Create image upload endpoint
- [ ] Integrate with replacement form
- [ ] Store real URLs, not filenames
- [ ] Display images properly

---

## PHASE 2: COMPLETE RETURN WORKFLOW 🔄 (6-8 hours)
**Priority:** HIGH - Core Business Process

### 2.1 Return Workflow Models
- [ ] Create ReturnWorkflowStatus enum (11 stages)
- [ ] Create ReturnClaim model (claim details)
- [ ] Create ReturnQC model (inspection report)
- [ ] Add workflow fields to return_requests

### 2.2 Return Workflow Backend
- [ ] POST /api/returns/{id}/workflow/advance - Move to next stage
- [ ] POST /api/returns/{id}/claim - File claim
- [ ] POST /api/returns/{id}/qc-report - Submit QC
- [ ] PATCH /api/returns/{id}/claim-status - Update claim
- [ ] GET /api/returns/{id}/workflow - Get full workflow

### 2.3 Return Detail Page (Frontend)
- [ ] Create ReturnDetail.js page
- [ ] Show workflow stages (visual stepper)
- [ ] Action buttons for current stage
- [ ] Claim filing form
- [ ] QC report form
- [ ] History timeline

### 2.4 Integration
- [ ] Link from Returns dashboard to detail
- [ ] Link from Order detail to return detail
- [ ] Notifications for stage changes

**Workflow Implementation:**
```
Stage 1: Return Requested ✓ (exists)
Stage 2: Feedback Check → Form: "Negative review? Y/N", "Platform?"
Stage 3: Claim Filed → Form: "Claim type? A-Z/Safe-T/Other"
Stage 4: Authorization → Button: "Auto" or "Manual Authorize"
Stage 5: Return Initiated → Button: "Customer Shipped"
Stage 6: Return Tracking → Form: "Return tracking number"
Stage 7: Warehouse Received → Button: "Mark Received" + Date picker
Stage 8: QC Inspection → Form: Damage level, Photos, Notes
Stage 9: Claim Filing → Form: Courier, Amount, Reason, Attachments
Stage 10: Claim Status → Dropdown: Pending/Approved/Rejected + Amount
Stage 11: Refund Processed → Button: "Issue Refund" + Amount
Stage 12: Closed → Auto when refund processed
```

---

## PHASE 3: LOSS CALCULATION UI 💰 (2-3 hours)
**Priority:** MEDIUM

### 3.1 Loss Configuration Page
- [ ] Create Settings.js or Configuration.js
- [ ] GET /api/loss/config
- [ ] Edit form for all variables
- [ ] PATCH /api/loss/config to save
- [ ] Show last updated by/when

### 3.2 Loss Calculator in Order Detail
- [ ] Add "Loss Calculation" card
- [ ] Show breakdown (all 4 components)
- [ ] "Auto Calculate" button
- [ ] "Edit Manually" button → open edit form
- [ ] Show calculation method (auto/manual)
- [ ] Show edited by/when

---

## PHASE 4: EDIT HISTORY UI 📝 (2 hours)
**Priority:** MEDIUM

### 4.1 Edit History Card in Order Detail
- [ ] Fetch /api/edit-history/order/{id}
- [ ] Display in collapsible card
- [ ] Show each change: Field, Old → New, User, Time
- [ ] Color code by type (status=red, price=green, etc.)
- [ ] Filter by date range or field

### 4.2 Recent Edits Page (Optional)
- [ ] Create RecentEdits.js
- [ ] Show all recent changes across orders
- [ ] Filter by user
- [ ] Useful for audit

---

## PHASE 5: REPLACEMENT ENHANCEMENTS 📦 (3-4 hours)
**Priority:** MEDIUM

### 5.1 Image Upload & Display
- [ ] Upload endpoint (S3 or local storage)
- [ ] Frontend integration in replacement form
- [ ] Image gallery in replacement detail
- [ ] Click to enlarge/download

### 5.2 Replacement Detail Page
- [ ] Create ReplacementDetail.js
- [ ] Show full damage description
- [ ] Image gallery
- [ ] Workflow timeline
- [ ] Action buttons for each stage
- [ ] Notes section

### 5.3 Replacement Cost Tracking
- [ ] Add replacement_cost field
- [ ] Track parts cost + logistics
- [ ] Show in loss calculation
- [ ] Report: Replacement costs by product

---

## PHASE 6: DASHBOARD ENHANCEMENTS 📊 (2-3 hours)
**Priority:** MEDIUM

### 6.1 Returns Analytics
- [ ] Add "Returns Overview" card
- [ ] Show: Total returns, Return rate %, Top reasons
- [ ] Click to filter Returns page

### 6.2 Loss Analytics
- [ ] Add "Total Loss This Month" card
- [ ] Breakdown by category (PFC/Resolved/Refunded/Fraud)
- [ ] Trend chart (loss over time)

### 6.3 Replacement Status
- [ ] Show pending replacements count
- [ ] Show resolved this month
- [ ] Quick actions

---

## PHASE 7: ADVANCED ANALYTICS 📈 (4-6 hours)
**Priority:** LOW (Future)

### 7.1 Returns Analytics Page
- [ ] Return rate by product
- [ ] Return rate by courier
- [ ] Return rate by pincode
- [ ] Return reasons breakdown (charts)
- [ ] Loss analysis by reason
- [ ] Month-over-month trends

### 7.2 Financial Reports
- [ ] Total loss by month/quarter/year
- [ ] Loss by category breakdown
- [ ] Profitability after returns/losses
- [ ] Export to Excel

### 7.3 Courier Performance
- [ ] RTO rate by courier
- [ ] Damage rate by courier
- [ ] Claim approval rate
- [ ] Recommended courier by pincode

---

## PHASE 8: CUSTOMER RISK SCORING 🛡️ (4-5 hours)
**Priority:** LOW (Future)

### 8.1 Risk Score Calculation
- [ ] Track: Return frequency per customer
- [ ] Track: Refusal at doorstep count
- [ ] Track: Claims filed
- [ ] Calculate risk score (0-100)

### 8.2 Risk Alerts
- [ ] Flag high-risk customers (score > 70)
- [ ] Show in order detail
- [ ] Require manager approval for high-risk orders
- [ ] Block option for extreme cases

---

## PHASE 9: INSTALLATION MANAGEMENT 🔧 (5-6 hours)
**Priority:** LOW (Future)

### 9.1 Installation Workflow
- [ ] Track: Installation required Y/N
- [ ] Assign installer
- [ ] Schedule date/time
- [ ] Installation cost
- [ ] Completion verification
- [ ] Customer signature/photo
- [ ] Installer rating

---

## PHASE 10: CLAIMS MANAGEMENT 📋 (4-5 hours)
**Priority:** MEDIUM (Part of Return Workflow)

### 10.1 Claim Types
- [ ] Courier damage claims
- [ ] Marketplace claims (A-Z, Safe-T)
- [ ] Insurance claims

### 10.2 Claim Tracking
- [ ] Filed date
- [ ] Expected resolution date
- [ ] Status updates
- [ ] Claim amount
- [ ] Approved/Rejected amount
- [ ] Documents/proof

### 10.3 Claim Success Rate
- [ ] By courier
- [ ] By claim type
- [ ] Average approval amount
- [ ] Time to resolution

---

## 📊 PRIORITY MATRIX

### DO NOW (Next 24 hours):
1. ✅ Fix return reason sync bug
2. ✅ Fix classification "unknown" bug
3. ✅ Make cancellation reason mandatory
4. ✅ Fix image upload for replacements

### DO NEXT (This Week):
1. 🔄 Complete return workflow (11 stages)
2. 💰 Loss calculation UI
3. 📝 Edit history UI
4. 📋 Claim filing in return workflow

### DO LATER (Next 2 Weeks):
1. 📊 Returns analytics
2. 📈 Financial reports
3. 🛡️ Customer risk scoring
4. 🔧 Installation management

---

## 🎯 SUCCESS CRITERIA

### Return System Complete When:
- [ ] Return reason automatically syncs to order
- [ ] No "unspecified cancellations" for new returns
- [ ] All 11 workflow stages functional
- [ ] Claims can be filed and tracked
- [ ] QC reports can be submitted
- [ ] Refunds tracked per return
- [ ] Loss calculated per return

### Loss System Complete When:
- [ ] Variables editable via UI
- [ ] Loss shown in order detail
- [ ] Manual override possible
- [ ] Edit history tracked
- [ ] Reports show total loss

### Replacement System Complete When:
- [ ] Images upload and display properly
- [ ] All 6 workflow stages functional
- [ ] Cost tracking per replacement
- [ ] Resolution tracking (solved Y/N)

---

## 📄 FILES NEEDING CHANGES

### Backend:
- `/app/backend/routes/return_routes.py` - Fix sync bug
- `/app/backend/routes/returns_routes.py` - Fix classification
- `/app/backend/models.py` - Add workflow models
- New: `/app/backend/routes/return_workflow_routes.py`
- New: `/app/backend/routes/claim_routes.py`

### Frontend:
- `/app/frontend/src/pages/OrderDetail.js` - Add loss card, edit history
- New: `/app/frontend/src/pages/ReturnDetail.js`
- New: `/app/frontend/src/pages/ReplacementDetail.js`
- New: `/app/frontend/src/pages/Settings.js` (loss config)
- `/app/frontend/src/pages/Returns.js` - Link to detail pages

---

## 🚨 CRITICAL NOTES FOR NEXT AGENT

1. **Return Reason Bug is TOP PRIORITY** - Affects business operations
2. **Return Workflow is CORE FEATURE** - 11 stages, not 3
3. **Images must actually upload** - Not just filenames
4. **Loss calculation UI needed** - Backend exists, frontend missing
5. **Edit history UI needed** - Backend tracking, frontend missing

**Test after fixing bugs:**
```
1. Create return via order detail
2. Select "Damage" reason
3. Check dashboard → unspecified alert should NOT show
4. Check Returns page → should classify correctly
5. Check order detail → should show return status card
```

---

END OF DOCUMENT
