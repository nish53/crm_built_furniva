# HANDOFF TO NEXT AGENT - QUICK START GUIDE
**Created:** July 2025  
**Purpose:** Quick reference to get the next agent started immediately

---

## 🎯 YOUR MISSION

User wants the **Return/Replacement/Cancellation workflow completely redesigned** to be context-dependent based on order status. This is the **TOP PRIORITY** and must be completed before any other work.

---

## 📖 DOCUMENTS TO READ (In Order)

### 1. START HERE: `/app/UPDATED_ROADMAP_AND_STATUS.md`
**This is your primary reference.** Contains:
- Complete current state (what's done vs what's not)
- Full workflow redesign specification
- Context-dependent reason taxonomy
- Backend model changes required
- Frontend changes required
- Step-by-step implementation order (16-22 hours)

### 2. ADDITIONAL CONTEXT: `/app/WORKFLOW_SPECIFICATION.md`
- Original workflow specification from earlier session
- Additional details on 3-type return workflow
- Replacement workflow specifics

### 3. FEATURE STATUS: `/app/FEATURE_LIST_STATUS.md`
- Complete list of all features (11 phases)
- Current status of each phase
- Time estimates for remaining work

### 4. TESTING PROTOCOL: `/app/test_result.md`
- Lines 1-97: Testing protocol (DO NOT EDIT THIS SECTION)
- Lines 105+: Current testing data and history
- Must read before calling testing agents

---

## ⚡ QUICK SUMMARY OF WHAT NEEDS TO BE DONE

### The Problem:
Current return/replacement system uses a fixed 12-stage workflow that doesn't match real business needs. User needs different cancellation reasons and workflows depending on when the order is cancelled:
- **Before shipping** (pre-dispatch): Simple cancel with reasons like "Change of Mind"
- **During shipping** (in-transit): RTO (Return to Origin) with tracking
- **After delivery** (post-delivery): Return with pickup or replacement options

### What You Need to Build:

#### 1. Backend Changes:
- Replace return reason enums with 3 context-dependent enums
- Add `return_type` field to ReturnRequest model
- Rewrite `/app/backend/routes/return_routes.py` for 3-type workflow
- Rewrite `/app/backend/routes/replacement_routes.py` for full/partial workflow
- Update historical import in `/app/backend/routes/order_routes.py`
- Add cancelled-orders and resolved-orders endpoints

#### 2. Frontend Changes:
- **OrderDetail.js**: Add context-dependent action buttons (cancel/RTO/return/replacement based on order status)
- **New pages**: CancelledOrders.js, ResolvedOrders.js
- **Rewrite pages**: ReturnDetail.js, ReplacementDetail.js for new workflows
- **Update navigation**: Add "Cancelled Orders" and "Resolved Orders" to sidebar menu

---

## 🔑 KEY CONCEPTS

### Context-Dependent Reasons:
- **Pre-dispatch** (order not shipped yet): 6 reasons (Change of Mind, Better Pricing, etc.)
- **In-transit** (shipped, not delivered): 3 reasons (Customer Refused, Unavailable, Delay)
- **Post-delivery** (delivered): 8 reasons (Damage, Quality Issue, Wrong Product, etc.)

### 3-Type Return Workflow:
1. **Pre-dispatch cancellation**: Request → Approve/Reject → Done
2. **In-transit RTO**: Request → Approve → RTO Tracking → Warehouse Received → Done
3. **Post-delivery return**: Request → Accept → Pickup (or "Pickup Not Required") → Warehouse → Condition Check → Done

### Replacement Workflow:
- **Reasons**: Damaged, Quality, Wrong Product, Customer Change of Mind
- **Types**: Full Replacement OR Partial Replacement (for Damaged/Quality only)
- **Flow**: Request → Approve → Pickup (optional) → New Shipment → Delivery → Resolved
- **Special**: "Pickup Not Required" checkbox for severely damaged items

### Historical Import:
CSV has columns "Live Status" and "Reason for Cancellation/Replacement" that must be mapped correctly:
- `cancelled` + "PFC" → Cancelled Orders, reason = "did_not_specify"
- `cancelled` + "Damage" → Cancelled Orders, reason = "damage"
- `delivered` + "Part Damage" → Resolved Orders
- See full mapping table in `/app/UPDATED_ROADMAP_AND_STATUS.md`

---

