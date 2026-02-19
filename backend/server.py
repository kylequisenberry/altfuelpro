from fastapi import FastAPI, APIRouter, Query, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="FuelPoint Navigator API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== ENUMS ====================
class FuelType(str, Enum):
    CNG = "CNG"
    LNG = "LNG"
    HYDROGEN = "Hydrogen"
    ELECTRIC = "Electric"
    DIESEL = "Diesel"
    GASOLINE = "Gasoline"
    BIODIESEL = "Biodiesel"

class ServiceType(str, Enum):
    MOBILE = "Mobile"
    IN_SHOP = "In-Shop"
    BOTH = "Both"

# ==================== MODELS ====================

# Fuel Station Models
class FuelStation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    address: str
    city: str
    state: str
    zip_code: str
    latitude: float
    longitude: float
    fuel_types: List[FuelType]
    phone: Optional[str] = None
    hours: Optional[str] = None
    amenities: List[str] = []
    card_accepted: List[str] = []
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    status: str = "Operational"
    prices: Optional[dict] = None

# Regulation Models
class Regulation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    fuel_types: List[FuelType]
    category: str  # Safety, Emissions, Installation, etc.
    jurisdiction: str  # Federal, State, Local
    state: Optional[str] = None
    code_reference: Optional[str] = None  # e.g., NFPA 52, SAE J2601
    effective_date: Optional[str] = None
    summary: str
    pdf_url: Optional[str] = None

