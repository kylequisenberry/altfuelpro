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
    status: Optional[str] = None  # "active", "discontinued", etc.
    locations: Optional[dict] = None  # Additional location details

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

# Support/Feedback Models
class FeedbackType(str, Enum):
    SUGGESTION = "suggestion"
    SUPPORT = "support"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    GENERAL = "general"

class Feedback(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: FeedbackType
    subject: str
    message: str
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    app_version: str = "1.0.0"
    platform: Optional[str] = None  # ios, android, web
    status: str = "new"  # new, in_progress, resolved, closed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class FeedbackCreate(BaseModel):
    type: FeedbackType
    subject: str
    message: str
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    platform: Optional[str] = None

# ==================== FUEL SYSTEM PROVIDERS DATA ====================

FUEL_SYSTEM_PROVIDERS = [
    {
        "id": "provider-001",
        "name": "Hexagon Agility",
        "description": "Leading provider of CNG/RNG fuel systems, FleetCare services, and system installation for commercial vehicles. US Corporate headquarters in Salisbury, NC.",
        "fuel_types": ["CNG"],
        "website": "https://hexagonagility.com",
        "support_url": "https://hexagonagility.com/support",
        "documentation_url": "https://hexagonagility.com/resources",
        "phone": "+1 (704) 633-2553",
        "headquarters": "1010 Corporate Center Drive, Salisbury, NC 28146, USA",
        "products": ["CNG/RNG Fuel Systems", "FleetCare Services", "System Installation", "Vehicle Integration"],
        "locations": {
            "us_corporate": "1010 Corporate Center Drive, Salisbury, NC 28146, USA",
            "fleetcare_installation": "4995 S Main St, Salisbury, NC 28147, USA"
        }
    },
    {
        "id": "provider-001b",
        "name": "Hexagon Purus",
        "description": "Mobile Pipeline and Type 4 cylinder manufacturing facility. Specializes in hydrogen storage systems and composite pressure vessels for clean energy applications.",
        "fuel_types": ["CNG", "Hydrogen"],
        "website": "https://hexagonpurus.com",
        "support_url": "https://hexagonpurus.com/support",
        "documentation_url": "https://hexagonpurus.com/resources",
        "phone": "+1 (402) 434-2345",
        "headquarters": "Lincoln, Nebraska, USA",
        "products": ["Mobile Pipeline Systems", "Type 4 Cylinders", "Hydrogen Storage", "Composite Pressure Vessels"]
    },
    {
        "id": "provider-002",
        "name": "Cummins Clean Fuel Technologies",
        "formerly_known_as": "Momentum Fuel Technologies",
        "description": "Comprehensive CNG and RNG fuel system solutions for heavy-duty trucking and transit applications. Specializes in natural gas fuel systems only.",
        "fuel_types": ["CNG"],
        "website": "https://www.cumminscleantech.com",
        "support_url": "https://www.cumminscleantech.com/support",
        "documentation_url": "https://www.cumminscleantech.com/resources",
        "headquarters": "Roanoke, Texas, USA",
        "products": ["CNG Fuel Systems", "RNG Systems", "Fuel Storage", "Fuel Delivery Systems"]
    },
    {
        "id": "provider-003",
        "name": "Mainstay Fuel Technologies",
        "formerly_known_as": "Piedmont, SC Operations",
        "description": "DISCONTINUED - Formerly manufactured CNG and propane fuel systems for light and medium-duty vehicles. Company is no longer in business, but legacy systems remain in the field with limited documentation available.",
        "fuel_types": ["CNG", "LPG"],
        "website": "https://mainstayfuel.com",
        "headquarters": "Piedmont, South Carolina, USA (CLOSED)",
        "products": ["CNG Bi-Fuel Systems (Legacy)", "Propane Systems (Legacy)", "Fuel Injectors (Legacy)", "Regulators (Legacy)"],
        "status": "discontinued"
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
        "name": "Heil Environmental",
        "description": "Manufacturer of refuse and recycling collection vehicle bodies. Part of Environmental Solutions Group. Contact through heil.com directory for locations and service.",
        "fuel_types": ["CNG"],
        "website": "https://www.heil.com",
        "support_url": "https://www.heil.com/contact",
        "documentation_url": "https://www.heil.com/resources",
        "headquarters": "Fort Payne, Alabama, USA",
        "products": ["CNG Refuse Bodies", "Alternative Fuel Ready Equipment", "Recycling Collection Vehicles"]
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
    # ==================== RUSH TRUCK CENTERS ====================
    {
        "id": "rush-001",
        "name": "Rush Truck Centers - Dallas",
        "address": "4455 Lyndon B Johnson Fwy",
        "city": "Dallas",
        "state": "TX",
        "zip_code": "75244",
        "latitude": 32.9251,
        "longitude": -96.8234,
        "phone": "(972) 387-1200",
        "website": "https://www.rushtruckcenters.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["Peterbilt Certified", "CNG Specialist", "Cummins Authorized"],
        "rating": 4.6,
        "review_count": 234,
        "hours": "Mon-Fri 7AM-6PM, Sat 8AM-12PM",
        "services_offered": ["CNG System Repair", "Tank Inspection", "Engine Service", "Fleet Maintenance"]
    },
    {
        "id": "rush-002",
        "name": "Rush Truck Centers - Houston",
        "address": "15455 North Freeway",
        "city": "Houston",
        "state": "TX",
        "zip_code": "77090",
        "latitude": 29.9561,
        "longitude": -95.4183,
        "phone": "(281) 931-9700",
        "website": "https://www.rushtruckcenters.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["Peterbilt Certified", "Natural Gas Specialist", "ASE Certified"],
        "rating": 4.7,
        "review_count": 312,
        "hours": "Mon-Fri 7AM-6PM, Sat 8AM-12PM",
        "services_offered": ["Natural Gas Engine Service", "CNG Fuel System Repair", "DOT Inspections"]
    },
    {
        "id": "rush-003",
        "name": "Rush Truck Centers - San Antonio",
        "address": "6455 IH-10 West",
        "city": "San Antonio",
        "state": "TX",
        "zip_code": "78201",
        "latitude": 29.4750,
        "longitude": -98.5645,
        "phone": "(210) 736-2100",
        "website": "https://www.rushtruckcenters.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["Peterbilt Platinum", "CNG Certified", "Fleet Solutions"],
        "rating": 4.5,
        "review_count": 189,
        "hours": "Mon-Fri 7AM-6PM, Sat 8AM-12PM",
        "services_offered": ["CNG Repairs", "Preventive Maintenance", "Parts Sales"]
    },
    {
        "id": "rush-004",
        "name": "Rush Truck Centers - Phoenix",
        "address": "550 N 75th Ave",
        "city": "Phoenix",
        "state": "AZ",
        "zip_code": "85043",
        "latitude": 33.4412,
        "longitude": -112.2159,
        "phone": "(623) 936-4500",
        "website": "https://www.rushtruckcenters.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["Natural Gas Certified", "Peterbilt Dealer"],
        "rating": 4.4,
        "review_count": 156,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Service", "Fleet Maintenance", "Parts & Accessories"]
    },
    {
        "id": "rush-005",
        "name": "Rush Truck Centers - Orlando",
        "address": "5410 L.B. McLeod Rd",
        "city": "Orlando",
        "state": "FL",
        "zip_code": "32811",
        "latitude": 28.4932,
        "longitude": -81.4437,
        "phone": "(407) 425-4561",
        "website": "https://www.rushtruckcenters.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["CNG Specialist", "Peterbilt Certified"],
        "rating": 4.5,
        "review_count": 145,
        "hours": "Mon-Fri 7AM-6PM",
        "services_offered": ["CNG Repair", "Fuel System Service", "Fleet Support"]
    },
    {
        "id": "rush-006",
        "name": "Rush Truck Centers - Denver",
        "address": "5301 Oswego St",
        "city": "Denver",
        "state": "CO",
        "zip_code": "80239",
        "latitude": 39.7849,
        "longitude": -104.8372,
        "phone": "(303) 375-5000",
        "website": "https://www.rushtruckcenters.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["Natural Gas Certified", "Cummins Authorized"],
        "rating": 4.6,
        "review_count": 178,
        "hours": "Mon-Fri 7AM-6PM, Sat 8AM-12PM",
        "services_offered": ["CNG/LNG Service", "Engine Repair", "Tank Inspection"]
    },
    # ==================== CUMMINS SALES & SERVICE ====================
    {
        "id": "cummins-001",
        "name": "Cummins Sales and Service - Dallas",
        "address": "9225 N Stemmons Fwy",
        "city": "Dallas",
        "state": "TX",
        "zip_code": "75247",
        "latitude": 32.8524,
        "longitude": -96.8831,
        "phone": "(214) 630-8585",
        "website": "https://www.cummins.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["Cummins Certified", "Natural Gas Specialist", "OEM Authorized"],
        "rating": 4.8,
        "review_count": 267,
        "hours": "Mon-Fri 7AM-6PM, Sat 8AM-12PM",
        "services_offered": ["Natural Gas Engine Service", "CNG System Repair", "Parts Sales", "Technical Training"]
    },
    {
        "id": "cummins-002",
        "name": "Cummins Sales and Service - Houston",
        "address": "8350 Mosley Rd",
        "city": "Houston",
        "state": "TX",
        "zip_code": "77075",
        "latitude": 29.6186,
        "longitude": -95.2542,
        "phone": "(713) 943-7800",
        "website": "https://www.cummins.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "Both",
        "certifications": ["Cummins Master Certified", "X15N Specialist"],
        "rating": 4.9,
        "review_count": 345,
        "hours": "24/7 Available",
        "services_offered": ["Natural Gas Engine Service", "Emergency Repair", "Fleet Maintenance", "Mobile Service"]
    },
    {
        "id": "cummins-003",
        "name": "Cummins Sales and Service - Los Angeles",
        "address": "10855 Sutter Ave",
        "city": "Pacoima",
        "state": "CA",
        "zip_code": "91331",
        "latitude": 34.2715,
        "longitude": -118.4125,
        "phone": "(818) 897-4611",
        "website": "https://www.cummins.com",
        "fuel_specializations": ["CNG", "LNG", "Hydrogen"],
        "service_type": "In-Shop",
        "certifications": ["Cummins Certified", "CARB Compliant", "Zero Emission Ready"],
        "rating": 4.7,
        "review_count": 289,
        "hours": "Mon-Fri 6AM-6PM",
        "services_offered": ["Natural Gas Service", "Emissions Compliance", "Engine Overhaul"]
    },
    {
        "id": "cummins-004",
        "name": "Cummins Sales and Service - Atlanta",
        "address": "1755 Enterprise Way SE",
        "city": "Marietta",
        "state": "GA",
        "zip_code": "30067",
        "latitude": 33.9125,
        "longitude": -84.4975,
        "phone": "(770) 423-9000",
        "website": "https://www.cummins.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Cummins Authorized", "Natural Gas Certified"],
        "rating": 4.6,
        "review_count": 198,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Engine Service", "Parts & Service", "Fleet Support"]
    },
    {
        "id": "cummins-005",
        "name": "Cummins Sales and Service - Chicago",
        "address": "500 W North Ave",
        "city": "Melrose Park",
        "state": "IL",
        "zip_code": "60160",
        "latitude": 41.9012,
        "longitude": -87.8567,
        "phone": "(708) 345-0011",
        "website": "https://www.cummins.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["Cummins Master Tech", "Natural Gas Specialist"],
        "rating": 4.5,
        "review_count": 167,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["Natural Gas Engine Repair", "Parts Sales", "Warranty Service"]
    },
    # ==================== MHC KENWORTH ====================
    {
        "id": "mhc-001",
        "name": "MHC Kenworth - RoadReady Center Chillicothe",
        "address": "3301 N Washington St",
        "city": "Chillicothe",
        "state": "MO",
        "zip_code": "64601",
        "latitude": 39.8175,
        "longitude": -93.5495,
        "phone": "(660) 646-0100",
        "website": "https://mhc.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["Agility Certified Installer", "Trilogy Authorized", "CNG Specialist"],
        "rating": 4.8,
        "review_count": 156,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG/LNG Installation", "Tank Installation", "System Testing", "Pre-Delivery Service"]
    },
    {
        "id": "mhc-002",
        "name": "MHC Kenworth - Kansas City",
        "address": "8600 NE Underground Dr",
        "city": "Kansas City",
        "state": "MO",
        "zip_code": "64161",
        "latitude": 39.1621,
        "longitude": -94.4718,
        "phone": "(816) 483-3200",
        "website": "https://mhc.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth Certified", "Alternative Fuel Ready"],
        "rating": 4.5,
        "review_count": 134,
        "hours": "Mon-Fri 7AM-6PM, Sat 8AM-12PM",
        "services_offered": ["CNG Service", "Heavy Duty Repair", "Parts Sales"]
    },
    {
        "id": "mhc-003",
        "name": "MHC Kenworth - Oklahoma City",
        "address": "7200 SE 59th St",
        "city": "Oklahoma City",
        "state": "OK",
        "zip_code": "73135",
        "latitude": 35.3834,
        "longitude": -97.4537,
        "phone": "(405) 672-7500",
        "website": "https://mhc.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth Dealer", "Natural Gas Service"],
        "rating": 4.4,
        "review_count": 98,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Repair", "Truck Service", "Fleet Maintenance"]
    },
    {
        "id": "mhc-004",
        "name": "MHC Kenworth - Knoxville",
        "address": "2607 N Central St",
        "city": "Knoxville",
        "state": "TN",
        "zip_code": "37917",
        "latitude": 35.9875,
        "longitude": -83.9187,
        "phone": "(865) 522-4131",
        "website": "https://mhc.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth Certified", "CNG Ready"],
        "rating": 4.6,
        "review_count": 112,
        "hours": "Mon-Fri 7AM-6PM",
        "services_offered": ["Alternative Fuel Service", "Heavy Duty Repair", "Parts"]
    },
    # ==================== VELOCITY TRUCK CENTERS ====================
    {
        "id": "velocity-001",
        "name": "Velocity Truck Centers - Fontana",
        "address": "14578 Valley Blvd",
        "city": "Fontana",
        "state": "CA",
        "zip_code": "92335",
        "latitude": 34.0753,
        "longitude": -117.4521,
        "phone": "(909) 349-0200",
        "website": "https://www.velocitytruckcenters.com",
        "fuel_specializations": ["CNG", "Electric", "Hydrogen"],
        "service_type": "In-Shop",
        "certifications": ["Volvo Authorized", "CNG Specialist", "Zero Emission Certified"],
        "rating": 4.5,
        "review_count": 187,
        "hours": "Mon-Fri 6AM-6PM",
        "services_offered": ["CNG Service", "EV Maintenance", "Fleet Support", "Alternative Fuel Consulting"]
    },
    {
        "id": "velocity-002",
        "name": "Velocity Truck Centers - Los Angeles",
        "address": "4900 S Santa Fe Ave",
        "city": "Vernon",
        "state": "CA",
        "zip_code": "90058",
        "latitude": 34.0012,
        "longitude": -118.2128,
        "phone": "(323) 585-7777",
        "website": "https://www.velocitytruckcenters.com",
        "fuel_specializations": ["CNG", "Electric"],
        "service_type": "In-Shop",
        "certifications": ["Mack Certified", "Alternative Fuel Ready"],
        "rating": 4.4,
        "review_count": 145,
        "hours": "Mon-Fri 6AM-5PM",
        "services_offered": ["CNG Repair", "Electric Vehicle Service", "Parts Sales"]
    },
    {
        "id": "velocity-003",
        "name": "Velocity Truck Centers - Phoenix",
        "address": "4025 W Van Buren St",
        "city": "Phoenix",
        "state": "AZ",
        "zip_code": "85009",
        "latitude": 33.4512,
        "longitude": -112.1156,
        "phone": "(602) 269-9500",
        "website": "https://www.velocitytruckcenters.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Volvo Dealer", "Natural Gas Service"],
        "rating": 4.3,
        "review_count": 98,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Service", "Truck Repair", "Fleet Maintenance"]
    },
    # ==================== TEXAS CNG NOW ====================
    {
        "id": "txcng-001",
        "name": "Texas CNG Now",
        "address": "1020 Industrial Blvd",
        "city": "Euless",
        "state": "TX",
        "zip_code": "76040",
        "latitude": 32.8371,
        "longitude": -97.0761,
        "phone": "(682) 415-3291",
        "email": "info@texascngnow.com",
        "website": "https://texascngnow.com",
        "fuel_specializations": ["CNG"],
        "service_type": "Both",
        "certifications": ["Texas Railroad Commission Certified", "CNG Specialist", "AFVi Certified"],
        "rating": 4.9,
        "review_count": 234,
        "hours": "24/7 Mobile Service Available",
        "services_offered": ["CNG Repairs", "Tank Inspections", "Conversions", "Mobile Service", "24/7 Emergency Support"]
    },
    # ==================== OHIO PETERBILT ====================
    {
        "id": "ohpete-001",
        "name": "Ohio Peterbilt - Perrysburg",
        "address": "26391 Glenwood Rd",
        "city": "Perrysburg",
        "state": "OH",
        "zip_code": "43551",
        "latitude": 41.5418,
        "longitude": -83.6421,
        "phone": "(419) 872-9595",
        "website": "https://ohiopeterbilt.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["Peterbilt Platinum", "CNG Certified", "Fleet Services"],
        "rating": 4.8,
        "review_count": 189,
        "hours": "Mon-Fri 7AM-6PM, Sat 8AM-12PM",
        "services_offered": ["CNG Service", "Natural Gas Repair", "26 Service Bays", "Parts Sales"]
    },
    {
        "id": "ohpete-002",
        "name": "Ohio Peterbilt - Cleveland",
        "address": "5000 Transportation Blvd",
        "city": "Cleveland",
        "state": "OH",
        "zip_code": "44125",
        "latitude": 41.4275,
        "longitude": -81.6458,
        "phone": "(216) 642-5600",
        "website": "https://ohiopeterbilt.com",
        "fuel_specializations": ["CNG", "Electric"],
        "service_type": "In-Shop",
        "certifications": ["Peterbilt Dealer", "Alternative Fuel Certified", "EV Ready"],
        "rating": 4.7,
        "review_count": 156,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Repair", "Electric Vehicle Service", "Fleet Support"]
    },
    # ==================== TEC EQUIPMENT ====================
    {
        "id": "tec-001",
        "name": "TEC Equipment - La Mirada CNG Center",
        "address": "15000 Firestone Blvd",
        "city": "La Mirada",
        "state": "CA",
        "zip_code": "90638",
        "latitude": 33.9175,
        "longitude": -118.0125,
        "phone": "(714) 521-9806",
        "website": "https://www.tecequipment.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["Volvo Authorized", "CNG Specialist", "CARB Compliant"],
        "rating": 4.6,
        "review_count": 198,
        "hours": "Mon-Fri 6AM-6PM",
        "services_offered": ["CNG Service", "Natural Gas Repair", "Fleet Maintenance", "Parts Sales"]
    },
    {
        "id": "tec-002",
        "name": "TEC Equipment - Seattle",
        "address": "25619 Pacific Hwy South",
        "city": "Des Moines",
        "state": "WA",
        "zip_code": "98198",
        "latitude": 47.4012,
        "longitude": -122.3134,
        "phone": "(206) 764-3833",
        "website": "https://www.tecequipment.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Volvo Dealer", "Alternative Fuel Service"],
        "rating": 4.5,
        "review_count": 134,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Repair", "Truck Service", "Parts"]
    },
    {
        "id": "tec-003",
        "name": "TEC Equipment - Portland",
        "address": "19350 SW 125th Ct",
        "city": "Tualatin",
        "state": "OR",
        "zip_code": "97062",
        "latitude": 45.3675,
        "longitude": -122.7621,
        "phone": "(503) 612-4000",
        "website": "https://www.tecequipment.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Mack Authorized", "Volvo Dealer"],
        "rating": 4.4,
        "review_count": 112,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["Alternative Fuel Service", "Heavy Duty Repair"]
    },
    # ==================== CALIFORNIA TRUCK CENTERS ====================
    {
        "id": "catruck-001",
        "name": "California Truck Centers - Fresno",
        "address": "3155 S Cherry Ave",
        "city": "Fresno",
        "state": "CA",
        "zip_code": "93706",
        "latitude": 36.7125,
        "longitude": -119.7875,
        "phone": "(559) 233-7721",
        "website": "https://www.californiatruckcenters.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Battle Motors Authorized", "CNG Certified"],
        "rating": 4.4,
        "review_count": 87,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Truck Service", "Parts Sales", "Fleet Support"]
    },
    {
        "id": "catruck-002",
        "name": "California Truck Centers - Sacramento",
        "address": "2851 El Centro Rd",
        "city": "Sacramento",
        "state": "CA",
        "zip_code": "95833",
        "latitude": 38.6175,
        "longitude": -121.4975,
        "phone": "(916) 922-7767",
        "website": "https://www.californiatruckcenters.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["CNG Service Center", "Battle Motors Dealer"],
        "rating": 4.3,
        "review_count": 76,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Service", "Truck Repair", "Parts"]
    },
    {
        "id": "catruck-003",
        "name": "California Truck Centers - Oakland",
        "address": "8350 San Leandro St",
        "city": "Oakland",
        "state": "CA",
        "zip_code": "94621",
        "latitude": 37.7375,
        "longitude": -122.1875,
        "phone": "(510) 568-8500",
        "website": "https://www.californiatruckcenters.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Alternative Fuel Certified"],
        "rating": 4.5,
        "review_count": 98,
        "hours": "Mon-Fri 7AM-6PM",
        "services_offered": ["CNG Repair", "Fleet Maintenance"]
    },
    # ==================== AM PM DIESEL SERVICES ====================
    {
        "id": "ampm-001",
        "name": "AM PM Diesel Services - Houston",
        "address": "5815 Brittmoore Rd",
        "city": "Houston",
        "state": "TX",
        "zip_code": "77041",
        "latitude": 29.8275,
        "longitude": -95.5612,
        "phone": "(713) 466-3780",
        "website": "https://www.ampmdieselsvcs.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "Both",
        "certifications": ["Natural Gas Certified", "Fleet Specialist"],
        "rating": 4.6,
        "review_count": 145,
        "hours": "Mon-Fri 7AM-6PM",
        "services_offered": ["Natural Gas Truck Repair", "Engine Service", "Fleet Training", "Mobile Service"]
    },
    {
        "id": "ampm-002",
        "name": "AM PM Diesel Services - Midland",
        "address": "2701 W Industrial Ave",
        "city": "Midland",
        "state": "TX",
        "zip_code": "79701",
        "latitude": 31.9912,
        "longitude": -102.1175,
        "phone": "(432) 687-1700",
        "website": "https://www.ampmdieselsvcs.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["CNG Repair Certified"],
        "rating": 4.4,
        "review_count": 67,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Service", "Diesel Repair", "Fleet Support"]
    },
    # ==================== NATURAL GAS VEHICLES TEXAS ====================
    {
        "id": "ngvtx-001",
        "name": "Natural Gas Vehicles Texas",
        "address": "10733 Spangler Rd",
        "city": "Dallas",
        "state": "TX",
        "zip_code": "75220",
        "latitude": 32.8675,
        "longitude": -96.8912,
        "phone": "(214) 357-6000",
        "website": "https://www.ngvtexas.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["CNG Specialist", "Conversion Certified", "AFVi Trained"],
        "rating": 4.7,
        "review_count": 156,
        "hours": "Mon-Fri 7:30AM-5PM",
        "services_offered": ["CNG Conversions", "Maintenance", "Tank Inspections", "Parts Sales"]
    },
    # ==================== CLEAN ENERGY FUELS SERVICE ====================
    {
        "id": "cleanenergy-001",
        "name": "Clean Energy - Los Angeles Fleet Services",
        "address": "4675 MacArthur Ct",
        "city": "Newport Beach",
        "state": "CA",
        "zip_code": "92660",
        "latitude": 33.6612,
        "longitude": -117.8675,
        "phone": "(949) 437-1000",
        "website": "https://www.cleanenergyfuels.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "Both",
        "certifications": ["RNG Certified", "Fleet Solutions", "Station Maintenance"],
        "rating": 4.5,
        "review_count": 234,
        "hours": "Mon-Fri 8AM-5PM",
        "services_offered": ["Fleet Consulting", "Station Maintenance", "Fuel Supply", "Training"]
    },
    # ==================== TRILLIUM CNG ====================
    {
        "id": "trillium-001",
        "name": "Trillium CNG - Houston Service Center",
        "address": "1300 Post Oak Blvd",
        "city": "Houston",
        "state": "TX",
        "zip_code": "77056",
        "latitude": 29.7512,
        "longitude": -95.4612,
        "phone": "(713) 629-3600",
        "website": "https://www.trilliumenergy.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["CNG Certified", "Station Operations"],
        "rating": 4.4,
        "review_count": 123,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Station Service", "Fleet Support", "Equipment Maintenance"]
    },
    # ==================== ADDITIONAL CANADIAN LOCATIONS ====================
    {
        "id": "can-001",
        "name": "Peterbilt Pacific - Abbotsford",
        "address": "33735 Gladys Ave",
        "city": "Abbotsford",
        "state": "BC",
        "zip_code": "V2S 2E8",
        "latitude": 49.0512,
        "longitude": -122.3175,
        "phone": "(604) 853-7447",
        "website": "https://peterbiltpacific.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["Peterbilt Dealer", "Natural Gas Specialist"],
        "rating": 4.6,
        "review_count": 89,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG/LNG Service", "Natural Gas Repair", "Parts Sales"]
    },
    {
        "id": "can-002",
        "name": "Cummins Western Canada - Calgary",
        "address": "4003 23rd St NE",
        "city": "Calgary",
        "state": "AB",
        "zip_code": "T2E 6W9",
        "latitude": 51.0712,
        "longitude": -113.9875,
        "phone": "(403) 291-1051",
        "website": "https://www.cummins.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["Cummins Certified", "Natural Gas Specialist"],
        "rating": 4.7,
        "review_count": 134,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["Natural Gas Engine Service", "Parts", "Technical Support"]
    },
    {
        "id": "can-003",
        "name": "Cummins Eastern Canada - Toronto",
        "address": "1200 Creditstone Rd",
        "city": "Vaughan",
        "state": "ON",
        "zip_code": "L4K 5V7",
        "latitude": 43.8175,
        "longitude": -79.5412,
        "phone": "(905) 669-7777",
        "website": "https://www.cummins.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Cummins Authorized", "CNG Certified"],
        "rating": 4.6,
        "review_count": 112,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Service", "Engine Repair", "Fleet Support"]
    },
    # ==================== MORE US LOCATIONS ====================
    {
        "id": "ngvsol-001",
        "name": "NGV Solutions - Salt Lake City",
        "address": "1850 W 2100 S",
        "city": "Salt Lake City",
        "state": "UT",
        "zip_code": "84119",
        "latitude": 40.7275,
        "longitude": -111.9412,
        "phone": "(801) 972-3000",
        "fuel_specializations": ["CNG"],
        "service_type": "Both",
        "certifications": ["CNG Conversion Specialist", "AFVi Certified"],
        "rating": 4.6,
        "review_count": 98,
        "hours": "Mon-Fri 8AM-5PM",
        "services_offered": ["CNG Conversions", "Repair Service", "Tank Inspections", "Mobile Service"]
    },
    {
        "id": "fltngas-001",
        "name": "Fleet Natural Gas Services - Indianapolis",
        "address": "5550 W 74th St",
        "city": "Indianapolis",
        "state": "IN",
        "zip_code": "46278",
        "latitude": 39.8612,
        "longitude": -86.2875,
        "phone": "(317) 297-4450",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["CNG Certified", "Fleet Specialist"],
        "rating": 4.5,
        "review_count": 87,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Repair", "LNG Service", "Fleet Maintenance"]
    },
    {
        "id": "gtruck-001",
        "name": "Georgia Truck Center - Atlanta",
        "address": "5050 Fulton Industrial Blvd",
        "city": "Atlanta",
        "state": "GA",
        "zip_code": "30336",
        "latitude": 33.7512,
        "longitude": -84.5275,
        "phone": "(404) 691-8200",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Peterbilt Dealer", "CNG Ready"],
        "rating": 4.4,
        "review_count": 134,
        "hours": "Mon-Fri 7AM-6PM",
        "services_offered": ["CNG Service", "Truck Repair", "Parts Sales"]
    },
    {
        "id": "nctruck-001",
        "name": "Tri-State Truck Center - Charlotte",
        "address": "4815 North I-85 Service Rd",
        "city": "Charlotte",
        "state": "NC",
        "zip_code": "28269",
        "latitude": 35.3275,
        "longitude": -80.7512,
        "phone": "(704) 598-1616",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth Dealer", "Alternative Fuel Service"],
        "rating": 4.5,
        "review_count": 112,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Repair", "Heavy Duty Service", "Fleet Support"]
    },
    {
        "id": "midwest-001",
        "name": "Midwest Peterbilt - Des Moines",
        "address": "700 E Army Post Rd",
        "city": "Des Moines",
        "state": "IA",
        "zip_code": "50315",
        "latitude": 41.5512,
        "longitude": -93.5875,
        "phone": "(515) 282-8100",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["Peterbilt Certified", "CNG Service"],
        "rating": 4.6,
        "review_count": 89,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["Natural Gas Service", "Truck Repair", "Fleet Maintenance"]
    },
    {
        "id": "sw-001",
        "name": "Southwest Freightliner - Albuquerque",
        "address": "10601 Coors Bypass NW",
        "city": "Albuquerque",
        "state": "NM",
        "zip_code": "87114",
        "latitude": 35.1612,
        "longitude": -106.6875,
        "phone": "(505) 898-3673",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Freightliner Dealer", "Alternative Fuel Ready"],
        "rating": 4.3,
        "review_count": 67,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Service", "Truck Repair", "Parts"]
    },
    {
        "id": "nw-001",
        "name": "Northwest Truck & Trailer - Boise",
        "address": "2901 Elder St",
        "city": "Boise",
        "state": "ID",
        "zip_code": "83705",
        "latitude": 43.5912,
        "longitude": -116.2175,
        "phone": "(208) 344-9452",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Peterbilt Dealer", "CNG Ready"],
        "rating": 4.4,
        "review_count": 56,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Service", "Heavy Duty Repair"]
    },
    {
        "id": "fla-001",
        "name": "Florida Kenworth - Tampa",
        "address": "7501 E Hillsborough Ave",
        "city": "Tampa",
        "state": "FL",
        "zip_code": "33610",
        "latitude": 27.9975,
        "longitude": -82.3512,
        "phone": "(813) 621-8881",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth Certified", "Alternative Fuel Service"],
        "rating": 4.5,
        "review_count": 123,
        "hours": "Mon-Fri 7AM-6PM",
        "services_offered": ["CNG Repair", "Truck Service", "Fleet Support"]
    },
    {
        "id": "fla-002",
        "name": "Florida Kenworth - Miami",
        "address": "1501 NW 112th Ave",
        "city": "Miami",
        "state": "FL",
        "zip_code": "33172",
        "latitude": 25.7875,
        "longitude": -80.3712,
        "phone": "(305) 592-5360",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth Dealer", "CNG Ready"],
        "rating": 4.4,
        "review_count": 98,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Service", "Parts Sales", "Fleet Maintenance"]
    },
    {
        "id": "pac-001",
        "name": "Pacific Truck Centers - Las Vegas",
        "address": "3675 Losee Rd",
        "city": "North Las Vegas",
        "state": "NV",
        "zip_code": "89030",
        "latitude": 36.2312,
        "longitude": -115.1175,
        "phone": "(702) 643-4422",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Peterbilt Dealer", "Alternative Fuel Ready"],
        "rating": 4.3,
        "review_count": 78,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Service", "Truck Repair", "Parts"]
    },
    # ==================== HYDROGEN SERVICE CENTERS ====================
    {
        "id": "h2-001",
        "name": "Nikola Service Center - Phoenix",
        "address": "4141 E Broadway Rd",
        "city": "Phoenix",
        "state": "AZ",
        "zip_code": "85040",
        "latitude": 33.4075,
        "longitude": -111.9812,
        "phone": "(480) 666-2100",
        "website": "https://www.nikolamotor.com",
        "fuel_specializations": ["Hydrogen", "Electric"],
        "service_type": "In-Shop",
        "certifications": ["Nikola Authorized", "Hydrogen Certified", "High Voltage"],
        "rating": 4.7,
        "review_count": 89,
        "hours": "Mon-Fri 7AM-6PM",
        "services_offered": ["Hydrogen Fuel Cell Service", "EV Repair", "Battery Diagnostics"]
    },
    {
        "id": "h2-002",
        "name": "Toyota Hydrogen Service - Los Angeles",
        "address": "19001 S Western Ave",
        "city": "Torrance",
        "state": "CA",
        "zip_code": "90501",
        "latitude": 33.8312,
        "longitude": -118.3112,
        "phone": "(310) 618-4000",
        "website": "https://www.toyota.com",
        "fuel_specializations": ["Hydrogen"],
        "service_type": "In-Shop",
        "certifications": ["Toyota Certified", "Mirai Specialist", "Hydrogen Trained"],
        "rating": 4.8,
        "review_count": 167,
        "hours": "Mon-Fri 7AM-6PM, Sat 8AM-4PM",
        "services_offered": ["Hydrogen Vehicle Service", "Fuel Cell Repair", "Warranty Service"]
    },
    # ==================== EV SERVICE CENTERS ====================
    {
        "id": "ev-001",
        "name": "Daimler Truck Electric - Portland",
        "address": "4747 NE Portland Hwy",
        "city": "Portland",
        "state": "OR",
        "zip_code": "97218",
        "latitude": 45.5712,
        "longitude": -122.5875,
        "phone": "(503) 283-4848",
        "website": "https://www.daimler-truck.com",
        "fuel_specializations": ["Electric"],
        "service_type": "In-Shop",
        "certifications": ["Freightliner eCascadia Certified", "High Voltage Trained"],
        "rating": 4.6,
        "review_count": 112,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["Electric Truck Service", "Battery Diagnostics", "Charging Solutions"]
    },
    {
        "id": "ev-002",
        "name": "BYD Service Center - Los Angeles",
        "address": "1800 S Figueroa St",
        "city": "Los Angeles",
        "state": "CA",
        "zip_code": "90015",
        "latitude": 34.0312,
        "longitude": -118.2675,
        "phone": "(213) 748-3980",
        "website": "https://www.byd.com",
        "fuel_specializations": ["Electric"],
        "service_type": "In-Shop",
        "certifications": ["BYD Authorized", "Electric Vehicle Specialist"],
        "rating": 4.5,
        "review_count": 145,
        "hours": "Mon-Fri 8AM-5PM",
        "services_offered": ["Electric Bus Service", "Battery Repair", "Fleet Support"]
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

# ==================== SUPPORT & FEEDBACK ====================

@api_router.post("/feedback", response_model=Feedback)
async def submit_feedback(feedback: FeedbackCreate):
    """Submit user feedback, suggestion, or support request"""
    feedback_doc = {
        "id": str(uuid.uuid4()),
        "type": feedback.type,
        "subject": feedback.subject,
        "message": feedback.message,
        "user_email": feedback.user_email,
        "user_name": feedback.user_name,
        "platform": feedback.platform,
        "app_version": "1.0.0",
        "status": "new",
        "created_at": datetime.utcnow(),
        "updated_at": None
    }
    
    await db.feedback.insert_one(feedback_doc)
    logger.info(f"New feedback submitted: {feedback.type} - {feedback.subject}")
    
    return Feedback(**feedback_doc)

@api_router.get("/feedback", response_model=List[Feedback])
async def get_all_feedback(
    status: Optional[str] = Query(None, description="Filter by status"),
    feedback_type: Optional[str] = Query(None, description="Filter by type")
):
    """Get all feedback (admin endpoint)"""
    query = {}
    if status:
        query["status"] = status
    if feedback_type:
        query["type"] = feedback_type
    
    feedbacks = await db.feedback.find(query).sort("created_at", -1).to_list(1000)
    return [Feedback(**{**f, "id": f.get("id", str(f.get("_id")))}) for f in feedbacks]

@api_router.get("/feedback/{feedback_id}", response_model=Feedback)
async def get_feedback(feedback_id: str):
    """Get specific feedback by ID"""
    feedback = await db.feedback.find_one({"id": feedback_id})
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return Feedback(**{**feedback, "id": feedback.get("id", str(feedback.get("_id")))})

@api_router.get("/feedback/stats/summary")
async def get_feedback_stats():
    """Get feedback statistics summary"""
    total = await db.feedback.count_documents({})
    new_count = await db.feedback.count_documents({"status": "new"})
    
    # Count by type
    type_counts = {}
    for ftype in ["suggestion", "support", "bug_report", "feature_request", "general"]:
        type_counts[ftype] = await db.feedback.count_documents({"type": ftype})
    
    return {
        "total": total,
        "new": new_count,
        "by_type": type_counts
    }

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