## 📁 KEY FILES TO MODIFY

### Backend:
```
/app/backend/models.py (lines 434-598)
  └─ Replace ReturnReason, ReturnStatus, ReplacementStatus enums
  └─ Update ReturnRequest model (add return_type, notes, pickup fields)
  └─ Update ReplacementRequest model (add replacement_type, pickup fields)

/app/backend/routes/return_routes.py (FULL REWRITE)
  └─ Implement 3-type workflow
  └─ Context-aware validation
  └─ workflow/advance endpoint

/app/backend/routes/replacement_routes.py (FULL REWRITE)
  └─ Full/partial replacement logic
  └─ Pickup tracking + new shipment tracking

/app/backend/routes/order_routes.py (UPDATE import section)
  └─ Lines 268-292: parse_date function
  └─ Import mapping for "Reason for Cancellation/Replacement"
```

### Frontend:
```
/app/frontend/src/pages/OrderDetail.js
  └─ Add context-dependent action buttons

/app/frontend/src/pages/CancelledOrders.js (NEW FILE)
  └─ Tabbed view, grouped by cancellation reason

/app/frontend/src/pages/ResolvedOrders.js (NEW FILE)
  └─ List of resolved orders

/app/frontend/src/pages/ReturnDetail.js (REWRITE)
  └─ 3-type workflow with context-aware stepper

/app/frontend/src/pages/ReplacementDetail.js (REWRITE)
  └─ Full/partial replacement flow

/app/frontend/src/App.js
  └─ Add routes for new pages

/app/frontend/src/components/Layout.js
  └─ Add nav items for Cancelled Orders, Resolved Orders
```

---

## ✅ IMPLEMENTATION CHECKLIST

Copy this to your planning:

### Phase 1: Backend Models (1-2 hours)
- [ ] Update return reason enums in models.py
- [ ] Add return_type field to ReturnRequest
- [ ] Add replacement_type field to ReplacementRequest
- [ ] Add pickup-related fields to both models
- [ ] Test models can be instantiated

### Phase 2: Backend Routes - Returns (2-3 hours)
- [ ] Rewrite create endpoint with return_type detection
- [ ] Implement workflow/advance with 3 different flows
- [ ] Implement workflow-stages endpoint
- [ ] Handle pickup_not_required flag
- [ ] Test with curl/Postman

### Phase 3: Backend Routes - Replacements (2-3 hours)
- [ ] Rewrite create endpoint for full/partial
- [ ] Implement advance endpoint with dual tracking
- [ ] Handle pickup_not_required flag
- [ ] Test with curl/Postman

### Phase 4: Backend Routes - Orders (1-2 hours)
- [ ] Update historical import mapping
- [ ] Add cancelled-orders endpoints
- [ ] Add resolved-orders endpoints
- [ ] Test import with sample CSV

### Phase 5: Backend Testing (1 hour)
- [ ] Call deep_testing_backend_v2
- [ ] Fix any issues found

### Phase 6: Frontend - OrderDetail (1-2 hours)
- [ ] Add context-dependent buttons
- [ ] Create cancel/RTO/return/replacement modals
- [ ] Test button visibility

### Phase 7: Frontend - New Pages (2-3 hours)
- [ ] Create CancelledOrders.js
- [ ] Create ResolvedOrders.js
- [ ] Add routes and nav items

### Phase 8: Frontend - Rewrite Details (3-4 hours)
- [ ] Rewrite ReturnDetail.js
- [ ] Rewrite ReplacementDetail.js
- [ ] Update Returns.js and Replacements.js

### Phase 9: End-to-End Testing (1 hour)
- [ ] Test pre-dispatch cancel
- [ ] Test in-transit RTO
- [ ] Test post-delivery return
- [ ] Test full replacement
- [ ] Test partial replacement
- [ ] Test historical import

---

## 🚨 CRITICAL RULES

### DO:
✅ Follow the implementation order exactly (backend first, frontend second)  
✅ Test after each phase before moving to next  
✅ Read `/app/test_result.md` before calling testing agents  
✅ Use `deep_testing_backend_v2` after backend changes  
✅ Ask user for confirmation before starting  
✅ Handle "Pickup Not Required" checkbox in both return and replacement flows  
✅ Make reasons context-dependent based on order status  