# Service Center Models
class ServiceCenter(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    address: str
    city: str
    state: str
    zip_code: str
    latitude: float
    longitude: float
    phone: str
    email: Optional[str] = None
    website: Optional[str] = None
    fuel_specializations: List[FuelType]
    service_type: ServiceType
    certifications: List[str] = []
    rating: float = 0.0
    review_count: int = 0
    hours: Optional[str] = None
    services_offered: List[str] = []

# Inspector Models
class Inspector(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    company: Optional[str] = None
    phone: str
    email: str
    city: str
    state: str
    latitude: float
    longitude: float
    fuel_specializations: List[FuelType]
    certifications: List[str] = []
    license_number: Optional[str] = None
    years_experience: int = 0
    service_area: List[str] = []  # List of cities/regions covered
    rating: float = 0.0
    review_count: int = 0
    bio: Optional[str] = None

# User Profile Models
class UserProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Guest User"
    email: Optional[str] = None
    phone: Optional[str] = None
    preferred_fuel_types: List[FuelType] = []
    favorite_stations: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    preferred_fuel_types: Optional[List[FuelType]] = None

# ==================== MOCK DATA ====================

MOCK_STATIONS = [
    {
        "id": "station-001",
        "name": "CleanFuel CNG Station",
        "address": "1234 Green Energy Blvd",
        "city": "Los Angeles",
        "state": "CA",
        "zip_code": "90001",
        "latitude": 34.0522,
        "longitude": -118.2437,
        "fuel_types": ["CNG", "LNG"],
        "phone": "(310) 555-0101",
        "hours": "24/7",
        "amenities": ["Restroom", "Convenience Store", "ATM"],
        "card_accepted": ["Visa", "Mastercard", "Fleet Card"],
        "status": "Operational",
        "prices": {"CNG": 2.49, "LNG": 2.89}
    },
    {
        "id": "station-002",
        "name": "HydroGen Fueling Hub",
        "address": "5678 Future Drive",
        "city": "San Francisco",
        "state": "CA",
        "zip_code": "94102",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "fuel_types": ["Hydrogen"],
        "phone": "(415) 555-0202",
        "hours": "6:00 AM - 10:00 PM",
        "amenities": ["Restroom", "WiFi", "EV Charging"],
        "card_accepted": ["Visa", "Mastercard", "Amex"],
        "status": "Operational",
        "prices": {"Hydrogen": 16.99}
    },
    {
        "id": "station-003",
        "name": "ElectriCharge SuperStation",
        "address": "910 Volt Avenue",
        "city": "San Diego",
        "state": "CA",
        "zip_code": "92101",
        "latitude": 32.7157,
        "longitude": -117.1611,
        "fuel_types": ["Electric"],
        "phone": "(619) 555-0303",
        "hours": "24/7",
        "amenities": ["Restroom", "Lounge", "Coffee Shop", "WiFi"],
        "card_accepted": ["Visa", "Mastercard", "Tesla Network"],
        "status": "Operational",
        "prices": {"Electric": 0.35}
    },
    {
        "id": "station-004",
        "name": "BioDiesel Express",
        "address": "2468 Renewable Road",
        "city": "Portland",
        "state": "OR",
        "zip_code": "97201",
        "latitude": 45.5152,
        "longitude": -122.6784,
        "fuel_types": ["Biodiesel", "Diesel"],
        "phone": "(503) 555-0404",
        "hours": "5:00 AM - 11:00 PM",
        "amenities": ["Restroom", "Truck Parking", "Showers"],
        "card_accepted": ["Visa", "Mastercard", "Fleet Card", "Comdata"],
        "status": "Operational",
        "prices": {"Biodiesel": 4.29, "Diesel": 4.09}
    },
    {
        "id": "station-005",
        "name": "Metro CNG Fleet Center",
        "address": "1357 Transit Way",
        "city": "Denver",
        "state": "CO",
        "zip_code": "80202",
        "latitude": 39.7392,
        "longitude": -104.9903,
        "fuel_types": ["CNG"],
        "phone": "(303) 555-0505",
        "hours": "24/7",
        "amenities": ["Fleet Services", "Truck Wash"],
        "card_accepted": ["Fleet Card", "Clean Energy Card"],
        "status": "Operational",
        "prices": {"CNG": 2.19}
    },
    {
        "id": "station-006",
        "name": "Texas LNG Terminal",
        "address": "7890 Energy Parkway",
        "city": "Houston",
        "state": "TX",
        "zip_code": "77001",
        "latitude": 29.7604,
        "longitude": -95.3698,
        "fuel_types": ["LNG", "CNG"],
        "phone": "(713) 555-0606",
        "hours": "24/7",
        "amenities": ["Restroom", "Fleet Services", "Maintenance Bay"],
        "card_accepted": ["Visa", "Mastercard", "Fleet Card"],
        "status": "Operational",
        "prices": {"LNG": 2.69, "CNG": 2.39}
    },
    {
        "id": "station-007",
        "name": "EcoFuel Multi-Station",
        "address": "4567 Sustainable Street",
        "city": "Phoenix",
        "state": "AZ",
        "zip_code": "85001",
        "latitude": 33.4484,
        "longitude": -112.0740,
        "fuel_types": ["CNG", "Electric", "Hydrogen"],
        "phone": "(602) 555-0707",
        "hours": "6:00 AM - 12:00 AM",
        "amenities": ["Restroom", "Convenience Store", "Car Wash"],
        "card_accepted": ["Visa", "Mastercard", "Amex"],
        "status": "Operational",
        "prices": {"CNG": 2.59, "Electric": 0.32, "Hydrogen": 17.49}
    },
    {
        "id": "station-008",
        "name": "Northeast Hydrogen Hub",
        "address": "321 Innovation Lane",
        "city": "Boston",
        "state": "MA",
        "zip_code": "02101",
        "latitude": 42.3601,
        "longitude": -71.0589,
        "fuel_types": ["Hydrogen"],
        "phone": "(617) 555-0808",
        "hours": "7:00 AM - 9:00 PM",
        "amenities": ["Restroom", "WiFi"],
        "card_accepted": ["Visa", "Mastercard"],
        "status": "Under Maintenance",
        "prices": {"Hydrogen": 18.99}
    }
]

MOCK_REGULATIONS = [
    {
        "id": "reg-001",
        "title": "NFPA 52 - Vehicular Natural Gas Fuel Systems Code",
        "description": "Standard for compressed natural gas (CNG) and liquefied natural gas (LNG) vehicular fuel systems.",
        "fuel_types": ["CNG", "LNG"],
        "category": "Safety",
        "jurisdiction": "Federal",
        "code_reference": "NFPA 52",
        "effective_date": "2023-01-01",
        "summary": "Covers installation, maintenance, and operation of CNG and LNG fuel systems in vehicles. Includes requirements for fuel containers, piping, and dispensing equipment."
    },
    {
        "id": "reg-002",
        "title": "SAE J2601 - Hydrogen Fueling Protocol",
        "description": "Standard for fueling light duty gaseous hydrogen surface vehicles.",
        "fuel_types": ["Hydrogen"],
        "category": "Safety",
        "jurisdiction": "Federal",
        "code_reference": "SAE J2601",
        "effective_date": "2024-06-01",
        "summary": "Defines the protocol for safely fueling hydrogen vehicles, including temperature, pressure, and communication requirements between vehicle and dispenser."
    },
    {
        "id": "reg-003",
        "title": "DOT FMVSS 304 - CNG Fuel Container Integrity",
        "description": "Federal Motor Vehicle Safety Standard for CNG fuel container integrity.",
        "fuel_types": ["CNG"],
        "category": "Safety",
        "jurisdiction": "Federal",
        "code_reference": "49 CFR 571.304",
        "effective_date": "2022-01-01",
        "summary": "Specifies requirements for the integrity of compressed natural gas motor vehicle fuel containers to minimize the hazard of death and injury."
    },
    {
        "id": "reg-004",
        "title": "California LCFS - Low Carbon Fuel Standard",
        "description": "California's program to reduce the carbon intensity of transportation fuels.",
        "fuel_types": ["CNG", "LNG", "Hydrogen", "Electric", "Biodiesel"],
        "category": "Emissions",
        "jurisdiction": "State",
        "state": "CA",
        "code_reference": "17 CCR 95480-95503",
        "effective_date": "2024-01-01",
        "summary": "Requires fuel providers to meet declining carbon intensity benchmarks. Provides credits for low-carbon fuel production and use."
    },
    {
        "id": "reg-005",
        "title": "NFPA 2 - Hydrogen Technologies Code",
        "description": "Comprehensive code for hydrogen technologies including storage, use, and handling.",
        "fuel_types": ["Hydrogen"],
        "category": "Safety",
        "jurisdiction": "Federal",
        "code_reference": "NFPA 2",
        "effective_date": "2023-07-01",
        "summary": "Provides fundamental safeguards for the generation, installation, storage, piping, use, and handling of hydrogen in compressed gas or cryogenic liquid form."
    },
    {
        "id": "reg-006",
        "title": "EPA Renewable Fuel Standard (RFS)",
        "description": "Federal program requiring transportation fuel to contain minimum volumes of renewable fuels.",
        "fuel_types": ["Biodiesel", "CNG", "LNG"],
        "category": "Emissions",
        "jurisdiction": "Federal",
        "code_reference": "40 CFR Part 80",
        "effective_date": "2024-01-01",
        "summary": "Mandates the blending of renewable fuels into the nation's fuel supply. Sets annual volume requirements for various categories of renewable fuel."
    },
    {
        "id": "reg-007",
        "title": "NEC Article 625 - Electric Vehicle Charging",
        "description": "National Electrical Code requirements for EV charging equipment and installations.",
        "fuel_types": ["Electric"],
        "category": "Installation",
        "jurisdiction": "Federal",
        "code_reference": "NEC Article 625",
        "effective_date": "2023-01-01",
        "summary": "Covers the electrical conductors and equipment connecting an electric vehicle to a premises wiring system for charging, power export, or bidirectional operation."
    },
    {
        "id": "reg-008",
        "title": "Texas Alternative Fuels Tax Exemption",
        "description": "State tax incentives for alternative fuel vehicles and fueling infrastructure.",
        "fuel_types": ["CNG", "LNG", "Hydrogen", "Electric"],
        "category": "Incentive",
        "jurisdiction": "State",
        "state": "TX",
        "code_reference": "TX Tax Code 152.0925",
        "effective_date": "2024-01-01",
        "summary": "Provides sales tax exemption for alternative fuel vehicles and equipment. Includes rebates for installing alternative fueling infrastructure."
    }
]

MOCK_SERVICE_CENTERS = [
    {
        "id": "service-001",
        "name": "GreenTech Vehicle Services",
        "address": "500 Mechanic Way",
        "city": "Los Angeles",
        "state": "CA",
        "zip_code": "90015",
        "latitude": 34.0407,
        "longitude": -118.2668,
        "phone": "(310) 555-1001",
        "email": "service@greentech.com",
        "website": "https://greentechvehicle.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["ASE Certified", "EPA 609", "CNG/LNG Specialist"],
        "rating": 4.8,
        "review_count": 156,
        "hours": "Mon-Fri 7AM-6PM, Sat 8AM-2PM",
        "services_offered": ["Tank Inspection", "System Repair", "Conversion Installation", "Annual Certification"]
    },
    {
        "id": "service-002",
        "name": "HydroPro Service Center",
        "address": "750 Fuel Cell Blvd",
        "city": "San Francisco",
        "state": "CA",
        "zip_code": "94107",
        "latitude": 37.7648,
        "longitude": -122.3995,
        "phone": "(415) 555-2002",
        "email": "support@hydropro.com",
        "website": "https://hydropro.com",
        "fuel_specializations": ["Hydrogen"],
        "service_type": "Both",
        "certifications": ["Hydrogen Safety Certified", "OEM Authorized", "ISO 14001"],
        "rating": 4.9,
        "review_count": 89,
        "hours": "Mon-Fri 8AM-5PM",
        "services_offered": ["Fuel Cell Diagnostics", "Stack Replacement", "System Maintenance", "Emergency Roadside"]
    },
    {
        "id": "service-003",
        "name": "EV Masters",
        "address": "1200 Battery Lane",
        "city": "San Diego",
        "state": "CA",
        "zip_code": "92121",
        "latitude": 32.8998,
        "longitude": -117.2015,
        "phone": "(619) 555-3003",
        "email": "help@evmasters.com",
        "fuel_specializations": ["Electric"],
        "service_type": "In-Shop",
        "certifications": ["Tesla Certified", "Rivian Authorized", "High Voltage Certified"],
        "rating": 4.7,
        "review_count": 234,
        "hours": "Mon-Sat 8AM-6PM",
        "services_offered": ["Battery Diagnostics", "Charger Installation", "Motor Repair", "Software Updates"]
    },
    {
        "id": "service-004",
        "name": "FleetCare Mobile Services",
        "address": "Service Area: Greater Denver",
        "city": "Denver",
        "state": "CO",
        "zip_code": "80202",
        "latitude": 39.7500,
        "longitude": -104.9800,
        "phone": "(303) 555-4004",
        "email": "dispatch@fleetcare.com",
        "fuel_specializations": ["CNG", "LNG", "Diesel"],
        "service_type": "Mobile",
        "certifications": ["DOT Certified", "CNG Safety Certified", "Fleet Maintenance Specialist"],
        "rating": 4.6,
        "review_count": 312,
        "hours": "24/7 Emergency Available",
        "services_offered": ["On-Site Repairs", "Tank Inspections", "Emergency Response", "Fleet Maintenance Contracts"]
    },
    {
        "id": "service-005",
        "name": "Alternative Fuel Systems Inc.",
        "address": "8900 Industrial Park",
        "city": "Houston",
        "state": "TX",
        "zip_code": "77041",
        "latitude": 29.8200,
        "longitude": -95.5500,
        "phone": "(713) 555-5005",
        "email": "info@altfuelsystems.com",
        "website": "https://altfuelsystems.com",
        "fuel_specializations": ["CNG", "LNG", "Hydrogen", "Biodiesel"],
        "service_type": "Both",
        "certifications": ["ASE Master Certified", "EPA Certified", "Multi-Fuel Specialist"],
        "rating": 4.5,
        "review_count": 178,
        "hours": "Mon-Fri 6AM-8PM, Sat 7AM-3PM",
        "services_offered": ["Full System Conversions", "Compliance Inspections", "Repair Services", "Training"]
    }
]

MOCK_INSPECTORS = [
    {
        "id": "inspector-001",
        "name": "Robert Chen",
        "company": "CNG Safety Inspections LLC",
        "phone": "(310) 555-8001",
        "email": "rchen@cngsafety.com",
        "city": "Los Angeles",
        "state": "CA",
        "latitude": 34.0522,
        "longitude": -118.2437,
        "fuel_specializations": ["CNG", "LNG"],
        "certifications": ["CSA Certified Inspector", "NFPA 52 Qualified", "DOT Inspector"],
        "license_number": "CA-CNG-2024-1234",
        "years_experience": 15,
        "service_area": ["Los Angeles", "Orange County", "Riverside", "San Bernardino"],
        "rating": 4.9,
        "review_count": 87,
        "bio": "15+ years experience in CNG/LNG system inspections. Former fleet maintenance director for major transit authority."
    },
    {
        "id": "inspector-002",
        "name": "Sarah Martinez",
        "company": "H2 Inspection Services",
        "phone": "(415) 555-8002",
        "email": "smartinez@h2inspect.com",
        "city": "San Francisco",
        "state": "CA",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "fuel_specializations": ["Hydrogen"],
        "certifications": ["Hydrogen Safety Inspector", "SAE J2601 Certified", "NFPA 2 Qualified"],
        "license_number": "CA-H2-2024-5678",
        "years_experience": 8,
        "service_area": ["San Francisco", "Oakland", "San Jose", "Sacramento"],
        "rating": 4.8,
        "review_count": 52,
        "bio": "Specialized in hydrogen fuel cell vehicle inspections. Background in aerospace fuel systems engineering."
    },
    {
        "id": "inspector-003",
        "name": "Michael Thompson",
        "company": "EV Compliance Experts",
        "phone": "(619) 555-8003",
        "email": "mthompson@evcomply.com",
        "city": "San Diego",
        "state": "CA",
        "latitude": 32.7157,
        "longitude": -117.1611,
        "fuel_specializations": ["Electric"],
        "certifications": ["High Voltage Certified", "NEC Article 625 Inspector", "UL Listed Equipment Specialist"],
        "license_number": "CA-EV-2024-9012",
        "years_experience": 10,
        "service_area": ["San Diego", "Imperial County", "Temecula"],
        "rating": 4.7,
        "review_count": 124,
        "bio": "Former electrical engineer specializing in EV charging infrastructure compliance and safety inspections."
    },
    {
        "id": "inspector-004",
        "name": "James Wilson",
        "company": "MultiFleet Inspections",
        "phone": "(303) 555-8004",
        "email": "jwilson@multifleet.com",
        "city": "Denver",
        "state": "CO",
        "latitude": 39.7392,
        "longitude": -104.9903,
        "fuel_specializations": ["CNG", "LNG", "Biodiesel"],
        "certifications": ["DOT Certified Inspector", "EPA Compliance Officer", "CARB Certified"],
        "license_number": "CO-AFL-2024-3456",
        "years_experience": 20,
        "service_area": ["Colorado", "Wyoming", "New Mexico"],
        "rating": 4.9,
        "review_count": 203,
        "bio": "20 years in alternative fuel compliance. Served on state regulatory boards. Expert in fleet compliance audits."
    },
    {
        "id": "inspector-005",
        "name": "Emily Davis",
        "company": "Texas Fuel Systems Inspection",
        "phone": "(713) 555-8005",
        "email": "edavis@txfuelinspect.com",
        "city": "Houston",
        "state": "TX",
        "latitude": 29.7604,
        "longitude": -95.3698,
        "fuel_specializations": ["CNG", "LNG", "Hydrogen"],
        "certifications": ["Texas Railroad Commission Certified", "NFPA 52 & NFPA 2 Qualified", "ASE Master"],
        "license_number": "TX-AFL-2024-7890",
        "years_experience": 12,
        "service_area": ["Houston", "Dallas", "Austin", "San Antonio"],
        "rating": 4.6,
        "review_count": 156,
        "bio": "Comprehensive alternative fuel inspector covering all major Texas markets. Bilingual English/Spanish."
    }
]

# ==================== API ENDPOINTS ====================

@api_router.get("/")
async def root():
    return {"message": "FuelPoint Navigator API", "version": "1.0.0"}

# Health check
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# ==================== FUEL STATIONS ====================

@api_router.get("/stations", response_model=List[FuelStation])
async def get_stations(
    fuel_type: Optional[str] = Query(None, description="Filter by fuel type"),
    state: Optional[str] = Query(None, description="Filter by state"),
    city: Optional[str] = Query(None, description="Filter by city"),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """Get all fuel stations with optional filters"""
    # Check if we have data in MongoDB
    count = await db.fuel_stations.count_documents({})
    
    if count == 0:
        # Seed with mock data
        for station in MOCK_STATIONS:
            station["last_updated"] = datetime.utcnow()
            await db.fuel_stations.insert_one(station)
    
    # Build query
    query = {}
    if fuel_type:
        query["fuel_types"] = fuel_type
    if state:
        query["state"] = state.upper()
    if city:
        query["city"] = {"$regex": city, "$options": "i"}
    if status:
        query["status"] = status
    
    stations = await db.fuel_stations.find(query).to_list(1000)
    return [FuelStation(**{**s, "id": s.get("id", str(s.get("_id")))}) for s in stations]

@api_router.get("/stations/{station_id}", response_model=FuelStation)
async def get_station(station_id: str):
    """Get a specific fuel station by ID"""
    station = await db.fuel_stations.find_one({"id": station_id})
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    return FuelStation(**{**station, "id": station.get("id", str(station.get("_id")))})

# ==================== REGULATIONS ====================

@api_router.get("/regulations", response_model=List[Regulation])
async def get_regulations(
    fuel_type: Optional[str] = Query(None, description="Filter by fuel type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction"),
    state: Optional[str] = Query(None, description="Filter by state")
):
    """Get all regulations with optional filters"""
    count = await db.regulations.count_documents({})
    
    if count == 0:
        for reg in MOCK_REGULATIONS:
            await db.regulations.insert_one(reg)
    
    query = {}
    if fuel_type:
        query["fuel_types"] = fuel_type
    if category:
        query["category"] = {"$regex": category, "$options": "i"}
    if jurisdiction:
        query["jurisdiction"] = jurisdiction
    if state:
        query["state"] = state.upper()
    
    regulations = await db.regulations.find(query).to_list(1000)
    return [Regulation(**{**r, "id": r.get("id", str(r.get("_id")))}) for r in regulations]

@api_router.get("/regulations/{regulation_id}", response_model=Regulation)
async def get_regulation(regulation_id: str):
    """Get a specific regulation by ID"""
    regulation = await db.regulations.find_one({"id": regulation_id})
    if not regulation:
        raise HTTPException(status_code=404, detail="Regulation not found")
    return Regulation(**{**regulation, "id": regulation.get("id", str(regulation.get("_id")))})

# ==================== SERVICE CENTERS ====================

@api_router.get("/service-centers", response_model=List[ServiceCenter])
async def get_service_centers(
    fuel_type: Optional[str] = Query(None, description="Filter by fuel specialization"),
    service_type: Optional[str] = Query(None, description="Filter by service type"),
    state: Optional[str] = Query(None, description="Filter by state"),
    city: Optional[str] = Query(None, description="Filter by city")
):
    """Get all service centers with optional filters"""
    count = await db.service_centers.count_documents({})
    
    if count == 0:
        for center in MOCK_SERVICE_CENTERS:
            await db.service_centers.insert_one(center)
    
    query = {}
    if fuel_type:
        query["fuel_specializations"] = fuel_type
    if service_type:
        query["service_type"] = service_type
    if state:
        query["state"] = state.upper()
    if city:
        query["city"] = {"$regex": city, "$options": "i"}
    
    centers = await db.service_centers.find(query).to_list(1000)
    return [ServiceCenter(**{**c, "id": c.get("id", str(c.get("_id")))}) for c in centers]

@api_router.get("/service-centers/{center_id}", response_model=ServiceCenter)
async def get_service_center(center_id: str):
    """Get a specific service center by ID"""
    center = await db.service_centers.find_one({"id": center_id})
    if not center:
        raise HTTPException(status_code=404, detail="Service center not found")
    return ServiceCenter(**{**center, "id": center.get("id", str(center.get("_id")))})

# ==================== INSPECTORS ====================

@api_router.get("/inspectors", response_model=List[Inspector])
async def get_inspectors(
    fuel_type: Optional[str] = Query(None, description="Filter by fuel specialization"),
    state: Optional[str] = Query(None, description="Filter by state"),
    city: Optional[str] = Query(None, description="Filter by city")
):
    """Get all inspectors with optional filters"""
    count = await db.inspectors.count_documents({})
    
    if count == 0:
        for inspector in MOCK_INSPECTORS:
            await db.inspectors.insert_one(inspector)
    
    query = {}
    if fuel_type:
        query["fuel_specializations"] = fuel_type
    if state:
        query["state"] = state.upper()
    if city:
        query["city"] = {"$regex": city, "$options": "i"}
    
    inspectors = await db.inspectors.find(query).to_list(1000)
    return [Inspector(**{**i, "id": i.get("id", str(i.get("_id")))}) for i in inspectors]

@api_router.get("/inspectors/{inspector_id}", response_model=Inspector)
async def get_inspector(inspector_id: str):
    """Get a specific inspector by ID"""
    inspector = await db.inspectors.find_one({"id": inspector_id})
    if not inspector:
        raise HTTPException(status_code=404, detail="Inspector not found")
    return Inspector(**{**inspector, "id": inspector.get("id", str(inspector.get("_id")))})

# ==================== USER PROFILE ====================

@api_router.get("/profile", response_model=UserProfile)
async def get_profile():
    """Get user profile (uses device-based storage in MVP)"""
    profile = await db.user_profiles.find_one({"id": "default-user"})
    if not profile:
        # Create default profile
        default_profile = UserProfile(id="default-user")
        await db.user_profiles.insert_one(default_profile.dict())
        return default_profile
    return UserProfile(**profile)

@api_router.put("/profile", response_model=UserProfile)
async def update_profile(update: UserProfileUpdate):
    """Update user profile"""
    profile = await db.user_profiles.find_one({"id": "default-user"})
    if not profile:
        profile = UserProfile(id="default-user").dict()
    
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    if update_data:
        await db.user_profiles.update_one(
            {"id": "default-user"},
            {"$set": update_data},
            upsert=True
        )
    
    updated_profile = await db.user_profiles.find_one({"id": "default-user"})
    return UserProfile(**updated_profile)

@api_router.post("/profile/favorites/{station_id}")
async def add_favorite_station(station_id: str):
    """Add a station to favorites"""
    await db.user_profiles.update_one(
        {"id": "default-user"},
        {"$addToSet": {"favorite_stations": station_id}},
        upsert=True
    )
    return {"message": "Station added to favorites"}

@api_router.delete("/profile/favorites/{station_id}")
async def remove_favorite_station(station_id: str):
    """Remove a station from favorites"""
    await db.user_profiles.update_one(
        {"id": "default-user"},
        {"$pull": {"favorite_stations": station_id}}
    )
    return {"message": "Station removed from favorites"}

# ==================== FUEL TYPES ====================

@api_router.get("/fuel-types")
async def get_fuel_types():
    """Get all available fuel types"""
    return [
        {"id": "CNG", "name": "Compressed Natural Gas", "icon": "gas-cylinder"},
        {"id": "LNG", "name": "Liquefied Natural Gas", "icon": "gas-cylinder"},
        {"id": "Hydrogen", "name": "Hydrogen", "icon": "molecule-h2o"},
        {"id": "Electric", "name": "Electric (EV)", "icon": "ev-plug-type1"},
        {"id": "Diesel", "name": "Diesel", "icon": "gas-station"},
        {"id": "Gasoline", "name": "Gasoline", "icon": "gas-station"},
        {"id": "Biodiesel", "name": "Biodiesel", "icon": "leaf"}
    ]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
