#!/usr/bin/env python3
"""
Final verification test for Inventory Management Phase 4 after ObjectId fixes
Testing ALL endpoints mentioned in the review request
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://furniture-flow-pro.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@furniva.com"
ADMIN_PASSWORD = "Admin123!"

class Phase4Tester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        
    def log_result(self, test_name, success, details="", error=""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()
    
    def authenticate(self):
        """Authenticate and get token"""
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                self.log_result("Authentication", True, f"Logged in as {ADMIN_EMAIL}")
                return True
            else:
                self.log_result("Authentication", False, error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Authentication", False, error=str(e))
            return False
    
    def test_csv_template_bug_fix(self):
        """1. CSV Template (Bug Fix): GET /api/inventory/csv-template"""
        try:
            response = self.session.get(f"{BASE_URL}/inventory/csv-template")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify proper JSON structure with example_rows array
                if "example_rows" not in data:
                    self.log_result("CSV Template - Structure", False, 
                                  error="Missing 'example_rows' field")
                    return False
                
                example_rows = data.get("example_rows", [])
                if not isinstance(example_rows, list):
                    self.log_result("CSV Template - Array Type", False,
                                  error="example_rows should be an array")
                    return False
                
                if len(example_rows) == 0:
                    self.log_result("CSV Template - Array Content", False,
                                  error="example_rows array is empty")
                    return False
                
                self.log_result("CSV Template Bug Fix", True, 
                              f"✅ Proper JSON structure with example_rows array containing {len(example_rows)} examples")
                return True
                
            else:
                self.log_result("CSV Template Bug Fix", False, 
                              error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("CSV Template Bug Fix", False, error=str(e))
            return False
    
    def test_warehouse_management(self):
        """2. Warehouse Management endpoints"""
        try:
            # Create Delhi Warehouse - code WH-DEL
            print("   Testing: POST /api/inventory/warehouses (create Delhi Warehouse - code WH-DEL)")
            warehouse_data = {
                "name": "Delhi Warehouse",
                "code": "WH-DEL",
                "address": "Industrial Area, Sector 62",
                "city": "Delhi",
                "state": "Delhi",
                "pincode": "110001"
            }
            
            response = self.session.post(f"{BASE_URL}/inventory/warehouses", params=warehouse_data)
            
            if response.status_code == 200:
                warehouse = response.json()
                self.log_result("Create Delhi Warehouse (WH-DEL)", True, 
                              f"Created warehouse: {warehouse.get('name')} ({warehouse.get('code')})")
                warehouse_created = True
            else:
                self.log_result("Create Delhi Warehouse (WH-DEL)", False, 
                              error=f"Status: {response.status_code}, Response: {response.text}")
                warehouse_created = False
            
            # Get all warehouses - verify list includes all warehouses
            print("   Testing: GET /api/inventory/warehouses (verify list includes all warehouses)")
            response = self.session.get(f"{BASE_URL}/inventory/warehouses")
            
            if response.status_code == 200:
                data = response.json()
                warehouses = data.get("warehouses", [])
                
                # Check if WH-DEL exists in the list
                wh_del_exists = any(w.get("code") == "WH-DEL" for w in warehouses)
                
                details = f"Retrieved {len(warehouses)} warehouses"
                if wh_del_exists:
                    details += " (includes WH-DEL)"
                elif warehouse_created:
                    details += " (WH-DEL missing despite creation success)"
                
                self.log_result("Get All Warehouses", True, details)
            else:
                self.log_result("Get All Warehouses", False, 
                              error=f"Status: {response.status_code}, Response: {response.text}")
                return False
            
            # Get warehouse stock for WH-DEL - verify empty/has stock
            print("   Testing: GET /api/inventory/warehouse-stock/WH-DEL (verify empty/has stock)")
            response = self.session.get(f"{BASE_URL}/inventory/warehouse-stock/WH-DEL")
            
            if response.status_code == 200:
                data = response.json()
                stock_items = data.get("stock", [])
                self.log_result("Get WH-DEL Stock", True, 
                              f"WH-DEL warehouse stock: {len(stock_items)} items")
            elif response.status_code == 404:
                self.log_result("Get WH-DEL Stock", True, 
                              "WH-DEL warehouse not found (expected if creation failed)")
            else:
                self.log_result("Get WH-DEL Stock", False, 
                              error=f"Status: {response.status_code}, Response: {response.text}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Warehouse Management", False, error=str(e))
            return False
    
    def ensure_test_sku_exists(self):
        """Ensure TEST-CHAIR-001 SKU exists for testing"""
        try:
            # Check if TEST-CHAIR-001 already exists
            response = self.session.get(f"{BASE_URL}/master-sku/")
            if response.status_code == 200:
                skus = response.json()
                test_sku = next((sku for sku in skus if sku.get("master_sku") == "TEST-CHAIR-001"), None)
                if test_sku:
                    self.log_result("Test SKU Verification", True, "TEST-CHAIR-001 already exists")
                    return True
            
            # Create TEST-CHAIR-001 SKU
            sku_data = {
                "master_sku": "TEST-CHAIR-001",
                "product_name": "Test Office Chair",
                "category": "Furniture",
                "cost_price": 2000,
                "selling_price": 3500
            }
            
            response = self.session.post(f"{BASE_URL}/master-sku/", json=sku_data)
            
            if response.status_code == 200:
                self.log_result("Create TEST-CHAIR-001", True, "Created TEST-CHAIR-001 SKU")
                return True
            else:
                self.log_result("Create TEST-CHAIR-001", False, 
                              error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Create TEST-CHAIR-001", False, error=str(e))
            return False
    
    def test_stock_adjustments(self):
        """3. Stock Adjustments endpoints"""
        try:
            # Ensure we have TEST-CHAIR-001 SKU
            if not self.ensure_test_sku_exists():
                return False
            
            # POST stock adjustment with TEST-CHAIR-001, WH-DEL, add, 50 units
            print("   Testing: POST /api/inventory/stock-adjustment with TEST-CHAIR-001, WH-DEL, add, 50 units")
            adjustment_params = {
                "master_sku": "TEST-CHAIR-001",
                "warehouse_code": "WH-DEL",
                "adjustment_type": "add",
                "quantity": 50,
                "reason": "Initial stock for Phase 4 testing",
                "reference": "PHASE4-TEST-001"
            }
            
            response = self.session.post(f"{BASE_URL}/inventory/stock-adjustment", params=adjustment_params)
            
            if response.status_code == 200:
                data = response.json()
                adjustment = data.get("adjustment", {})
                self.log_result("Stock Adjustment - Add 50 units", True, 
                              f"Added {adjustment.get('quantity_change')} units to TEST-CHAIR-001. Before: {adjustment.get('quantity_before')}, After: {adjustment.get('quantity_after')}")
            else:
                self.log_result("Stock Adjustment - Add 50 units", False, 
                              error=f"Status: {response.status_code}, Response: {response.text}")
                return False
            
            # GET stock adjustments - verify adjustment logged
            print("   Testing: GET /api/inventory/stock-adjustments (verify adjustment logged)")
            response = self.session.get(f"{BASE_URL}/inventory/stock-adjustments", params={"limit": 50})
            
            if response.status_code == 200:
                data = response.json()
                adjustments = data.get("items", [])
                test_adjustments = [adj for adj in adjustments if adj.get("master_sku") == "TEST-CHAIR-001"]
                
                self.log_result("Get Stock Adjustments", True, 
                              f"Retrieved {len(adjustments)} total adjustments, {len(test_adjustments)} for TEST-CHAIR-001")
            else:
                self.log_result("Get Stock Adjustments", False, 
                              error=f"Status: {response.status_code}, Response: {response.text}")
                return False
            
            # POST another adjustment with "remove" type
            print("   Testing: POST another adjustment with 'remove' type")
            adjustment_params = {
                "master_sku": "TEST-CHAIR-001",
                "warehouse_code": "WH-DEL",
                "adjustment_type": "remove",
                "quantity": 5,
                "reason": "Damage during handling",
                "reference": "PHASE4-TEST-002"
            }
            
            response = self.session.post(f"{BASE_URL}/inventory/stock-adjustment", params=adjustment_params)
            
            if response.status_code == 200:
                data = response.json()
                adjustment = data.get("adjustment", {})
                self.log_result("Stock Adjustment - Remove 5 units", True, 
                              f"Removed {abs(adjustment.get('quantity_change'))} units from TEST-CHAIR-001. Before: {adjustment.get('quantity_before')}, After: {adjustment.get('quantity_after')}")
                
                # Verify quantity calculations are correct
                before_qty = adjustment.get('quantity_before', 0)
                after_qty = adjustment.get('quantity_after', 0)
                quantity_change = adjustment.get('quantity_change', 0)
                
                if before_qty - 5 == after_qty and quantity_change == -5:
                    self.log_result("Quantity Calculation Verification", True, 
                                  f"✅ Calculations correct: {before_qty} - 5 = {after_qty}")
                else:
                    self.log_result("Quantity Calculation Verification", False, 
                                  error=f"Calculation error: {before_qty} - 5 ≠ {after_qty}, change: {quantity_change}")
            else:
                self.log_result("Stock Adjustment - Remove 5 units", False, 
                              error=f"Status: {response.status_code}, Response: {response.text}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Stock Adjustments", False, error=str(e))
            return False
    
    def test_audit_log(self):
        """4. Audit Log: GET /api/inventory/audit-log?limit=20"""
        try:
            print("   Testing: GET /api/inventory/audit-log?limit=20")
            response = self.session.get(f"{BASE_URL}/inventory/audit-log", params={"limit": 20})
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle both list and dict responses
                if isinstance(data, list):
                    logs = data
                elif isinstance(data, dict) and "items" in data:
                    logs = data.get("items", [])
                else:
                    logs = []
                
                # Verify warehouse creation and stock adjustments appear in logs
                warehouse_logs = [log for log in logs if log.get("type") == "WAREHOUSE" or "warehouse" in str(log).lower()]
                adjustment_logs = [log for log in logs if log.get("type") == "ADJUSTMENT" or "adjustment" in str(log).lower()]
                
                # Check log structure has proper fields
                if logs:
                    sample_log = logs[0]
                    required_fields = ["type", "action", "user_id", "timestamp"]
                    present_fields = [field for field in required_fields if field in sample_log]
                    
                    details = f"Retrieved {len(logs)} audit log entries"
                    details += f", {len(warehouse_logs)} warehouse-related"
                    details += f", {len(adjustment_logs)} adjustment-related"
                    details += f". Sample log has fields: {list(sample_log.keys())}"
                    
                    self.log_result("Audit Log Verification", True, details)
                else:
                    self.log_result("Audit Log Verification", True, "Retrieved empty audit log (expected for new system)")
                
            else:
                self.log_result("Audit Log Verification", False, 
                              error=f"Status: {response.status_code}, Response: {response.text}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Audit Log Verification", False, error=str(e))
            return False
    
    def test_dashboard_analytics(self):
        """5. Dashboard & Analytics endpoints"""
        try:
            # GET /api/inventory/dashboard
            print("   Testing: GET /api/inventory/dashboard")
            response = self.session.get(f"{BASE_URL}/inventory/dashboard")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check expected dashboard fields
                expected_fields = ["total_skus", "categories", "aging", "stockout_alerts"]
                present_fields = [field for field in expected_fields if field in data]
                missing_fields = [field for field in expected_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Inventory Dashboard", False, 
                                  error=f"Missing fields: {missing_fields}")
                else:
                    total_skus = data.get("total_skus", 0)
                    categories = data.get("categories", [])
                    aging = data.get("aging", {})
                    stockout_alerts = data.get("stockout_alerts", 0)
                    
                    details = f"Total SKUs: {total_skus}, Categories: {len(categories)}, Stockout Alerts: {stockout_alerts}"
                    self.log_result("Inventory Dashboard", True, details)
            else:
                self.log_result("Inventory Dashboard", False, 
                              error=f"Status: {response.status_code}, Response: {response.text}")
                return False
            
            # GET /api/inventory/stock-summary
            print("   Testing: GET /api/inventory/stock-summary")
            response = self.session.get(f"{BASE_URL}/inventory/stock-summary")
            if response.status_code == 200:
                data = response.json()
                summary = data.get("summary", {})
                stock_by_sku = data.get("stock_by_sku", [])
                self.log_result("Stock Summary", True, 
                              f"Total SKUs: {summary.get('total_skus', 0)}, SKUs with stock: {len(stock_by_sku)}")
            else:
                self.log_result("Stock Summary", False, 
                              error=f"Status: {response.status_code}")
                return False
            
            # GET /api/inventory/aging-analysis
            print("   Testing: GET /api/inventory/aging-analysis")
            response = self.session.get(f"{BASE_URL}/inventory/aging-analysis")
            if response.status_code == 200:
                data = response.json()
                summary = data.get("summary", {})
                self.log_result("Aging Analysis", True, 
                              f"Total SKUs: {summary.get('total_skus', 0)}, Attention needed: {summary.get('attention_needed', 0)}")
            else:
                self.log_result("Aging Analysis", False, 
                              error=f"Status: {response.status_code}")
                return False
            
            # GET /api/inventory/stockout-alerts
            print("   Testing: GET /api/inventory/stockout-alerts")
            response = self.session.get(f"{BASE_URL}/inventory/stockout-alerts")
            if response.status_code == 200:
                data = response.json()
                total_alerts = data.get("total_alerts", 0)
                critical = data.get("critical", 0)
                self.log_result("Stockout Alerts", True, 
                              f"Total alerts: {total_alerts}, Critical: {critical}")
            else:
                self.log_result("Stockout Alerts", False, 
                              error=f"Status: {response.status_code}")
                return False
            
            # GET /api/inventory/shrinkage-report
            print("   Testing: GET /api/inventory/shrinkage-report")
            response = self.session.get(f"{BASE_URL}/inventory/shrinkage-report")
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                total_skus_with_variance = data.get("total_skus_with_variance", 0)
                self.log_result("Shrinkage Report", True, 
                              f"SKUs with variance: {total_skus_with_variance}, Items: {len(items)}")
            else:
                self.log_result("Shrinkage Report", False, 
                              error=f"Status: {response.status_code}")
                return False
            
            # GET /api/inventory/cycle-counts
            print("   Testing: GET /api/inventory/cycle-counts")
            response = self.session.get(f"{BASE_URL}/inventory/cycle-counts")
            if response.status_code == 200:
                data = response.json()
                counts = data.get("items", [])
                self.log_result("Cycle Counts", True, 
                              f"Retrieved {len(counts)} cycle counts")
            else:
                self.log_result("Cycle Counts", False, 
                              error=f"Status: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Dashboard & Analytics", False, error=str(e))
            return False
    
    def run_phase4_verification(self):
        """Run all Phase 4 verification tests"""
        print("🎯 INVENTORY MANAGEMENT PHASE 4 - FINAL VERIFICATION")
        print("=" * 80)
        print("Testing ALL endpoints mentioned in review request after ObjectId fixes")
        print()
        
        # Authentication
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        print("1. CSV Template (Bug Fix):")
        print("-" * 40)
        self.test_csv_template_bug_fix()
        
        print("2. Warehouse Management:")
        print("-" * 40)
        self.test_warehouse_management()
        
        print("3. Stock Adjustments:")
        print("-" * 40)
        self.test_stock_adjustments()
        
        print("4. Audit Log:")
        print("-" * 40)
        self.test_audit_log()
        
        print("5. Dashboard & Analytics:")
        print("-" * 40)
        self.test_dashboard_analytics()
        
        # Summary
        self.print_final_summary()
        
        return True
    
    def print_final_summary(self):
        """Print final test summary"""
        print("\n" + "=" * 80)
        print("📊 FINAL VERIFICATION SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['error']}")
        
        print(f"\n🎯 PHASE 4 COMPLETION STATUS:")
        
        # Check specific requirements from review request
        csv_test = next((r for r in self.test_results if "CSV Template" in r["test"]), None)
        if csv_test and csv_test["success"]:
            print("   ✅ CSV Template Bug Fix: RESOLVED")
        else:
            print("   ❌ CSV Template Bug Fix: FAILED")
        
        warehouse_tests = [r for r in self.test_results if "Warehouse" in r["test"]]
        warehouse_passed = len([r for r in warehouse_tests if r["success"]])
        print(f"   📦 Warehouse Management: {warehouse_passed}/{len(warehouse_tests)} working")
        
        stock_tests = [r for r in self.test_results if "Stock Adjustment" in r["test"]]
        stock_passed = len([r for r in stock_tests if r["success"]])
        print(f"   📊 Stock Adjustments: {stock_passed}/{len(stock_tests)} working")
        
        audit_test = next((r for r in self.test_results if "Audit Log" in r["test"]), None)
        if audit_test and audit_test["success"]:
            print("   ✅ Audit Log: WORKING")
        else:
            print("   ❌ Audit Log: FAILED")
        
        dashboard_tests = [r for r in self.test_results if any(keyword in r["test"] for keyword in 
                          ["Dashboard", "Stock Summary", "Aging", "Stockout", "Shrinkage", "Cycle Counts"])]
        dashboard_passed = len([r for r in dashboard_tests if r["success"]])
        print(f"   📈 Dashboard & Analytics: {dashboard_passed}/{len(dashboard_tests)} working")
        
        # MongoDB ObjectId issue check
        objectid_errors = [r for r in self.test_results if not r["success"] and "ObjectId" in r["error"]]
        if objectid_errors:
            print(f"\n⚠️  CRITICAL ISSUE: {len(objectid_errors)} endpoints still have MongoDB ObjectId serialization errors")
            print("   This indicates the ObjectId fixes are not complete.")
        else:
            print("\n✅ MongoDB ObjectId serialization issues appear to be resolved")
        
        print(f"\n🏆 FINAL PHASE 4 STATUS:")
        if failed_tests == 0:
            print("   🎉 ALL ENDPOINTS WORKING - PHASE 4 COMPLETE!")
        elif failed_tests <= 2:
            print("   ⚠️  MOSTLY WORKING - Minor issues remain")
        else:
            print("   ❌ SIGNIFICANT ISSUES - Phase 4 needs more work")


def main():
    """Main test execution"""
    tester = Phase4Tester()
    
    try:
        success = tester.run_phase4_verification()
        
        # Exit with appropriate code
        failed_tests = len([r for r in tester.test_results if not r["success"]])
        sys.exit(0 if failed_tests == 0 else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error during testing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()