### DON'T:
❌ Start without reading `/app/UPDATED_ROADMAP_AND_STATUS.md` first  
❌ Modify any working features unrelated to workflow redesign  
❌ Break existing URLs or endpoints  
❌ Skip the testing phases  
❌ Hardcode values that should come from enums  
❌ Forget to add "Notes" field to all filing forms  
❌ Use the old 12-stage workflow logic  

---

## 🧪 HOW TO TEST

### Backend Testing:
```bash
# After backend changes, update test_result.md then call:
Call deep_testing_backend_v2 with:
"Test the new 3-type return workflow:
1. Create return for pending order (pre-dispatch)
2. Create return for dispatched order (in-transit RTO)  
3. Create return for delivered order (post-delivery)
4. Test pickup_not_required flag
5. Test workflow advancement for each type
6. Create full replacement
7. Create partial replacement
8. Test cancelled-orders endpoint
9. Test resolved-orders endpoint"
```

### Frontend Testing:
```bash
# After frontend changes:
1. Open OrderDetail for pending order → verify "Cancel Order" button shows
2. Open OrderDetail for dispatched order → verify "Cancel/RTO" button shows
3. Open OrderDetail for delivered order → verify BOTH buttons show
4. Click buttons → verify correct reasons appear in dropdowns
5. Test Cancelled Orders page → verify grouping works
6. Test Resolved Orders page → verify orders display
7. Test return detail pages → verify 3 workflows work
8. Test replacement detail pages → verify full/partial flows work
```

---

## 💬 QUESTIONS TO ASK USER

Before starting, confirm with user:
1. "I've reviewed the complete workflow redesign requirements in `/app/UPDATED_ROADMAP_AND_STATUS.md`. Should I proceed with the implementation following the 10-phase plan (estimated 16-22 hours)?"

2. "Do you have a sample CSV file with the 'Live Status' and 'Reason for Cancellation/Replacement' columns that I can use to test the historical import mapping?"

3. "Are there any other cancellation reasons beyond the ones specified that should be included?"

---

## 📞 GETTING HELP

### If you encounter issues:
1. **Read the docs again** - The answer is probably in `/app/UPDATED_ROADMAP_AND_STATUS.md`
2. **Check test_result.md** - See if issue was encountered before
3. **Call troubleshoot_agent** - After 3 failed attempts at same operation
4. **Ask user** - If requirements are unclear

### Common Issues:
- **Enum validation errors**: Make sure you're using the new enum values, not old ones
- **Pydantic errors**: Check model definitions match the new fields
- **Import failures**: Check the column name mapping in parse_date function
- **Missing fields**: Add to both model and create endpoint

---

## 🎉 SUCCESS CRITERIA

You've succeeded when:
1. ✅ Historical CSV imports map cancellation reasons correctly
2. ✅ OrderDetail shows different buttons based on order status
3. ✅ Pre-dispatch cancel flow works end-to-end
4. ✅ In-transit RTO flow works with tracking
5. ✅ Post-delivery return flow works with pickup/condition check
6. ✅ Full replacement flow works with pickup + new shipment
7. ✅ Partial replacement flow works with parts tracking
8. ✅ "Pickup Not Required" checkbox skips pickup phases
9. ✅ Cancelled Orders page groups orders correctly
10. ✅ Resolved Orders page displays correctly
11. ✅ All backend tests pass
12. ✅ User confirms everything works as expected

---

## 📊 TIME ESTIMATE BREAKDOWN

- **Backend Models:** 1-2 hours
- **Backend Returns Routes:** 2-3 hours
- **Backend Replacements Routes:** 2-3 hours
- **Backend Orders & New Endpoints:** 1-2 hours
- **Backend Testing:** 1 hour
- **Frontend OrderDetail:** 1-2 hours
- **Frontend New Pages:** 2-3 hours
- **Frontend Detail Pages Rewrite:** 3-4 hours
- **Frontend Testing:** 1 hour

**Total:** 16-22 hours

---

## 🚀 READY TO START?

1. Read `/app/UPDATED_ROADMAP_AND_STATUS.md` (15 mins)
2. Skim `/app/WORKFLOW_SPECIFICATION.md` (5 mins)
3. Ask user for confirmation (5 mins)
4. Install dependencies and restart services (5 mins)
5. Start Phase 1: Backend Models (1-2 hours)

**Good luck! You've got this! 🎯**

---

**END OF HANDOFF DOCUMENT**
