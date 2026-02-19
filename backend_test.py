#!/usr/bin/env python3
"""
Comprehensive Backend API Tests for FuelPoint Navigator
Tests all endpoints with proper filtering and validation
"""
import requests
import json
import sys
from datetime import datetime

# Base URL from frontend environment
BASE_URL = "https://green-fuel-map.preview.emergentagent.com/api"

# Colors for output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class APITester:
    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_results = []
    
    def log(self, message, level="INFO"):
        """Log message with color coding"""
        color = {
            "PASS": Colors.GREEN,
            "FAIL": Colors.RED,
            "WARN": Colors.YELLOW,
            "INFO": Colors.BLUE
        }.get(level, Colors.BLUE)
        print(f"{color}{level}: {message}{Colors.END}")
    
    def test_endpoint(self, endpoint, expected_status=200, method="GET", data=None, description=""):
        """Generic endpoint tester"""
        self.total_tests += 1
        url = f"{BASE_URL}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, timeout=30)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=30)
            elif method == "PUT":
                response = requests.put(url, json=data, timeout=30)
            elif method == "DELETE":
                response = requests.delete(url, timeout=30)
            
            if response.status_code == expected_status:
                self.passed_tests += 1
                self.log(f"✅ {method} {endpoint} - {description}", "PASS")
                return response.json() if response.content else {}
            else:
                self.failed_tests += 1
                self.log(f"❌ {method} {endpoint} - Expected {expected_status}, got {response.status_code}", "FAIL")
                self.log(f"Response: {response.text[:500]}", "FAIL")
                return None
                
        except Exception as e:
            self.failed_tests += 1
            self.log(f"❌ {method} {endpoint} - Exception: {str(e)}", "FAIL")
            return None
    
    def validate_response_count(self, response, expected_count, description):
        """Validate response array length"""
        if response and isinstance(response, list):
            actual_count = len(response)
            if actual_count == expected_count:
                self.log(f"✅ {description} - Got {actual_count} items as expected", "PASS")
                return True
            else:
                self.log(f"❌ {description} - Expected {expected_count}, got {actual_count}", "FAIL")
                return False
        else:
            self.log(f"❌ {description} - Invalid response format", "FAIL")
            return False
    
    def validate_filter_result(self, response, filter_field, filter_value, description):
        """Validate that all items in response match the filter"""
        if not response or not isinstance(response, list):
            self.log(f"❌ {description} - Invalid response", "FAIL")
            return False
        
        for item in response:
            if filter_field == "fuel_types" or filter_field == "fuel_specializations":
                # For array fields, check if filter_value is in the array
                if filter_value not in item.get(filter_field, []):
                    self.log(f"❌ {description} - Item {item.get('id', 'unknown')} doesn't match filter", "FAIL")
                    return False
            else:
                # For string fields, exact match
                if item.get(filter_field) != filter_value:
                    self.log(f"❌ {description} - Item {item.get('id', 'unknown')} doesn't match filter", "FAIL")
                    return False
        
        self.log(f"✅ {description} - All {len(response)} items match filter", "PASS")
        return True
    
    def test_health_and_utility(self):
        """Test health check and utility endpoints"""
        self.log("\n" + "="*60, "INFO")
        self.log("TESTING HEALTH & UTILITY ENDPOINTS", "INFO")
        self.log("="*60, "INFO")
        
        # Health check
        self.test_endpoint("/health", description="Health check")
        
        # Fuel types
        fuel_types = self.test_endpoint("/fuel-types", description="Get fuel types")
        if fuel_types:
            self.validate_response_count(fuel_types, 7, "Fuel types count validation")
    
    def test_fuel_stations(self):
        """Test all fuel station endpoints"""
        self.log("\n" + "="*60, "INFO")
        self.log("TESTING FUEL STATION ENDPOINTS", "INFO") 
        self.log("="*60, "INFO")
        
        # Get all stations
        stations = self.test_endpoint("/stations", description="Get all stations")
        if stations:
            self.validate_response_count(stations, 8, "All stations count validation")
        
        # Filter by CNG fuel type
        cng_stations = self.test_endpoint("/stations?fuel_type=CNG", description="Filter by CNG fuel type")
        if cng_stations:
            self.validate_filter_result(cng_stations, "fuel_types", "CNG", "CNG filter validation")
        
        # Filter by Hydrogen fuel type
        hydrogen_stations = self.test_endpoint("/stations?fuel_type=Hydrogen", description="Filter by Hydrogen fuel type")
        if hydrogen_stations:
            self.validate_filter_result(hydrogen_stations, "fuel_types", "Hydrogen", "Hydrogen filter validation")
        
        # Filter by California state
        ca_stations = self.test_endpoint("/stations?state=CA", description="Filter by California state")
        if ca_stations:
            self.validate_filter_result(ca_stations, "state", "CA", "California state filter validation")
        
        # Get single station
        self.test_endpoint("/stations/station-001", description="Get single station details")
        
        # Test non-existent station
        self.test_endpoint("/stations/non-existent", expected_status=404, description="Non-existent station (should fail)")
    
    def test_regulations(self):
        """Test all regulation endpoints"""
        self.log("\n" + "="*60, "INFO")
        self.log("TESTING REGULATION ENDPOINTS", "INFO")
        self.log("="*60, "INFO")
        
        # Get all regulations
        regulations = self.test_endpoint("/regulations", description="Get all regulations")
        if regulations:
            self.validate_response_count(regulations, 8, "All regulations count validation")
        
        # Filter by Safety category
        safety_regs = self.test_endpoint("/regulations?category=Safety", description="Filter by Safety category")
        if safety_regs:
            self.validate_filter_result(safety_regs, "category", "Safety", "Safety category filter validation")
        
        # Filter by Federal jurisdiction
        federal_regs = self.test_endpoint("/regulations?jurisdiction=Federal", description="Filter by Federal jurisdiction")
        if federal_regs:
            self.validate_filter_result(federal_regs, "jurisdiction", "Federal", "Federal jurisdiction filter validation")
        
        # Get single regulation
        self.test_endpoint("/regulations/reg-001", description="Get single regulation details")
        
        # Test non-existent regulation
        self.test_endpoint("/regulations/non-existent", expected_status=404, description="Non-existent regulation (should fail)")
    
    def test_service_centers(self):
        """Test all service center endpoints"""
        self.log("\n" + "="*60, "INFO")
        self.log("TESTING SERVICE CENTER ENDPOINTS", "INFO")
        self.log("="*60, "INFO")
        
        # Get all service centers
        centers = self.test_endpoint("/service-centers", description="Get all service centers")
        if centers:
            self.validate_response_count(centers, 5, "All service centers count validation")
        
        # Filter by CNG specialization
        cng_centers = self.test_endpoint("/service-centers?fuel_type=CNG", description="Filter by CNG specialization")
        if cng_centers:
            self.validate_filter_result(cng_centers, "fuel_specializations", "CNG", "CNG specialization filter validation")
        
        # Filter by Mobile service type
        mobile_centers = self.test_endpoint("/service-centers?service_type=Mobile", description="Filter by Mobile service type")
        if mobile_centers:
            self.validate_filter_result(mobile_centers, "service_type", "Mobile", "Mobile service type filter validation")
        
        # Get single service center
        self.test_endpoint("/service-centers/service-001", description="Get single service center")
        
        # Test non-existent service center
        self.test_endpoint("/service-centers/non-existent", expected_status=404, description="Non-existent service center (should fail)")
    
    def test_inspectors(self):
        """Test all inspector endpoints"""
        self.log("\n" + "="*60, "INFO")
        self.log("TESTING INSPECTOR ENDPOINTS", "INFO")
        self.log("="*60, "INFO")
        
        # Get all inspectors
        inspectors = self.test_endpoint("/inspectors", description="Get all inspectors")
        if inspectors:
            self.validate_response_count(inspectors, 5, "All inspectors count validation")
        
        # Filter by Hydrogen specialization
        hydrogen_inspectors = self.test_endpoint("/inspectors?fuel_type=Hydrogen", description="Filter by Hydrogen specialization")
        if hydrogen_inspectors:
            self.validate_filter_result(hydrogen_inspectors, "fuel_specializations", "Hydrogen", "Hydrogen specialization filter validation")
        
        # Filter by California state
        ca_inspectors = self.test_endpoint("/inspectors?state=CA", description="Filter by California state")
        if ca_inspectors:
            self.validate_filter_result(ca_inspectors, "state", "CA", "California inspector filter validation")
        
        # Get single inspector
        self.test_endpoint("/inspectors/inspector-001", description="Get single inspector details")
        
        # Test non-existent inspector
        self.test_endpoint("/inspectors/non-existent", expected_status=404, description="Non-existent inspector (should fail)")
    
    def test_user_profile(self):
        """Test user profile endpoints"""
        self.log("\n" + "="*60, "INFO")
        self.log("TESTING USER PROFILE ENDPOINTS", "INFO")
        self.log("="*60, "INFO")
        
        # Get profile (creates default if not exists)
        profile = self.test_endpoint("/profile", description="Get user profile")
        
        # Update profile
        update_data = {
            "name": "Test User",
            "email": "test@example.com"
        }
        updated_profile = self.test_endpoint("/profile", method="PUT", data=update_data, description="Update profile")
        
        if updated_profile:
            if updated_profile.get("name") == "Test User" and updated_profile.get("email") == "test@example.com":
                self.log("✅ Profile update validation - Name and email updated correctly", "PASS")
            else:
                self.log("❌ Profile update validation - Values not updated correctly", "FAIL")
        
        # Add station to favorites
        self.test_endpoint("/profile/favorites/station-001", method="POST", description="Add station to favorites")
        
        # Remove station from favorites
        self.test_endpoint("/profile/favorites/station-001", method="DELETE", description="Remove station from favorites")
    
    def run_all_tests(self):
        """Run all test suites"""
        self.log(f"\n{Colors.BOLD}🚀 STARTING FUELPOINT NAVIGATOR API TESTS{Colors.END}", "INFO")
        self.log(f"Base URL: {BASE_URL}", "INFO")
        self.log(f"Test started at: {datetime.now().isoformat()}", "INFO")
        
        # Run all test suites
        self.test_health_and_utility()
        self.test_fuel_stations()
        self.test_regulations()
        self.test_service_centers()
        self.test_inspectors()
        self.test_user_profile()
        
        # Print final results
        self.log("\n" + "="*60, "INFO")
        self.log(f"{Colors.BOLD}FINAL TEST RESULTS{Colors.END}", "INFO")
        self.log("="*60, "INFO")
        self.log(f"Total Tests: {self.total_tests}", "INFO")
        self.log(f"Passed: {self.passed_tests}", "PASS")
        self.log(f"Failed: {self.failed_tests}", "FAIL")
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        self.log(f"Success Rate: {success_rate:.1f}%", "INFO")
        
        if self.failed_tests == 0:
            self.log(f"\n🎉 ALL TESTS PASSED! 🎉", "PASS")
            return True
        else:
            self.log(f"\n⚠️  {self.failed_tests} TESTS FAILED", "FAIL")
            return False

def main():
    tester = APITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()