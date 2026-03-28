# Furniva Inventory Intelligence System - Comprehensive Plan

## Overview
This is the next major phase after Returns & Replacements. Moving beyond basic stock tracking to a full **Inventory Intelligence & Action System** that not only provides analytics but also **automates decisions and actions**.

---

## Module 1: SKU Mapping Engine Enhancement

### Current State
- SKU/ASIN/FNSKU mappings created one-by-one via UI

### Required Enhancement
**Bulk Import via CSV/Excel**

Format:
```csv
internal_sku,product_name,category,amazon_asin,amazon_fnsku,flipkart_fsn,website_sku
FRN-SR-001,Shoe Rack 3 Tier,Storage,B08XYZ123,X001ABC,FKSRACK001,SR-WEB-001
FRN-WD-002,Wardrobe 2 Door,Furniture,B09ABC456,X002DEF,FKWARD002,WD-WEB-002
```

Features:
- Validation (duplicate check, format validation)
- Preview before import
- Error report for failed rows
- Merge vs Replace mode
- Category auto-creation if new

---

## Module 2: Inventory Turnover Analysis

### Dead Stock / Non-Moving Analysis
- **Dead Stock**: 0 sales in 90+ days
- **Slow Moving**: <5 units in 60 days
- **Non-Moving**: No movement (sales or returns) in 30+ days

### Pricing Analysis
- Current price vs historical avg
- Price drop impact on velocity
- Competitor price tracking (manual/API)
- Margin analysis per SKU

### Movement Analysis
- Daily/Weekly/Monthly velocity
- Trend detection (rising/falling)
- Seasonality patterns
- Category-wise comparison

### Stock Reordering Suggestions
Formula:
```
Reorder Point = (Avg Daily Sales × Lead Time) + Safety Stock
Safety Stock = Z-score × Std Dev of Daily Sales × √Lead Time
```

### Stock Liquidation Suggestions
Triggers:
- Age > 120 days + velocity < 1 unit/week
- Margin < 10% + no sales in 45 days
- Seasonal item past season

Suggested Actions:
- Price drop % suggestion
- Bundle creation opportunity
- Marketplace clearance sale

### Category-Wise Sorting
- Group by category
- Category performance metrics
- Category health score

---

## Module 3: Real-Time Stock Sync Engine

### Stock Buckets
| Bucket | Definition |
|--------|------------|
| **Reserved Stock** | Orders placed but not shipped |
| **Available Stock** | Sellable inventory |
| **Incoming Stock** | PO pipeline (ordered from supplier) |
| **Damaged/Blocked Stock** | QC failed, returns pending inspection |
| **In-Transit Stock** | Shipped to customer (not delivered) |

### Stock Calculations
```
Sellable = Physical Stock - Reserved - Damaged - Blocked
ATP (Available to Promise) = Sellable + Incoming - Reserved Future Orders
```

### Sync Points
- Order created → Reserve stock
- Order shipped → Deduct from Available
- Order delivered → Confirm deduction
- Order cancelled → Release reservation
- Return received → Add to Damaged (pending QC)
- QC passed → Move to Available
- PO received → Add to Incoming → Available

---

## Module 4: Demand Forecasting

### SKU-Level Prediction
- Historical sales data (12-month rolling)
- Weighted moving average (recent data weighted higher)
- Trend detection (linear regression)

### Seasonal Multiplier
```javascript
seasonalMultiplier = {
  "diwali": 2.5,      // Oct-Nov
  "new_year": 1.8,    // Dec-Jan
  "summer": 0.8,      // Apr-Jun (furniture slow)
  "monsoon": 1.2,     // Jul-Sep
  "default": 1.0
}
```

### Marketplace-Specific Demand
- Amazon vs Flipkart vs Website patterns
- Region-wise demand (if warehouse data available)
- Channel-specific velocity

### Forecast Output
```
30-day forecast = Base Forecast × Seasonal Multiplier × Channel Factor
```

---

## Module 5: Purchase Intelligence

### Smart Order Quantity
**NOT just "stock low → reorder"**

```
Suggested Order Qty = 
  (Forecast Demand for Lead Time Period + Buffer Stock) 
  - Current Available Stock 
  - Incoming Stock (PO pipeline)
```

### Supplier Lead Time Tracking
- Average lead time per supplier
- Lead time variance
- On-time delivery %

### Supplier Performance Score
| Metric | Weight |
|--------|--------|
| On-time Delivery % | 30% |
| Defect Rate % | 25% |
| Price Competitiveness | 20% |
| Communication | 15% |
| Flexibility | 10% |

Score = Weighted average (0-100)

### Auto-Generated PO Suggestions
- When to order (lead time consideration)
- How much to order (demand + buffer - stock)
- Which supplier (performance score)

---

## Module 6: Return & Damage Intelligence

### SKU-Level Return Reason Analysis
Track per SKU:
- Return % (returns/sales)
- Top 3 return reasons
- Customer feedback patterns
- Quality issue correlation

### Courier-Wise Damage Rates
| Courier | Damage % | Avg Claim Time | Claim Success % |
|---------|----------|----------------|-----------------|
| Delhivery | 2.3% | 14 days | 78% |
| BlueDart | 1.1% | 7 days | 92% |
| Ecom Express | 3.5% | 21 days | 65% |

### Packaging Failure Correlation
- Damage rate vs packaging type
- Damage rate vs product category
- Damage rate vs distance shipped

### Actionable Insights
- "SKU-123 has 15% return rate due to 'assembly issues' - consider instruction video"
- "Courier X has 5x damage rate for fragile items - avoid for glass products"
- "Foam packaging reduces damage by 60% vs bubble wrap"

---

## Module 7: Inventory Aging Buckets

