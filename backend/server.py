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
import httpx

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# AFDC/NREL API Configuration
NREL_API_KEY = os.environ.get('NREL_API_KEY', '')
NREL_BASE_URL = "https://developer.nrel.gov/api/alt-fuel-stations/v1"

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
    ETHANOL = "E85"
    PROPANE = "LPG"

class ServiceType(str, Enum):
    MOBILE = "Mobile"
    IN_SHOP = "In-Shop"
    BOTH = "Both"

# AFDC Fuel Type Code Mapping
AFDC_FUEL_CODES = {
    "ELEC": "Electric",
    "CNG": "CNG",
    "LNG": "LNG",
    "HY": "Hydrogen",
    "BD": "Biodiesel",
    "E85": "E85",
    "LPG": "LPG",
    "RD": "Biodiesel"  # Renewable Diesel maps to Biodiesel
}

# Reverse mapping for API queries
FUEL_TO_AFDC = {
    "Electric": "ELEC",
    "CNG": "CNG",
    "LNG": "LNG",
    "Hydrogen": "HY",
    "Biodiesel": "BD",
    "E85": "E85",
    "LPG": "LPG"
}

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
    fuel_types: List[str]
    phone: Optional[str] = None
    hours: Optional[str] = None
    amenities: List[str] = []
    card_accepted: List[str] = []
    last_updated: Optional[datetime] = None
    status: str = "Operational"
    prices: Optional[dict] = None
    network: Optional[str] = None
    access_type: Optional[str] = None
    ev_connector_types: Optional[List[str]] = None
    ev_network: Optional[str] = None

# Regulation Models
class Regulation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    fuel_types: List[str]
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
    fuel_specializations: List[str]
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
    fuel_specializations: List[str]
    certifications: List[str] = []
    license_number: Optional[str] = None
    years_experience: int = 0
    service_area: List[str] = []  # List of cities/regions covered
    rating: float = 0.0
    review_count: int = 0
    bio: Optional[str] = None

