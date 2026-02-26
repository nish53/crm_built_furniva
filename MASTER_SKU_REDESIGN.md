# MASTER SKU REDESIGN - Supporting Multiple Listings Per Platform

## Problem:
Current design only allows ONE ASIN, ONE SKU per Master SKU. 
Reality: One Master SKU can have 5+ different listings on Amazon, each with different ASIN, SKU.

## New Architecture:

### 1. Master SKU Table (Core Product)
- master_sku (unique)
- product_name
- description
- category
- dimensions
- weight
- base_cost_price (reference only)

### 2. Platform Listings Table (One-to-Many)
- id
- master_sku (foreign key)
- platform (amazon/flipkart/website)
- platform_sku (seller SKU)
- platform_product_id (ASIN for Amazon, FSN for Flipkart)
- platform_fnsku (FNSKU for Amazon/Flipkart)
- listing_title
- is_active
- created_at

### 3. Procurement Batches Table (Cost Tracking)
- id
- master_sku
- batch_number
- procurement_date
- quantity
- unit_cost
- supplier
- notes

## Benefits:
- Multiple ASINs per Master SKU ✓
- Multiple FSNs per Master SKU ✓
- Historical cost tracking ✓
- Flexible platform listings ✓

## Implementation Needed:
1. Create platform_listings collection
2. Create procurement_batches collection  
3. Update Master SKU model to remove single ASIN/SKU fields
4. Update import logic to lookup across all listings
5. Update frontend to manage multiple listings per Master SKU