### Age Categories
| Bucket | Age Range | Action Level |
|--------|-----------|--------------|
| Fast Moving | 0-30 days | ✅ Healthy |
| Normal | 31-60 days | 🔵 Monitor |
| Slow | 61-90 days | 🟡 Price Review |
| Stale | 91-180 days | 🟠 Liquidation Plan |
| Dead | 180+ days | 🔴 Aggressive Liquidation |

### Age-Based Actions
- **60+ days**: Auto-suggest 10% price drop
- **90+ days**: Auto-suggest bundle creation
- **120+ days**: Auto-suggest marketplace clearance
- **180+ days**: Auto-suggest wholesale liquidation

### FIFO Tracking
- Batch-wise age tracking
- Ship oldest stock first
- Age-based warehouse placement

---

## Module 8: Action Engine (NOT JUST DASHBOARD)

### Auto-Create Actions

#### Purchase Orders
```
IF forecast_stockout_days < lead_time + 7 THEN
  auto_create_po(supplier, qty, urgency="high")
```

#### Liquidation Campaigns
```
IF age > 120 AND velocity < 1/week THEN
  create_liquidation_campaign(sku, suggested_discount)
```

#### Price Drops
```
IF competitor_price < our_price × 0.9 AND margin > 15% THEN
  suggest_price_drop(new_price, expected_velocity_increase)
```

### Smart Alerts
| Alert | Trigger | Priority |
|-------|---------|----------|
| Stockout Warning | "SKU will stockout in 6 days" | 🔴 Critical |
| Dead Stock Alert | "SKU has 0 sales in 90 days" | 🟠 High |
| Price Opportunity | "Competitor raised price by 15%" | 🟡 Medium |
| Supplier Issue | "Supplier late by 7+ days" | 🟠 High |
| Quality Alert | "Return rate jumped 3x this week" | 🔴 Critical |

### Alert Delivery
- In-app notifications
- Email digest (daily/weekly)
- WhatsApp alerts (critical only)

---

## Module 9: Marketplace-Specific Intelligence

### Amazon Intelligence
| Metric | Tracking |
|--------|----------|
| Buy Box % | Win rate tracking |
| Buy Box Price Sensitivity | Price vs Buy Box correlation |
| FBA vs FBM Split | Inventory allocation |
| A+ Content Performance | Conversion impact |
| Review Score | Quality indicator |

### Flipkart Intelligence
- Regional demand heatmap
- F-Assured badge impact
- Flipkart Fulfillment vs Self Ship
- Category ranking tracking

### Website Intelligence
- Conversion rate vs stock availability
- "Out of Stock" page visits
- Cart abandonment due to stock
- Wishlist vs availability correlation

### Cross-Platform Arbitrage
- Price parity monitoring
- Stock allocation optimization
- Channel-specific margin analysis

---

## Module 10: Multi-Warehouse + Routing Logic

### Warehouse Management
- Multiple warehouse support
- Warehouse-wise stock tracking
- Transfer orders between warehouses

### Fulfillment Decision Engine
```
BEST_WAREHOUSE = 
  minimize(
    distance_to_customer × distance_weight +
    stock_age × freshness_weight +
    warehouse_capacity × capacity_weight
  )
```

### Split Shipment Logic
```
IF order_items spread across warehouses THEN
  Option 1: Ship separately (fast, higher cost)
  Option 2: Consolidate to one warehouse first (slow, lower cost)
  DECIDE based on: customer_tier, margin, urgency
```

### Nearest Dispatch Optimization
- Pin code to warehouse mapping
- Courier serviceability check
- Cost vs speed tradeoff

---

## Module 11: Audit & Control

### Cycle Counts (Partial Inventory Checks)
- Random SKU selection for counting
- Variance detection
- Count frequency based on value/velocity
- Mobile app for counting

### Shrinkage Detection
```
Expected Stock = Opening + Received - Sold - Returns - Damaged
Shrinkage = Expected Stock - Actual Stock
```

Alert if shrinkage > 2%

### Staff Accountability Logs
Track per user:
- Stock adjustments made
- Cycle count participation
- Discrepancy rate
- Approval workflows for adjustments

### Audit Reports
- Daily stock movement summary
- Weekly variance report
- Monthly shrinkage analysis
- Quarterly inventory valuation

---

## Implementation Priority

### Phase 1 (MVP)
1. ✅ Bulk SKU Import (CSV/Excel)
2. ✅ Real-Time Stock Buckets (Reserved, Available, Damaged)
3. ✅ Basic Inventory Aging (30/60/90/180 day buckets)
4. ✅ Stockout Alerts

### Phase 2 (Intelligence)
1. Demand Forecasting (30-day)
2. Purchase Intelligence (Smart PO suggestions)
3. Return & Damage Analysis
4. Supplier Tracking

### Phase 3 (Automation)
1. Auto-Create POs
2. Liquidation Campaigns
3. Price Drop Suggestions
4. Full Alert System

### Phase 4 (Advanced)
1. Multi-Warehouse Support
2. Marketplace-Specific Intelligence
3. Audit & Control System
4. Advanced Routing Logic

---

## Technical Considerations

### Data Requirements
- 12+ months historical sales data
- Supplier information with lead times
- Warehouse locations
- Courier performance data

### Integration Points
- Amazon SP-API (inventory sync)
- Flipkart Seller API
- Accounting system (valuation)
- Warehouse Management System (if external)

### Performance
- Real-time stock updates (websocket)
- Batch processing for forecasts (nightly)
- Cached dashboard metrics (5-min refresh)

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Stockout Rate | < 2% |
| Inventory Turnover | > 6x/year |
| Dead Stock % | < 5% |
| Order Fulfillment Rate | > 98% |
| Forecast Accuracy | > 80% |
| Shrinkage Rate | < 1% |