# Fuel System Provider Models
class FuelSystemProvider(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    logo_url: Optional[str] = None
    description: str
    fuel_types: List[str]
    website: str
    support_url: Optional[str] = None
    documentation_url: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    headquarters: Optional[str] = None
    products: List[str] = []
    formerly_known_as: Optional[str] = None

# User Profile Models
class UserProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Guest User"
    email: Optional[str] = None
    phone: Optional[str] = None
    preferred_fuel_types: List[str] = []
    favorite_stations: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    preferred_fuel_types: Optional[List[str]] = None

# ==================== FUEL SYSTEM PROVIDERS DATA ====================

FUEL_SYSTEM_PROVIDERS = [
    {
        "id": "provider-001",
        "name": "Hexagon Agility",
        "description": "Leading provider of clean fuel solutions including CNG, RNG, and hydrogen fuel systems for commercial vehicles.",
        "fuel_types": ["CNG", "LNG", "Hydrogen"],
        "website": "https://hexagonagility.com",
        "support_url": "https://hexagonagility.com/support",
        "documentation_url": "https://hexagonagility.com/resources",
        "phone": "+1 (402) 434-2345",
        "headquarters": "Lincoln, Nebraska, USA",
        "products": ["CNG Fuel Systems", "Type 4 Cylinders", "LNG Systems", "Hydrogen Storage"]
    },
    {
        "id": "provider-002",
        "name": "Cummins Clean Fuel Technologies",
        "formerly_known_as": "Momentum Fuel Technologies",
        "description": "Comprehensive natural gas fuel system solutions for heavy-duty trucking and transit applications.",
        "fuel_types": ["CNG", "LNG"],
        "website": "https://www.cummins.com/parts-and-service/fuel-systems",
        "support_url": "https://www.cummins.com/support",
        "documentation_url": "https://www.cummins.com/parts-and-service/digital-products-and-services",
        "phone": "+1 (800) 343-7357",
        "headquarters": "Columbus, Indiana, USA",
        "products": ["CNG Fuel Systems", "LNG Systems", "Fuel Storage", "Fuel Delivery Systems"]
    },
    {
        "id": "provider-003",
        "name": "Mainstay Fuel Technologies",
        "description": "Manufacturer of CNG and propane fuel systems for light and medium-duty vehicles.",
        "fuel_types": ["CNG", "LPG"],
        "website": "https://mainstayfuel.com",
        "support_url": "https://mainstayfuel.com/support",
        "phone": "+1 (817) 295-0554",
        "headquarters": "Burleson, Texas, USA",
        "products": ["CNG Bi-Fuel Systems", "Propane Systems", "Fuel Injectors", "Regulators"]
    },
    {
        "id": "provider-004",
        "name": "A-1 Alternative Fuel Systems",
        "description": "Provider of alternative fuel conversion systems and components for fleet and commercial vehicles.",
        "fuel_types": ["CNG", "LPG"],
        "website": "https://a1altfuelsystems.com",
        "support_url": "https://a1altfuelsystems.com/technical-support",
        "phone": "+1 (800) 466-0776",
        "headquarters": "Oklahoma City, Oklahoma, USA",
        "products": ["CNG Conversion Kits", "Propane Systems", "Fuel Management", "Training Services"]
    },
    {
        "id": "provider-005",
        "name": "American CNG",
        "description": "Specialized in CNG fuel system conversions and installations for light, medium, and heavy-duty vehicles.",
        "fuel_types": ["CNG"],
        "website": "https://americancng.com",
        "support_url": "https://americancng.com/support",
        "documentation_url": "https://americancng.com/resources",
        "phone": "+1 (801) 975-1970",
        "headquarters": "Salt Lake City, Utah, USA",
        "products": ["EPA Certified CNG Systems", "Vehicle Conversions", "Fleet Solutions"]
    },
    {
        "id": "provider-006",
        "name": "Heil Trailer International",
        "description": "Manufacturer of tank trailers for petroleum, chemical, food, and alternative fuel transportation.",
        "fuel_types": ["CNG", "LNG", "LPG"],
        "website": "https://www.heiltrailer.com",
        "support_url": "https://www.heiltrailer.com/service-support",
        "phone": "+1 (423) 899-9100",
        "headquarters": "Chattanooga, Tennessee, USA",
        "products": ["LNG Transport Trailers", "CNG Tube Trailers", "Propane Transport"]
    },
    {
        "id": "provider-007",
        "name": "McNeilus Truck and Manufacturing",
        "description": "Leading manufacturer of refuse collection vehicles and concrete mixers with alternative fuel options.",
        "fuel_types": ["CNG", "LNG"],
        "website": "https://www.mcneiluscompanies.com",
        "support_url": "https://www.mcneiluscompanies.com/support",
        "phone": "+1 (507) 374-6321",
        "headquarters": "Dodge Center, Minnesota, USA",
        "products": ["CNG Refuse Trucks", "Alternative Fuel Ready Chassis", "Hybrid Systems"]
    },
    {
        "id": "provider-008",
        "name": "Westport Fuel Systems",
        "description": "Global leader in alternative fuel systems and components for transportation applications.",
        "fuel_types": ["CNG", "LNG", "Hydrogen"],
        "website": "https://www.westport.com",
        "support_url": "https://www.westport.com/support",
        "documentation_url": "https://www.westport.com/resources",
        "phone": "+1 (604) 718-2000",
        "headquarters": "Vancouver, British Columbia, Canada",
        "products": ["HPDI Fuel Systems", "CNG Components", "LNG Systems", "Hydrogen Engines"]
    },
    {
        "id": "provider-009",
        "name": "Quantum Fuel Systems",
        "description": "Advanced clean energy storage and fuel system technologies for transportation and industrial applications.",
        "fuel_types": ["CNG", "Hydrogen"],
        "website": "https://www.qtww.com",
        "support_url": "https://www.qtww.com/contact",
        "phone": "+1 (949) 399-4500",
        "headquarters": "Lake Forest, California, USA",
        "products": ["Type 4 CNG Tanks", "Hydrogen Storage Systems", "Virtual Pipelines"]
    },
    {
        "id": "provider-010",
        "name": "Optimus Technologies",
        "description": "Provider of advanced biodiesel fuel systems enabling vehicles to run on 100% biodiesel (B100).",
        "fuel_types": ["Biodiesel"],
        "website": "https://optimustec.com",
        "support_url": "https://optimustec.com/support",
        "documentation_url": "https://optimustec.com/resources",
        "phone": "+1 (412) 345-8734",
        "headquarters": "Pittsburgh, Pennsylvania, USA",
        "products": ["Vector System", "B100 Fuel Systems", "Fleet Management Software"]
    },
    {
        "id": "provider-011",
        "name": "Agility Fuel Solutions",
        "description": "Natural gas fuel systems and cylinders for medium and heavy-duty commercial vehicles.",
        "fuel_types": ["CNG", "LNG", "Hydrogen"],
        "website": "https://www.agilityfuelsolutions.com",
        "support_url": "https://www.agilityfuelsolutions.com/support",
        "phone": "+1 (714) 816-7800",
        "headquarters": "Costa Mesa, California, USA",
        "products": ["PowerCube Systems", "CNG Cylinders", "LNG Fuel Systems"]
    },
    {
        "id": "provider-012",
        "name": "IMPCO Automotive",
        "description": "Global manufacturer of alternative fuel systems and components for automotive applications.",
        "fuel_types": ["CNG", "LPG"],
        "website": "https://www.impco.com",
        "support_url": "https://www.impco.com/support",
        "documentation_url": "https://www.impco.com/technical-library",
        "phone": "+1 (714) 656-1200",
        "headquarters": "Cerritos, California, USA",
        "products": ["Fuel Injection Systems", "Regulators", "Fuel Rails", "Electronic Controls"]
    },
    {
        "id": "provider-013",
        "name": "Clean Energy Fuels",
        "description": "Largest provider of natural gas fuel for transportation in North America with extensive fueling network.",
        "fuel_types": ["CNG", "LNG"],
        "website": "https://www.cleanenergyfuels.com",
        "support_url": "https://www.cleanenergyfuels.com/contact",
        "documentation_url": "https://www.cleanenergyfuels.com/resources",
        "phone": "+1 (949) 437-1000",
        "headquarters": "Newport Beach, California, USA",
        "products": ["Redeem RNG Fuel", "Zero Now Financing", "Station Development"]
    },
    {
        "id": "provider-014",
        "name": "Worthington Industries",
        "description": "Manufacturer of pressure cylinders and CNG storage solutions for vehicles and stationary applications.",
        "fuel_types": ["CNG", "Hydrogen"],
        "website": "https://worthingtonindustries.com",
        "support_url": "https://worthingtonindustries.com/support",
        "phone": "+1 (614) 438-3210",
        "headquarters": "Columbus, Ohio, USA",
        "products": ["CNG Cylinders", "Hydrogen Storage", "Industrial Gas Equipment"]
    },
    {
        "id": "provider-015",
        "name": "Chart Industries",
        "description": "Global manufacturer of cryogenic equipment for LNG and hydrogen storage and distribution.",
        "fuel_types": ["LNG", "Hydrogen"],
        "website": "https://www.chartindustries.com",
        "support_url": "https://www.chartindustries.com/Support",
        "phone": "+1 (770) 721-8800",
        "headquarters": "Ball Ground, Georgia, USA",
        "products": ["LNG Vehicle Tanks", "Hydrogen Storage", "Cryogenic Trailers", "Fueling Equipment"]
    }
]

# ==================== MOCK DATA (Fallback) ====================

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
        "fuel_types": ["Biodiesel", "CNG", "LNG", "E85"],
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
        "fuel_types": ["CNG", "LNG", "Hydrogen", "Electric", "LPG"],
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

# ==================== AFDC API HELPER FUNCTIONS ====================

async def fetch_afdc_stations(
    fuel_type: Optional[str] = None,
    state: Optional[str] = None,
    city: Optional[str] = None,
    zip_code: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius: Optional[float] = None,
    limit: int = 100
) -> List[dict]:
    """Fetch stations from AFDC API"""
    
    if not NREL_API_KEY:
        logger.warning("NREL_API_KEY not set, returning empty list")
        return []
    
    params = {
        "api_key": NREL_API_KEY,
        "status": "E",  # E = Open stations
        "access": "public",
        "limit": limit,
        "format": "json"
    }
    
    # Convert fuel type to AFDC code
    if fuel_type and fuel_type in FUEL_TO_AFDC:
        params["fuel_type"] = FUEL_TO_AFDC[fuel_type]
    elif fuel_type:
        # If no specific mapping, try common codes
        params["fuel_type"] = fuel_type
    
    if state:
        params["state"] = state.upper()
    
    if city:
        params["city"] = city
    
    if zip_code:
        params["zip"] = zip_code
    
    # Location-based search
    if latitude and longitude:
        params["latitude"] = latitude
        params["longitude"] = longitude
        if radius:
            params["radius"] = radius
        else:
            params["radius"] = 50  # Default 50 miles
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{NREL_BASE_URL}.json", params=params)
            response.raise_for_status()
            data = response.json()
            
            stations = data.get("fuel_stations", [])
            logger.info(f"AFDC API returned {len(stations)} stations")
            return stations
    except httpx.HTTPError as e:
        logger.error(f"AFDC API error: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching AFDC data: {e}")
        return []

def transform_afdc_station(afdc_station: dict) -> dict:
    """Transform AFDC station data to our FuelStation format"""
    
    # Map AFDC fuel type code to our format
    fuel_code = afdc_station.get("fuel_type_code", "")
    fuel_type = AFDC_FUEL_CODES.get(fuel_code, fuel_code)
    
    # Determine status
    status_code = afdc_station.get("status_code", "E")
    status_map = {
        "E": "Operational",
        "P": "Planned",
        "T": "Temporarily Unavailable"
    }
    status = status_map.get(status_code, "Unknown")
    
    # Build amenities list
    amenities = []
    if afdc_station.get("facility_type"):
        amenities.append(afdc_station["facility_type"])
    if afdc_station.get("cards_accepted"):
        pass  # Handled separately
    
    # Build card_accepted list
    cards = []
    cards_str = afdc_station.get("cards_accepted", "")
    if cards_str:
        cards = [c.strip() for c in cards_str.split(",") if c.strip()]
    
    # EV-specific fields
    ev_connectors = []
    if fuel_code == "ELEC":
        connector_types = afdc_station.get("ev_connector_types", [])
        if connector_types:
            ev_connectors = connector_types
    
    return {
        "id": f"afdc-{afdc_station.get('id', '')}",
        "name": afdc_station.get("station_name", "Unknown Station"),
        "address": afdc_station.get("street_address", ""),
        "city": afdc_station.get("city", ""),
        "state": afdc_station.get("state", ""),
        "zip_code": afdc_station.get("zip", ""),
        "latitude": afdc_station.get("latitude", 0),
        "longitude": afdc_station.get("longitude", 0),
        "fuel_types": [fuel_type] if fuel_type else [],
        "phone": afdc_station.get("station_phone"),
        "hours": afdc_station.get("access_days_time"),
        "amenities": amenities,
        "card_accepted": cards,
        "status": status,
        "network": afdc_station.get("ev_network"),
        "access_type": afdc_station.get("access_code"),
        "ev_connector_types": ev_connectors if ev_connectors else None,
        "ev_network": afdc_station.get("ev_network")
    }

# ==================== API ENDPOINTS ====================

@api_router.get("/")
async def root():
    return {"message": "FuelPoint Navigator API", "version": "2.0.0", "data_source": "AFDC/NREL"}

# Health check
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat(), "afdc_enabled": bool(NREL_API_KEY)}

