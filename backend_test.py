#!/usr/bin/env python3

import requests
import json
import sys
from typing import Dict, Any, List

# Backend URL from the review request
BASE_URL = "https://fuel-hub-app.preview.emergentagent.com/api"

class APITester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results = []
        self.session = requests.Session()
        self.session.timeout = 30
        
    def test_endpoint(self, method: str, endpoint: str, params: dict = None, expected_status: int = 200, description: str = ""):
        """Test an API endpoint and record results"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, json=params)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=params)
            elif method.upper() == "DELETE":
                response = self.session.delete(url)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            success = response.status_code == expected_status
            
            result = {
                "method": method.upper(),
                "endpoint": endpoint,
                "params": params,
                "expected_status": expected_status,
                "actual_status": response.status_code,
                "success": success,
                "description": description,
                "response_size": len(response.text),
                "error": None
            }
            
            if success:
                try:
                    result["data"] = response.json()
                except:
                    result["data"] = response.text[:200] + "..." if len(response.text) > 200 else response.text
            else:
                result["error"] = f"Status {response.status_code}: {response.text[:200]}"
                
        except requests.exceptions.RequestException as e:
            result = {
                "method": method.upper(),
                "endpoint": endpoint,
                "params": params,
                "expected_status": expected_status,
                "actual_status": "ERROR",
                "success": False,
                "description": description,
                "response_size": 0,
                "error": str(e)
            }
        except Exception as e:
            result = {
                "method": method.upper(),
                "endpoint": endpoint,
                "params": params,
                "expected_status": expected_status,
                "actual_status": "EXCEPTION",
                "success": False,
                "description": description,
                "response_size": 0,
                "error": str(e)
            }
        
        self.results.append(result)
        return result
    
    def validate_afdc_data(self, stations_data: List[Dict]) -> Dict[str, Any]:
        """Validate that AFDC data is real and not empty"""
        validation = {
            "has_data": len(stations_data) > 0,
            "count": len(stations_data),
            "has_real_afdc_ids": False,
            "has_coordinates": False,
            "has_fuel_types": False,
            "sample_station": None
        }
        
        if stations_data:
            sample = stations_data[0]
            validation["sample_station"] = {
                "id": sample.get("id"),
                "name": sample.get("name"),
                "fuel_types": sample.get("fuel_types")
            }
            
            # Check for AFDC IDs (should start with "afdc-")
            validation["has_real_afdc_ids"] = any(
                station.get("id", "").startswith("afdc-") for station in stations_data
            )
            
            # Check for valid coordinates
            validation["has_coordinates"] = any(
                station.get("latitude") and station.get("longitude")
                for station in stations_data
            )
            
            # Check for fuel types
            validation["has_fuel_types"] = any(
                station.get("fuel_types") for station in stations_data
            )
        
        return validation
    
    def run_all_tests(self):
        """Run all the tests specified in the review request"""
        
        print("🚀 Starting FuelPoint Navigator Backend API Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 80)
        
        # 1. Health Check
        print("\n🏥 Testing Health Check...")
        health_result = self.test_endpoint("GET", "/health", description="Health check endpoint")
        if health_result["success"]:
            health_data = health_result.get("data", {})
            print(f"✅ Health check passed - Status: {health_data.get('status')}, AFDC Enabled: {health_data.get('afdc_enabled')}")
        else:
            print(f"❌ Health check failed: {health_result.get('error')}")
        
        # 2. Fuel Types
        print("\n⛽ Testing Fuel Types...")
        fuel_types_result = self.test_endpoint("GET", "/fuel-types", description="Fuel types list")
        if fuel_types_result["success"]:
            fuel_types = fuel_types_result.get("data", [])
            print(f"✅ Fuel types retrieved - Count: {len(fuel_types)}")
            if fuel_types:
                print(f"   Sample fuel types: {', '.join([ft.get('name', '') for ft in fuel_types[:3]])}")
        else:
            print(f"❌ Fuel types failed: {fuel_types_result.get('error')}")
        
        # 3. Stations - No filters (should return real AFDC data)
        print("\n🚉 Testing Stations (No Filters)...")
        stations_result = self.test_endpoint("GET", "/stations", description="All stations from AFDC API")
        if stations_result["success"]:
            stations_data = stations_result.get("data", [])
            validation = self.validate_afdc_data(stations_data)
            print(f"✅ Stations retrieved - Count: {validation['count']}")
            print(f"   Real AFDC IDs: {validation['has_real_afdc_ids']}")
            print(f"   Has coordinates: {validation['has_coordinates']}")
            print(f"   Has fuel types: {validation['has_fuel_types']}")
            if validation["sample_station"]:
                sample = validation["sample_station"]
                print(f"   Sample: {sample['name']} ({sample['id']}) - {sample['fuel_types']}")
        else:
            print(f"❌ Stations failed: {stations_result.get('error')}")
        
        # 4. Stations with Electric filter
        print("\n🔌 Testing Stations (Electric Filter)...")
        electric_result = self.test_endpoint("GET", "/stations", {"fuel_type": "Electric"}, description="Electric stations only")
        if electric_result["success"]:
            electric_stations = electric_result.get("data", [])
            print(f"✅ Electric stations retrieved - Count: {len(electric_stations)}")
            if electric_stations:
                sample = electric_stations[0]
                print(f"   Sample: {sample.get('name')} - Fuel types: {sample.get('fuel_types')}")
        else:
            print(f"❌ Electric stations failed: {electric_result.get('error')}")
        
        # 5. Stations with State filter
        print("\n🏛️ Testing Stations (CA State Filter)...")
        ca_result = self.test_endpoint("GET", "/stations", {"state": "CA"}, description="California stations only")
        if ca_result["success"]:
            ca_stations = ca_result.get("data", [])
            print(f"✅ CA stations retrieved - Count: {len(ca_stations)}")
            if ca_stations:
                sample = ca_stations[0]
                print(f"   Sample: {sample.get('name')} in {sample.get('city')}, {sample.get('state')}")
        else:
            print(f"❌ CA stations failed: {ca_result.get('error')}")
        
        # 6. Nearby Stations (Los Angeles coordinates)
        print("\n📍 Testing Nearby Stations...")
        nearby_result = self.test_endpoint("GET", "/stations/nearby", 
                                         {"latitude": 34.0522, "longitude": -118.2437, "radius": 25},
                                         description="Stations near Los Angeles")
        if nearby_result["success"]:
            nearby_stations = nearby_result.get("data", [])
            print(f"✅ Nearby stations retrieved - Count: {len(nearby_stations)}")
            if nearby_stations:
                sample = nearby_stations[0]
                print(f"   Sample: {sample.get('name')} at {sample.get('latitude')}, {sample.get('longitude')}")
        else:
            print(f"❌ Nearby stations failed: {nearby_result.get('error')}")
        
        # 7. Regulations
        print("\n📋 Testing Regulations...")
        regs_result = self.test_endpoint("GET", "/regulations", description="Regulations list")
        if regs_result["success"]:
            regulations = regs_result.get("data", [])
            print(f"✅ Regulations retrieved - Count: {len(regulations)}")
            if regulations:
                sample = regulations[0]
                print(f"   Sample: {sample.get('title')} ({sample.get('jurisdiction')})")
        else:
            print(f"❌ Regulations failed: {regs_result.get('error')}")
        
        # 8. Service Centers
        print("\n🔧 Testing Service Centers...")
        centers_result = self.test_endpoint("GET", "/service-centers", description="Service centers list")
        if centers_result["success"]:
            centers = centers_result.get("data", [])
            print(f"✅ Service centers retrieved - Count: {len(centers)}")
            if centers:
                sample = centers[0]
                print(f"   Sample: {sample.get('name')} - Specializations: {sample.get('fuel_specializations')}")
        else:
            print(f"❌ Service centers failed: {centers_result.get('error')}")
        
        # 9. Inspectors
        print("\n🔍 Testing Inspectors...")
        inspectors_result = self.test_endpoint("GET", "/inspectors", description="Inspectors list")
        if inspectors_result["success"]:
            inspectors = inspectors_result.get("data", [])
            print(f"✅ Inspectors retrieved - Count: {len(inspectors)}")
            if inspectors:
                sample = inspectors[0]
                print(f"   Sample: {sample.get('name')} - Specializations: {sample.get('fuel_specializations')}")
        else:
            print(f"❌ Inspectors failed: {inspectors_result.get('error')}")
        
        # 10. Inspector Lookup Links
        print("\n🔗 Testing Inspector Lookup Links...")
        links_result = self.test_endpoint("GET", "/inspector-lookup-links", description="AFVi and CSA lookup links")
        if links_result["success"]:
            links = links_result.get("data", {})
            afvi_present = "afvi" in links
            csa_present = "csa" in links
            print(f"✅ Inspector lookup links retrieved")
            print(f"   AFVi link present: {afvi_present}")
            print(f"   CSA link present: {csa_present}")
            if afvi_present:
                print(f"   AFVi URL: {links['afvi'].get('url')}")
            if csa_present:
                print(f"   CSA URL: {links['csa'].get('url')}")
        else:
            print(f"❌ Inspector lookup links failed: {links_result.get('error')}")
        
        # 11. Providers (All 15 expected)
        print("\n🏭 Testing Fuel System Providers...")
        providers_result = self.test_endpoint("GET", "/providers", description="All 15 fuel system providers")
        if providers_result["success"]:
            providers = providers_result.get("data", [])
            print(f"✅ Providers retrieved - Count: {len(providers)} (Expected: 15)")
            if providers:
                names = [p.get('name', 'Unknown') for p in providers[:5]]
                print(f"   Sample providers: {', '.join(names)}")
        else:
            print(f"❌ Providers failed: {providers_result.get('error')}")
        
        # 12. Providers with CNG filter
        print("\n🏭 Testing Providers (CNG Filter)...")
        cng_providers_result = self.test_endpoint("GET", "/providers", {"fuel_type": "CNG"}, description="CNG providers only")
        if cng_providers_result["success"]:
            cng_providers = cng_providers_result.get("data", [])
            print(f"✅ CNG providers retrieved - Count: {len(cng_providers)}")
            if cng_providers:
                sample = cng_providers[0]
                print(f"   Sample: {sample.get('name')} - Fuel types: {sample.get('fuel_types')}")
        else:
            print(f"❌ CNG providers failed: {cng_providers_result.get('error')}")
        
        # 13. Providers with Cummins search
        print("\n🔍 Testing Providers (Cummins Search)...")
        cummins_result = self.test_endpoint("GET", "/providers", {"search": "Cummins"}, description="Search for Cummins")
        if cummins_result["success"]:
            cummins_providers = cummins_result.get("data", [])
            print(f"✅ Cummins search retrieved - Count: {len(cummins_providers)}")
            if cummins_providers:
                sample = cummins_providers[0]
                print(f"   Found: {sample.get('name')} - {sample.get('description')[:100]}...")
        else:
            print(f"❌ Cummins search failed: {cummins_result.get('error')}")
        
        # 14. Specific Provider (Hexagon Agility)
        print("\n🎯 Testing Specific Provider (provider-001)...")
        hexagon_result = self.test_endpoint("GET", "/providers/provider-001", description="Hexagon Agility details")
        if hexagon_result["success"]:
            hexagon = hexagon_result.get("data", {})
            print(f"✅ Hexagon Agility retrieved")
            print(f"   Name: {hexagon.get('name')}")
            print(f"   Headquarters: {hexagon.get('headquarters')}")
            print(f"   Fuel types: {hexagon.get('fuel_types')}")
        else:
            print(f"❌ Hexagon Agility failed: {hexagon_result.get('error')}")
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n🚨 FAILED TESTS:")
            for result in self.results:
                if not result["success"]:
                    print(f"   ❌ {result['method']} {result['endpoint']} - {result.get('error', 'Unknown error')}")
        
        print("\n🔍 DETAILED RESULTS:")
        for result in self.results:
            status_icon = "✅" if result["success"] else "❌"
            print(f"   {status_icon} {result['method']} {result['endpoint']} - Status: {result['actual_status']}")
            if result.get("description"):
                print(f"      {result['description']}")

def main():
    """Main test runner"""
    tester = APITester(BASE_URL)
    tester.run_all_tests()
    
    # Return exit code based on results
    failed_tests = sum(1 for r in tester.results if not r["success"])
    sys.exit(1 if failed_tests > 0 else 0)

if __name__ == "__main__":
    main()