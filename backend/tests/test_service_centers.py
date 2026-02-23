"""
Service Centers API Tests
Tests for GET /api/service-centers endpoint with various filters
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://fuel-hub-app.preview.emergentagent.com')

class TestServiceCentersEndpoint:
    """Test suite for service centers API endpoint"""
    
    def test_get_all_service_centers_returns_118(self):
        """Test that endpoint returns 118 service centers"""
        response = requests.get(f"{BASE_URL}/api/service-centers")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 118, f"Expected 118 service centers, got {len(data)}"
    
    def test_service_centers_have_required_fields(self):
        """Test that each service center has required fields"""
        response = requests.get(f"{BASE_URL}/api/service-centers")
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ['id', 'name', 'address', 'city', 'state', 'zip_code', 
                          'latitude', 'longitude', 'phone', 'fuel_specializations',
                          'service_type', 'certifications', 'rating', 'review_count']
        
        for center in data[:5]:  # Check first 5 centers
            for field in required_fields:
                assert field in center, f"Missing field '{field}' in center {center.get('name', 'unknown')}"


class TestCanadianProvinces:
    """Test Canadian provinces are included in service centers"""
    
    def test_alberta_province_ab_exists(self):
        """Test Alberta (AB) service centers exist"""
        response = requests.get(f"{BASE_URL}/api/service-centers?state=AB")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1, "Expected at least 1 Alberta (AB) service center"
        # Verify all returned centers are in AB
        for center in data:
            assert center['state'] == 'AB', f"Expected state AB, got {center['state']}"
    
    def test_british_columbia_bc_exists(self):
        """Test British Columbia (BC) service centers exist"""
        response = requests.get(f"{BASE_URL}/api/service-centers?state=BC")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1, "Expected at least 1 BC service center"
        for center in data:
            assert center['state'] == 'BC', f"Expected state BC, got {center['state']}"
    
    def test_ontario_on_exists(self):
        """Test Ontario (ON) service centers exist"""
        response = requests.get(f"{BASE_URL}/api/service-centers?state=ON")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1, "Expected at least 1 Ontario (ON) service center"
        for center in data:
            assert center['state'] == 'ON', f"Expected state ON, got {center['state']}"
    
    def test_quebec_qc_exists(self):
        """Test Quebec (QC) service centers exist"""
        response = requests.get(f"{BASE_URL}/api/service-centers?state=QC")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1, "Expected at least 1 Quebec (QC) service center"
        for center in data:
            assert center['state'] == 'QC', f"Expected state QC, got {center['state']}"


class TestStateFilter:
    """Test state/province filter functionality"""
    
    def test_filter_by_texas(self):
        """Test filter by state=TX returns Texas locations"""
        response = requests.get(f"{BASE_URL}/api/service-centers?state=TX")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 5, f"Expected at least 5 Texas service centers, got {len(data)}"
        for center in data:
            assert center['state'] == 'TX', f"Expected Texas, got {center['state']}"
    
    def test_filter_by_california(self):
        """Test filter by state=CA returns California locations"""
        response = requests.get(f"{BASE_URL}/api/service-centers?state=CA")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 5, "Expected at least 5 California service centers"
        for center in data:
            assert center['state'] == 'CA'
    
    def test_filter_invalid_state_returns_empty(self):
        """Test filter by invalid state returns empty list"""
        response = requests.get(f"{BASE_URL}/api/service-centers?state=ZZ")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0, f"Expected 0 results for invalid state ZZ, got {len(data)}"


class TestFuelTypeFilter:
    """Test fuel type filter functionality"""
    
    def test_filter_by_hydrogen(self):
        """Test filter by fuel_type=Hydrogen returns hydrogen service centers"""
        response = requests.get(f"{BASE_URL}/api/service-centers?fuel_type=Hydrogen")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 5, f"Expected at least 5 Hydrogen centers, got {len(data)}"
        for center in data:
            assert 'Hydrogen' in center['fuel_specializations'], \
                f"Center {center['name']} missing Hydrogen specialization"
    
    def test_filter_by_cng(self):
        """Test filter by fuel_type=CNG returns CNG service centers"""
        response = requests.get(f"{BASE_URL}/api/service-centers?fuel_type=CNG")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 50, "Expected at least 50 CNG service centers"
        for center in data[:10]:  # Check first 10
            assert 'CNG' in center['fuel_specializations']
    
    def test_filter_by_electric(self):
        """Test filter by fuel_type=Electric returns EV service centers"""
        response = requests.get(f"{BASE_URL}/api/service-centers?fuel_type=Electric")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1, "Expected at least 1 Electric service center"
        for center in data:
            assert 'Electric' in center['fuel_specializations']
    
    def test_filter_by_lng(self):
        """Test filter by fuel_type=LNG returns LNG service centers"""
        response = requests.get(f"{BASE_URL}/api/service-centers?fuel_type=LNG")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 10, "Expected at least 10 LNG service centers"
        for center in data:
            assert 'LNG' in center['fuel_specializations']


class TestServiceTypeFilter:
    """Test service type filter functionality"""
    
    def test_filter_by_in_shop(self):
        """Test filter by service_type=In-Shop"""
        response = requests.get(f"{BASE_URL}/api/service-centers?service_type=In-Shop")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 100, f"Expected at least 100 In-Shop centers, got {len(data)}"
        for center in data[:10]:
            assert center['service_type'] == 'In-Shop'
    
    def test_filter_by_both(self):
        """Test filter by service_type=Both (Mobile + In-Shop)"""
        response = requests.get(f"{BASE_URL}/api/service-centers?service_type=Both")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 5, f"Expected at least 5 'Both' service type centers, got {len(data)}"
        for center in data:
            assert center['service_type'] == 'Both'
    
    def test_filter_by_mobile_may_return_empty(self):
        """Test filter by service_type=Mobile (may return empty if none exist)"""
        response = requests.get(f"{BASE_URL}/api/service-centers?service_type=Mobile")
        assert response.status_code == 200
        data = response.json()
        # This may return empty if no pure Mobile service centers exist
        for center in data:
            assert center['service_type'] == 'Mobile'


class TestCombinedFilters:
    """Test combined filter functionality"""
    
    def test_filter_state_and_fuel_type(self):
        """Test combined state and fuel_type filters"""
        response = requests.get(f"{BASE_URL}/api/service-centers?state=CA&fuel_type=Hydrogen")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1, "Expected at least 1 CA Hydrogen center"
        for center in data:
            assert center['state'] == 'CA'
            assert 'Hydrogen' in center['fuel_specializations']
    
    def test_filter_state_and_service_type(self):
        """Test combined state and service_type filters"""
        response = requests.get(f"{BASE_URL}/api/service-centers?state=TX&service_type=Both")
        assert response.status_code == 200
        data = response.json()
        for center in data:
            assert center['state'] == 'TX'
            assert center['service_type'] == 'Both'


class TestDataQuality:
    """Test data quality and consistency"""
    
    def test_coverage_40_states_provinces(self):
        """Test that 40 unique states/provinces are covered"""
        response = requests.get(f"{BASE_URL}/api/service-centers")
        assert response.status_code == 200
        data = response.json()
        states = set(center['state'] for center in data)
        assert len(states) == 40, f"Expected 40 states/provinces, got {len(states)}: {sorted(states)}"
    
    def test_all_centers_have_phone(self):
        """Test all service centers have phone numbers"""
        response = requests.get(f"{BASE_URL}/api/service-centers")
        assert response.status_code == 200
        data = response.json()
        for center in data:
            assert center['phone'], f"Center {center['name']} missing phone number"
    
    def test_all_centers_have_valid_coordinates(self):
        """Test all service centers have valid lat/long"""
        response = requests.get(f"{BASE_URL}/api/service-centers")
        assert response.status_code == 200
        data = response.json()
        for center in data:
            lat = center['latitude']
            lon = center['longitude']
            # North America latitude range: ~25 to ~70
            assert 20 <= lat <= 75, f"Invalid latitude {lat} for {center['name']}"
            # North America longitude range: ~-170 to ~-50
            assert -180 <= lon <= -50, f"Invalid longitude {lon} for {center['name']}"
    
    def test_service_center_ratings_valid(self):
        """Test that ratings are in valid range 0-5"""
        response = requests.get(f"{BASE_URL}/api/service-centers")
        assert response.status_code == 200
        data = response.json()
        for center in data:
            assert 0 <= center['rating'] <= 5, f"Invalid rating {center['rating']} for {center['name']}"
            assert center['review_count'] >= 0, f"Invalid review count for {center['name']}"


class TestIndividualServiceCenter:
    """Test individual service center endpoint"""
    
    def test_get_single_service_center(self):
        """Test fetching a single service center by ID"""
        # First get all centers
        response = requests.get(f"{BASE_URL}/api/service-centers")
        assert response.status_code == 200
        data = response.json()
        
        # Get first center ID
        first_center_id = data[0]['id']
        
        # Fetch individual center
        response = requests.get(f"{BASE_URL}/api/service-centers/{first_center_id}")
        assert response.status_code == 200
        center = response.json()
        assert center['id'] == first_center_id
    
    def test_get_nonexistent_service_center(self):
        """Test fetching non-existent service center returns 404"""
        response = requests.get(f"{BASE_URL}/api/service-centers/nonexistent-id-12345")
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