# ==================== FUEL STATIONS (AFDC Integration) ====================

@api_router.get("/stations", response_model=List[FuelStation])
async def get_stations(
    fuel_type: Optional[str] = Query(None, description="Filter by fuel type (Electric, CNG, LNG, Hydrogen, Biodiesel, E85, LPG)"),
    state: Optional[str] = Query(None, description="Filter by state (2-letter code)"),
    city: Optional[str] = Query(None, description="Filter by city"),
    zip_code: Optional[str] = Query(None, description="Filter by ZIP code"),
    latitude: Optional[float] = Query(None, description="Latitude for location-based search"),
    longitude: Optional[float] = Query(None, description="Longitude for location-based search"),
    radius: Optional[float] = Query(None, description="Search radius in miles (default: 50)"),
    limit: int = Query(100, description="Maximum number of results", le=500)
):
    """Get fuel stations from AFDC API with optional filters"""
    
    # Fetch from AFDC API
    afdc_stations = await fetch_afdc_stations(
        fuel_type=fuel_type,
        state=state,
        city=city,
        zip_code=zip_code,
        latitude=latitude,
        longitude=longitude,
        radius=radius,
        limit=limit
    )
    
    if afdc_stations:
        # Transform AFDC data to our format
        stations = [transform_afdc_station(s) for s in afdc_stations]
        return [FuelStation(**s) for s in stations]
    
    # Fallback: Return message that API key may be missing
    logger.warning("No stations returned from AFDC API, check API key")
    return []

@api_router.get("/stations/nearby")
async def get_nearby_stations(
    latitude: float = Query(..., description="User's latitude"),
    longitude: float = Query(..., description="User's longitude"),
    radius: float = Query(25, description="Search radius in miles"),
    fuel_type: Optional[str] = Query(None, description="Filter by fuel type"),
    limit: int = Query(50, le=200)
):
    """Get stations near a specific location"""
    
    afdc_stations = await fetch_afdc_stations(
        fuel_type=fuel_type,
        latitude=latitude,
        longitude=longitude,
        radius=radius,
        limit=limit
    )
    
    if afdc_stations:
        stations = [transform_afdc_station(s) for s in afdc_stations]
        return [FuelStation(**s) for s in stations]
    
    return []

@api_router.get("/stations/{station_id}", response_model=FuelStation)
async def get_station(station_id: str):
    """Get a specific fuel station by ID"""
    
    # For AFDC stations, fetch directly from API
    if station_id.startswith("afdc-"):
        afdc_id = station_id.replace("afdc-", "")
        
        if not NREL_API_KEY:
            raise HTTPException(status_code=503, detail="AFDC API not configured")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{NREL_BASE_URL}/{afdc_id}.json",
                    params={"api_key": NREL_API_KEY}
                )
                response.raise_for_status()
                data = response.json()
                
                if "alt_fuel_station" in data:
                    station = transform_afdc_station(data["alt_fuel_station"])
                    return FuelStation(**station)
        except httpx.HTTPError as e:
            logger.error(f"Error fetching station {station_id}: {e}")
            raise HTTPException(status_code=404, detail="Station not found")
    
    raise HTTPException(status_code=404, detail="Station not found")

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

# ==================== INSPECTOR LOOKUP LINKS ====================

@api_router.get("/inspector-lookup-links")
async def get_inspector_lookup_links():
    """Get external links for certified inspector lookups"""
    return {
        "afvi": {
            "name": "AFVi Certified Inspectors",
            "description": "Alternative Fuel Vehicle Institute - Search for certified CNG, LNG, and hydrogen fuel system inspectors",
            "url": "https://afvi.com/certification/certified-inspectors/",
            "certifications": ["CNG Inspector", "LNG Inspector", "Hydrogen Inspector"]
        },
        "csa": {
            "name": "CSA Group Qualified Personnel",
            "description": "CSA Group - Search for qualified personnel certified in fuel system standards",
            "url": "https://www.csagroup.org/search-qualified-personnel/",
            "certifications": ["CSA Certified", "NGV Inspector", "Fuel System Specialist"]
        }
    }

# ==================== FUEL SYSTEM PROVIDERS ====================

@api_router.get("/providers", response_model=List[FuelSystemProvider])
async def get_providers(
    fuel_type: Optional[str] = Query(None, description="Filter by fuel type"),
    search: Optional[str] = Query(None, description="Search by name or description")
):
    """Get all fuel system providers with optional filters"""
    
    providers = FUEL_SYSTEM_PROVIDERS
    
    if fuel_type:
        providers = [p for p in providers if fuel_type in p.get("fuel_types", [])]
    
    if search:
        search_lower = search.lower()
        providers = [
            p for p in providers 
            if search_lower in p.get("name", "").lower() 
            or search_lower in p.get("description", "").lower()
            or (p.get("formerly_known_as") and search_lower in p["formerly_known_as"].lower())
        ]
    
    return [FuelSystemProvider(**p) for p in providers]

@api_router.get("/providers/{provider_id}", response_model=FuelSystemProvider)
async def get_provider(provider_id: str):
    """Get a specific fuel system provider by ID"""
    
    for provider in FUEL_SYSTEM_PROVIDERS:
        if provider["id"] == provider_id:
            return FuelSystemProvider(**provider)
    
    raise HTTPException(status_code=404, detail="Provider not found")

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
        {"id": "Electric", "name": "Electric (EV)", "icon": "flash", "afdc_code": "ELEC"},
        {"id": "CNG", "name": "Compressed Natural Gas", "icon": "gas-cylinder", "afdc_code": "CNG"},
        {"id": "LNG", "name": "Liquefied Natural Gas", "icon": "snowflake", "afdc_code": "LNG"},
        {"id": "Hydrogen", "name": "Hydrogen", "icon": "atom", "afdc_code": "HY"},
        {"id": "Biodiesel", "name": "Biodiesel", "icon": "leaf", "afdc_code": "BD"},
        {"id": "E85", "name": "Ethanol (E85)", "icon": "water", "afdc_code": "E85"},
        {"id": "LPG", "name": "Propane (LPG)", "icon": "flame", "afdc_code": "LPG"}
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
