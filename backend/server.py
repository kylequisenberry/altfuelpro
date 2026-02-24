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
import math

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

# ==================== ROUTE PLANNER MODELS ====================

class RouteLocation(BaseModel):
    name: str
    latitude: float
    longitude: float
    address: Optional[str] = None

class VehicleSettings(BaseModel):
    fuel_type: str = "CNG"
    tank_capacity_dge: float = 60  # Diesel Gallon Equivalent
    mpg_dge: float = 6  # Miles per DGE
    reserve_percentage: float = 15  # Keep 15% reserve

class FuelStop(BaseModel):
    station_id: str
    station_name: str
    address: str
    city: str
    state: str
    latitude: float
    longitude: float
    fuel_types: List[str]
    distance_from_start: float  # Miles
    distance_from_previous: float  # Miles
    estimated_fuel_needed: float  # DGE
    phone: Optional[str] = None
    access_hours: Optional[str] = None

class RouteSegment(BaseModel):
    from_location: str
    to_location: str
    distance_miles: float
    distance_km: float
    estimated_time_hours: float

class RoutePlan(BaseModel):
    origin: RouteLocation
    destination: RouteLocation
    total_distance_miles: float
    total_distance_km: float
    estimated_total_time_hours: float
    fuel_stops: List[FuelStop]
    segments: List[RouteSegment]
    total_fuel_needed_dge: float
    estimated_fuel_cost: float
    vehicle_settings: VehicleSettings
    warnings: List[str] = []

class RoutePlanRequest(BaseModel):
    origin_lat: float
    origin_lng: float
    origin_name: str = "Origin"
    destination_lat: float
    destination_lng: float
    destination_name: str = "Destination"
    fuel_type: str = "CNG"
    tank_capacity_dge: float = 60
    mpg_dge: float = 6
    reserve_percentage: float = 15

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
    },
    # ==================== ADDITIONAL RUSH TRUCK CENTERS ====================
    {
        "id": "rush-007",
        "name": "Rush Truck Centers - Atlanta",
        "address": "2900 Moreland Ave SE",
        "city": "Atlanta",
        "state": "GA",
        "zip_code": "30315",
        "latitude": 33.7012,
        "longitude": -84.3562,
        "phone": "(404) 622-0100",
        "website": "https://www.rushtruckcenters.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["Peterbilt Certified", "Natural Gas Specialist", "ASE Certified"],
        "rating": 4.6,
        "review_count": 187,
        "hours": "Mon-Fri 7AM-6PM, Sat 8AM-12PM",
        "services_offered": ["CNG System Repair", "Natural Gas Engine Service", "Fleet Maintenance", "DOT Inspections"]
    },
    {
        "id": "rush-008",
        "name": "Rush Truck Centers - Nashville",
        "address": "1420 Murfreesboro Pike",
        "city": "Nashville",
        "state": "TN",
        "zip_code": "37217",
        "latitude": 36.1175,
        "longitude": -86.7125,
        "phone": "(615) 361-1600",
        "website": "https://www.rushtruckcenters.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["Peterbilt Platinum", "CNG Certified", "Fleet Solutions"],
        "rating": 4.5,
        "review_count": 156,
        "hours": "Mon-Fri 7AM-6PM",
        "services_offered": ["CNG Repairs", "Preventive Maintenance", "Parts Sales", "Tank Inspection"]
    },
    {
        "id": "rush-009",
        "name": "Rush Truck Centers - Memphis",
        "address": "3250 Lamar Ave",
        "city": "Memphis",
        "state": "TN",
        "zip_code": "38118",
        "latitude": 35.0512,
        "longitude": -89.9675,
        "phone": "(901) 365-0330",
        "website": "https://www.rushtruckcenters.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Natural Gas Certified", "Peterbilt Dealer"],
        "rating": 4.4,
        "review_count": 134,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Service", "Fleet Maintenance", "Parts & Accessories"]
    },
    {
        "id": "rush-010",
        "name": "Rush Truck Centers - Jacksonville",
        "address": "11350 Eastport Rd",
        "city": "Jacksonville",
        "state": "FL",
        "zip_code": "32218",
        "latitude": 30.4175,
        "longitude": -81.5412,
        "phone": "(904) 757-1900",
        "website": "https://www.rushtruckcenters.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["CNG Specialist", "Peterbilt Certified", "Fleet Services"],
        "rating": 4.6,
        "review_count": 167,
        "hours": "Mon-Fri 7AM-6PM",
        "services_offered": ["CNG Repair", "Fuel System Service", "Fleet Support", "Mobile Service"]
    },
    {
        "id": "rush-011",
        "name": "Rush Truck Centers - Birmingham",
        "address": "1901 Vanderbilt Rd",
        "city": "Birmingham",
        "state": "AL",
        "zip_code": "35234",
        "latitude": 33.5412,
        "longitude": -86.8175,
        "phone": "(205) 251-2831",
        "website": "https://www.rushtruckcenters.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Peterbilt Dealer", "Alternative Fuel Ready"],
        "rating": 4.5,
        "review_count": 123,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Service", "Heavy Duty Repair", "Parts Sales"]
    },
    {
        "id": "rush-012",
        "name": "Rush Truck Centers - Oklahoma City",
        "address": "6200 S I-35 Service Rd",
        "city": "Oklahoma City",
        "state": "OK",
        "zip_code": "73149",
        "latitude": 35.3875,
        "longitude": -97.4912,
        "phone": "(405) 631-2800",
        "website": "https://www.rushtruckcenters.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["Natural Gas Certified", "Cummins Authorized"],
        "rating": 4.6,
        "review_count": 145,
        "hours": "Mon-Fri 7AM-6PM, Sat 8AM-12PM",
        "services_offered": ["CNG/LNG Service", "Engine Repair", "Tank Inspection", "Fleet Support"]
    },
    {
        "id": "rush-013",
        "name": "Rush Truck Centers - New Orleans",
        "address": "5200 Lapalco Blvd",
        "city": "Marrero",
        "state": "LA",
        "zip_code": "70072",
        "latitude": 29.8875,
        "longitude": -90.1012,
        "phone": "(504) 340-5000",
        "website": "https://www.rushtruckcenters.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Peterbilt Certified", "CNG Ready"],
        "rating": 4.4,
        "review_count": 98,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Repair", "Truck Service", "Parts"]
    },
    {
        "id": "rush-014",
        "name": "Rush Truck Centers - Albuquerque",
        "address": "6400 Pan American Fwy NE",
        "city": "Albuquerque",
        "state": "NM",
        "zip_code": "87109",
        "latitude": 35.1512,
        "longitude": -106.5812,
        "phone": "(505) 345-8781",
        "website": "https://www.rushtruckcenters.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Alternative Fuel Service", "Peterbilt Dealer"],
        "rating": 4.3,
        "review_count": 87,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Service", "Truck Repair", "Fleet Maintenance"]
    },
    {
        "id": "rush-015",
        "name": "Rush Truck Centers - El Paso",
        "address": "11500 Gateway Blvd E",
        "city": "El Paso",
        "state": "TX",
        "zip_code": "79927",
        "latitude": 31.7812,
        "longitude": -106.3312,
        "phone": "(915) 859-1233",
        "website": "https://www.rushtruckcenters.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["CNG Certified", "Border Corridor Specialist"],
        "rating": 4.5,
        "review_count": 112,
        "hours": "Mon-Fri 7AM-6PM",
        "services_offered": ["Natural Gas Service", "Tank Inspection", "Fleet Support"]
    },
    # ==================== ADDITIONAL CUMMINS LOCATIONS ====================
    {
        "id": "cummins-006",
        "name": "Cummins Sales and Service - Phoenix",
        "address": "4202 W Buckeye Rd",
        "city": "Phoenix",
        "state": "AZ",
        "zip_code": "85009",
        "latitude": 33.4312,
        "longitude": -112.1175,
        "phone": "(602) 272-8571",
        "website": "https://www.cummins.com",
        "fuel_specializations": ["CNG", "LNG", "Hydrogen"],
        "service_type": "Both",
        "certifications": ["Cummins Master Certified", "X15N Specialist", "Zero Emission Ready"],
        "rating": 4.7,
        "review_count": 234,
        "hours": "Mon-Fri 7AM-6PM",
        "services_offered": ["Natural Gas Engine Service", "CNG System Repair", "Mobile Service", "Technical Training"]
    },
    {
        "id": "cummins-007",
        "name": "Cummins Sales and Service - Denver",
        "address": "5025 Washington St",
        "city": "Denver",
        "state": "CO",
        "zip_code": "80216",
        "latitude": 39.7812,
        "longitude": -104.9712,
        "phone": "(303) 292-8500",
        "website": "https://www.cummins.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["Cummins Certified", "Natural Gas Specialist", "High Altitude Expert"],
        "rating": 4.8,
        "review_count": 198,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["Natural Gas Engine Repair", "Parts Sales", "Warranty Service", "Fleet Support"]
    },
    {
        "id": "cummins-008",
        "name": "Cummins Sales and Service - Seattle",
        "address": "1830 13th Ave S",
        "city": "Seattle",
        "state": "WA",
        "zip_code": "98144",
        "latitude": 47.5875,
        "longitude": -122.3112,
        "phone": "(206) 329-5055",
        "website": "https://www.cummins.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["Cummins Authorized", "Pacific Northwest Hub"],
        "rating": 4.6,
        "review_count": 167,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Service", "Engine Repair", "Parts", "Technical Support"]
    },
    {
        "id": "cummins-009",
        "name": "Cummins Sales and Service - Minneapolis",
        "address": "4501 68th Ave N",
        "city": "Minneapolis",
        "state": "MN",
        "zip_code": "55429",
        "latitude": 45.0612,
        "longitude": -93.3512,
        "phone": "(763) 535-0631",
        "website": "https://www.cummins.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["Cummins Master Tech", "Cold Weather Specialist"],
        "rating": 4.7,
        "review_count": 145,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["Natural Gas Engine Service", "Cold Weather Systems", "Fleet Maintenance"]
    },
    {
        "id": "cummins-010",
        "name": "Cummins Sales and Service - Detroit",
        "address": "1380 E Big Beaver Rd",
        "city": "Troy",
        "state": "MI",
        "zip_code": "48083",
        "latitude": 42.5612,
        "longitude": -83.1375,
        "phone": "(248) 524-0606",
        "website": "https://www.cummins.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "Both",
        "certifications": ["Cummins Certified", "OEM Authorized", "X15N Specialist"],
        "rating": 4.8,
        "review_count": 223,
        "hours": "Mon-Fri 6AM-6PM, Sat 8AM-12PM",
        "services_offered": ["Natural Gas Engine Service", "Emergency Repair", "Parts Sales", "Training"]
    },
    {
        "id": "cummins-011",
        "name": "Cummins Sales and Service - Philadelphia",
        "address": "3501 Island Ave",
        "city": "Philadelphia",
        "state": "PA",
        "zip_code": "19153",
        "latitude": 39.8812,
        "longitude": -75.2412,
        "phone": "(215) 365-6500",
        "website": "https://www.cummins.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Cummins Authorized", "Northeast Hub"],
        "rating": 4.5,
        "review_count": 156,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Engine Service", "Parts & Service", "Fleet Support"]
    },
    {
        "id": "cummins-012",
        "name": "Cummins Sales and Service - Boston",
        "address": "200 Brookdale Dr",
        "city": "Springfield",
        "state": "MA",
        "zip_code": "01104",
        "latitude": 42.1312,
        "longitude": -72.5675,
        "phone": "(413) 736-9241",
        "website": "https://www.cummins.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Cummins Dealer", "Natural Gas Certified"],
        "rating": 4.4,
        "review_count": 123,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Repair", "Engine Service", "Parts"]
    },
    {
        "id": "cummins-013",
        "name": "Cummins Sales and Service - Salt Lake City",
        "address": "2255 S 300 W",
        "city": "Salt Lake City",
        "state": "UT",
        "zip_code": "84115",
        "latitude": 40.7312,
        "longitude": -111.8912,
        "phone": "(801) 487-3671",
        "website": "https://www.cummins.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["Cummins Certified", "Mountain Region Hub"],
        "rating": 4.6,
        "review_count": 134,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["Natural Gas Service", "Engine Overhaul", "Parts Sales"]
    },
    {
        "id": "cummins-014",
        "name": "Cummins Sales and Service - Portland",
        "address": "9525 N Whitaker Rd",
        "city": "Portland",
        "state": "OR",
        "zip_code": "97217",
        "latitude": 45.5912,
        "longitude": -122.7312,
        "phone": "(503) 285-2141",
        "website": "https://www.cummins.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Cummins Authorized", "Pacific Northwest Specialist"],
        "rating": 4.5,
        "review_count": 112,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Engine Repair", "Fleet Maintenance", "Parts"]
    },
    {
        "id": "cummins-015",
        "name": "Cummins Sales and Service - Kansas City",
        "address": "7300 E Frontage Rd",
        "city": "Merriam",
        "state": "KS",
        "zip_code": "66204",
        "latitude": 39.0112,
        "longitude": -94.6812,
        "phone": "(913) 722-3838",
        "website": "https://www.cummins.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["Cummins Master Certified", "Midwest Hub"],
        "rating": 4.7,
        "review_count": 178,
        "hours": "Mon-Fri 7AM-6PM",
        "services_offered": ["Natural Gas Engine Service", "CNG System Repair", "Technical Training"]
    },
    # ==================== INLAND KENWORTH ====================
    {
        "id": "inland-001",
        "name": "Inland Kenworth - San Diego",
        "address": "8650 Miramar Pl",
        "city": "San Diego",
        "state": "CA",
        "zip_code": "92121",
        "latitude": 32.8912,
        "longitude": -117.1512,
        "phone": "(858) 578-0550",
        "website": "https://www.inland-group.com",
        "fuel_specializations": ["CNG", "Electric"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth Certified", "Alternative Fuel Ready", "EV Service"],
        "rating": 4.6,
        "review_count": 156,
        "hours": "Mon-Fri 7AM-6PM",
        "services_offered": ["CNG Service", "Electric Vehicle Repair", "Fleet Support", "Parts Sales"]
    },
    {
        "id": "inland-002",
        "name": "Inland Kenworth - Mesa",
        "address": "1616 S Country Club Dr",
        "city": "Mesa",
        "state": "AZ",
        "zip_code": "85210",
        "latitude": 33.3912,
        "longitude": -111.8312,
        "phone": "(480) 834-9500",
        "website": "https://www.inland-group.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth Dealer", "Natural Gas Service", "12 Service Bays"],
        "rating": 4.5,
        "review_count": 134,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Repair", "LNG Service", "Heavy Duty Repair", "Parts"]
    },
    {
        "id": "inland-003",
        "name": "Inland Kenworth - El Centro",
        "address": "2100 N Imperial Ave",
        "city": "El Centro",
        "state": "CA",
        "zip_code": "92243",
        "latitude": 32.8112,
        "longitude": -115.5512,
        "phone": "(760) 352-0261",
        "website": "https://www.inland-group.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth Certified", "Border Region Specialist"],
        "rating": 4.4,
        "review_count": 89,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Service", "Truck Repair", "Fleet Maintenance"]
    },
    {
        "id": "inland-004",
        "name": "Inland Kenworth - Tucson",
        "address": "3650 E Irvington Rd",
        "city": "Tucson",
        "state": "AZ",
        "zip_code": "85714",
        "latitude": 32.1512,
        "longitude": -110.9112,
        "phone": "(520) 294-2000",
        "website": "https://www.inland-group.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth Dealer", "CNG Ready"],
        "rating": 4.5,
        "review_count": 98,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["Alternative Fuel Service", "Heavy Duty Repair", "Parts Sales"]
    },
    # ==================== KENWORTH SALES COMPANY ====================
    {
        "id": "kwsales-001",
        "name": "Kenworth Sales Company - Salt Lake City",
        "address": "4225 W 2100 S",
        "city": "West Valley City",
        "state": "UT",
        "zip_code": "84120",
        "latitude": 40.7212,
        "longitude": -111.9712,
        "phone": "(801) 972-5511",
        "website": "https://www.kenworthsalesco.com",
        "fuel_specializations": ["CNG", "LNG", "Hydrogen"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth PremierCare Gold", "55 Service Bays", "Alternative Fuel Specialist"],
        "rating": 4.9,
        "review_count": 312,
        "hours": "Mon-Fri 6AM-10PM, Sat 7AM-3PM",
        "services_offered": ["CNG/LNG Service", "Hydrogen Ready", "Express Maintenance", "Body Shop", "Paint Booth"]
    },
    {
        "id": "kwsales-002",
        "name": "Kenworth Sales Company - Reno",
        "address": "1250 E Greg St",
        "city": "Sparks",
        "state": "NV",
        "zip_code": "89431",
        "latitude": 39.5312,
        "longitude": -119.7112,
        "phone": "(775) 358-5554",
        "website": "https://www.kenworthsalesco.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth Certified", "PremierCare Gold"],
        "rating": 4.6,
        "review_count": 145,
        "hours": "Mon-Fri 7AM-6PM",
        "services_offered": ["CNG Service", "Fleet Maintenance", "Parts Sales"]
    },
    {
        "id": "kwsales-003",
        "name": "Kenworth Sales Company - Idaho Falls",
        "address": "2385 W Broadway St",
        "city": "Idaho Falls",
        "state": "ID",
        "zip_code": "83402",
        "latitude": 43.4812,
        "longitude": -112.0512,
        "phone": "(208) 523-8880",
        "website": "https://www.kenworthsalesco.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth Dealer", "Mountain Region Service"],
        "rating": 4.5,
        "review_count": 87,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Repair", "Truck Service", "Parts"]
    },
    # ==================== GABRIELLI TRUCK SALES (NY TRI-STATE) ====================
    {
        "id": "gabrielli-001",
        "name": "Gabrielli Truck Sales - Jamaica, NY",
        "address": "153-10 130th Ave",
        "city": "Jamaica",
        "state": "NY",
        "zip_code": "11434",
        "latitude": 40.6612,
        "longitude": -73.7912,
        "phone": "(718) 528-4100",
        "website": "https://www.gabriellitruck.com",
        "fuel_specializations": ["CNG", "Electric"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth PremierCare Gold", "ExpressLane", "NYC Fleet Specialist"],
        "rating": 4.7,
        "review_count": 234,
        "hours": "Mon-Fri 7AM-6PM, Sat 8AM-12PM",
        "services_offered": ["CNG Service", "EV Repair", "Fleet Maintenance", "Body Shop", "Towing"]
    },
    {
        "id": "gabrielli-002",
        "name": "Gabrielli Truck Sales - Bronx, NY",
        "address": "899 Brush Ave",
        "city": "Bronx",
        "state": "NY",
        "zip_code": "10465",
        "latitude": 40.8212,
        "longitude": -73.8212,
        "phone": "(718) 863-2800",
        "website": "https://www.gabriellitruck.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth Dealer", "Urban Fleet Support"],
        "rating": 4.5,
        "review_count": 156,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Repair", "Heavy Duty Service", "Parts Sales"]
    },
    {
        "id": "gabrielli-003",
        "name": "Gabrielli Truck Sales - Newark, NJ",
        "address": "350 Frelinghuysen Ave",
        "city": "Newark",
        "state": "NJ",
        "zip_code": "07114",
        "latitude": 40.7112,
        "longitude": -74.1612,
        "phone": "(973) 242-1700",
        "website": "https://www.gabriellitruck.com",
        "fuel_specializations": ["CNG", "Electric"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth PremierCare Gold", "Port Region Specialist"],
        "rating": 4.6,
        "review_count": 178,
        "hours": "Mon-Fri 7AM-6PM",
        "services_offered": ["CNG Service", "EV Maintenance", "Fleet Support", "DOT Inspections"]
    },
    {
        "id": "gabrielli-004",
        "name": "Gabrielli Truck Sales - Milford, CT",
        "address": "255 Bic Dr",
        "city": "Milford",
        "state": "CT",
        "zip_code": "06461",
        "latitude": 41.2312,
        "longitude": -73.0112,
        "phone": "(203) 876-3500",
        "website": "https://www.gabriellitruck.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth Dealer", "New England Region"],
        "rating": 4.4,
        "review_count": 112,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Service", "Truck Repair", "Parts"]
    },
    # ==================== CIT TRUCKS (CHICAGO AREA) ====================
    {
        "id": "cit-001",
        "name": "CIT Trucks - Wood Dale",
        "address": "3N150 N 25th Ave",
        "city": "Wood Dale",
        "state": "IL",
        "zip_code": "60191",
        "latitude": 41.9512,
        "longitude": -87.9712,
        "phone": "(630) 860-5100",
        "website": "https://www.cittrucks.com",
        "fuel_specializations": ["CNG", "LNG", "Electric"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth Certified", "64 Service Bays", "Alternative Fuel Center"],
        "rating": 4.8,
        "review_count": 267,
        "hours": "Mon-Fri 6AM-10PM, Sat 7AM-3PM",
        "services_offered": ["CNG/LNG Service", "EV Repair", "24/7 Roadside", "16,000 sq ft Parts"]
    },
    {
        "id": "cit-002",
        "name": "CIT Trucks - Gary",
        "address": "3100 W 15th Ave",
        "city": "Gary",
        "state": "IN",
        "zip_code": "46404",
        "latitude": 41.5712,
        "longitude": -87.3612,
        "phone": "(219) 944-0440",
        "website": "https://www.cittrucks.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth Dealer", "Chicagoland Region"],
        "rating": 4.5,
        "review_count": 134,
        "hours": "Mon-Fri 7AM-6PM",
        "services_offered": ["CNG Service", "Heavy Duty Repair", "Parts Sales"]
    },
    # ==================== MICHIGAN KENWORTH ====================
    {
        "id": "mikenworth-001",
        "name": "Michigan Kenworth - Van Buren Township",
        "address": "41151 Van Born Rd",
        "city": "Van Buren Township",
        "state": "MI",
        "zip_code": "48111",
        "latitude": 42.2312,
        "longitude": -83.4912,
        "phone": "(734) 326-1100",
        "website": "https://www.michigankenworth.com",
        "fuel_specializations": ["CNG", "LNG", "Electric"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth PremierCare Gold", "24 Service Bays", "EV Certified"],
        "rating": 4.7,
        "review_count": 198,
        "hours": "Mon-Fri 7AM-6PM, Sat 8AM-12PM",
        "services_offered": ["CNG/LNG Service", "Electric Truck Repair", "Parts Warehouse", "Fleet Support"]
    },
    {
        "id": "mikenworth-002",
        "name": "Michigan Kenworth - Grand Rapids",
        "address": "4300 36th St SE",
        "city": "Grand Rapids",
        "state": "MI",
        "zip_code": "49512",
        "latitude": 42.8912,
        "longitude": -85.5312,
        "phone": "(616) 698-9500",
        "website": "https://www.michigankenworth.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth Dealer", "West Michigan Hub"],
        "rating": 4.5,
        "review_count": 145,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Service", "Truck Repair", "Parts Sales"]
    },
    # ==================== KENWORTH OF LOUISIANA ====================
    {
        "id": "kwla-001",
        "name": "Kenworth of Louisiana - Hammond",
        "address": "42464 Veterans Ave",
        "city": "Hammond",
        "state": "LA",
        "zip_code": "70403",
        "latitude": 30.5112,
        "longitude": -90.4612,
        "phone": "(985) 345-8600",
        "website": "https://www.kenworthoflouisiana.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth Certified", "22 Service Bays", "Gulf Coast Hub"],
        "rating": 4.6,
        "review_count": 167,
        "hours": "Mon-Fri 7AM-6PM",
        "services_offered": ["CNG/LNG Service", "7,000 sq ft Parts", "Fleet Maintenance"]
    },
    {
        "id": "kwla-002",
        "name": "Kenworth of Louisiana - Lake Charles",
        "address": "2200 E Prien Lake Rd",
        "city": "Lake Charles",
        "state": "LA",
        "zip_code": "70601",
        "latitude": 30.1812,
        "longitude": -93.1712,
        "phone": "(337) 477-7700",
        "website": "https://www.kenworthoflouisiana.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth Dealer", "Southwest Louisiana Region"],
        "rating": 4.4,
        "review_count": 98,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Service", "Heavy Duty Repair", "Parts"]
    },
    # ==================== EXPANDED CANADIAN NETWORK ====================
    {
        "id": "can-004",
        "name": "Velocity Truck Centres - Edmonton CNG/H2 Hub",
        "address": "18004 118 Ave NW",
        "city": "Edmonton",
        "state": "AB",
        "zip_code": "T5S 2G2",
        "latitude": 53.5612,
        "longitude": -113.5712,
        "phone": "(780) 447-1200",
        "website": "https://www.velocitytruckcentres.ca",
        "fuel_specializations": ["CNG", "LNG", "Hydrogen"],
        "service_type": "In-Shop",
        "certifications": ["Volvo Authorized", "Alberta First H2/CNG Bay", "Zero Emission Certified"],
        "rating": 4.8,
        "review_count": 145,
        "hours": "Mon-Fri 7AM-6PM",
        "services_offered": ["CNG/LNG Service", "Hydrogen Fuel Cell Repair", "EV Maintenance", "Technical Training"]
    },
    {
        "id": "can-005",
        "name": "Velocity Truck Centres - Surrey",
        "address": "19295 Langley Bypass",
        "city": "Surrey",
        "state": "BC",
        "zip_code": "V3S 6K1",
        "latitude": 49.1112,
        "longitude": -122.6612,
        "phone": "(604) 888-2885",
        "website": "https://www.velocitytruckcentres.ca",
        "fuel_specializations": ["CNG", "Electric"],
        "service_type": "In-Shop",
        "certifications": ["Volvo Dealer", "Lower Mainland Hub", "Alternative Fuel Ready"],
        "rating": 4.6,
        "review_count": 134,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Service", "Electric Truck Repair", "Fleet Support"]
    },
    {
        "id": "can-006",
        "name": "TransWestern Truck Centres - Calgary South",
        "address": "5555 11 St SE",
        "city": "Calgary",
        "state": "AB",
        "zip_code": "T2H 1M7",
        "latitude": 50.9912,
        "longitude": -114.0512,
        "phone": "(403) 252-9600",
        "website": "https://www.transwestern.ca",
        "fuel_specializations": ["CNG", "LNG", "Electric"],
        "service_type": "In-Shop",
        "certifications": ["Mack Trucks Certified", "CNG Service", "EV Ready", "Hydrogen Expansion Planned"],
        "rating": 4.7,
        "review_count": 178,
        "hours": "Mon-Fri 7AM-6PM, Sat 8AM-12PM",
        "services_offered": ["CNG/LNG Repair", "Electric Truck Service", "Parts Sales", "Fleet Maintenance"]
    },
    {
        "id": "can-007",
        "name": "Cummins Western Canada - Edmonton",
        "address": "18303 118 Ave NW",
        "city": "Edmonton",
        "state": "AB",
        "zip_code": "T5S 2G3",
        "latitude": 53.5612,
        "longitude": -113.5812,
        "phone": "(780) 447-1141",
        "website": "https://www.cummins.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "Both",
        "certifications": ["Cummins Master Certified", "X15N Specialist", "Mobile Service Available"],
        "rating": 4.8,
        "review_count": 167,
        "hours": "Mon-Fri 7AM-6PM",
        "services_offered": ["Natural Gas Engine Service", "CNG System Repair", "Mobile Service", "Parts"]
    },
    {
        "id": "can-008",
        "name": "Peterbilt Pacific - Calgary",
        "address": "6505 72 Ave SE",
        "city": "Calgary",
        "state": "AB",
        "zip_code": "T2C 4Y5",
        "latitude": 50.9812,
        "longitude": -113.9612,
        "phone": "(403) 720-2322",
        "website": "https://peterbiltpacific.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["Peterbilt Certified", "Natural Gas Specialist", "Western Canada Hub"],
        "rating": 4.6,
        "review_count": 145,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG/LNG Service", "Natural Gas Repair", "Parts Sales", "Fleet Support"]
    },
    {
        "id": "can-009",
        "name": "Peterbilt Pacific - Vancouver",
        "address": "1855 Brigantine Dr",
        "city": "Coquitlam",
        "state": "BC",
        "zip_code": "V3K 7B7",
        "latitude": 49.2512,
        "longitude": -122.8012,
        "phone": "(604) 523-8484",
        "website": "https://peterbiltpacific.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Peterbilt Dealer", "Port of Vancouver Region"],
        "rating": 4.5,
        "review_count": 112,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Service", "Heavy Duty Repair", "Parts"]
    },
    {
        "id": "can-010",
        "name": "Kenworth Montreal - Laval",
        "address": "2400 Boul Industriel",
        "city": "Laval",
        "state": "QC",
        "zip_code": "H7S 1P3",
        "latitude": 45.5612,
        "longitude": -73.7212,
        "phone": "(450) 667-5200",
        "website": "https://www.kenworthmontreal.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth Certified", "Quebec Hub", "Bilingual Service"],
        "rating": 4.5,
        "review_count": 134,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Service", "Truck Repair", "Parts Sales", "Fleet Maintenance"]
    },
    {
        "id": "can-011",
        "name": "Kenworth Truck Centres Ontario - Mississauga",
        "address": "6900 Tranmere Dr",
        "city": "Mississauga",
        "state": "ON",
        "zip_code": "L5S 1L9",
        "latitude": 43.6812,
        "longitude": -79.6512,
        "phone": "(905) 564-8000",
        "website": "https://www.kenworthontario.com",
        "fuel_specializations": ["CNG", "Electric"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth PremierCare Gold", "GTA Hub", "EV Ready"],
        "rating": 4.7,
        "review_count": 189,
        "hours": "Mon-Fri 7AM-6PM",
        "services_offered": ["CNG Service", "Electric Truck Repair", "Fleet Support", "Parts Warehouse"]
    },
    {
        "id": "can-012",
        "name": "Rush Truck Centres Canada - Mississauga",
        "address": "7070 Pacific Cir",
        "city": "Mississauga",
        "state": "ON",
        "zip_code": "L5T 2A7",
        "latitude": 43.6412,
        "longitude": -79.6812,
        "phone": "(905) 564-7800",
        "website": "https://www.rushtruckcentres.ca",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["Peterbilt Certified", "CNG Specialist", "Ontario Region"],
        "rating": 4.6,
        "review_count": 156,
        "hours": "Mon-Fri 7AM-6PM",
        "services_offered": ["Natural Gas Service", "CNG Repair", "Fleet Maintenance", "Parts"]
    },
    # ==================== ADDITIONAL US COVERAGE - NORTHEAST ====================
    {
        "id": "kwne-001",
        "name": "Kenworth Northeast - Albany",
        "address": "1 Stonebreak Rd Extension",
        "city": "Malta",
        "state": "NY",
        "zip_code": "12020",
        "latitude": 42.9912,
        "longitude": -73.7912,
        "phone": "(518) 885-2700",
        "website": "https://www.kenworthne.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth PremierCare Gold", "Upstate NY Hub"],
        "rating": 4.5,
        "review_count": 112,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Service", "Truck Repair", "Parts Sales"]
    },
    {
        "id": "kwne-002",
        "name": "Kenworth Northeast - Syracuse",
        "address": "6483 Yorktown Cir",
        "city": "East Syracuse",
        "state": "NY",
        "zip_code": "13057",
        "latitude": 43.0512,
        "longitude": -76.0512,
        "phone": "(315) 437-2878",
        "website": "https://www.kenworthne.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth Dealer", "Central NY Region"],
        "rating": 4.4,
        "review_count": 98,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Repair", "Heavy Duty Service", "Parts"]
    },
    {
        "id": "kwne-003",
        "name": "Kenworth Northeast - Auburn, MA",
        "address": "150 Washington St",
        "city": "Auburn",
        "state": "MA",
        "zip_code": "01501",
        "latitude": 42.1912,
        "longitude": -71.8412,
        "phone": "(508) 832-9911",
        "website": "https://www.kenworthne.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth PremierCare Gold", "New England Hub"],
        "rating": 4.6,
        "review_count": 134,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Service", "Fleet Maintenance", "Parts Sales"]
    },
    # ==================== ADDITIONAL US COVERAGE - SOUTHEAST ====================
    {
        "id": "se-001",
        "name": "Kenworth of South Florida - Fort Lauderdale",
        "address": "4751 Oakes Rd",
        "city": "Davie",
        "state": "FL",
        "zip_code": "33314",
        "latitude": 26.0812,
        "longitude": -80.2312,
        "phone": "(954) 791-8800",
        "website": "https://www.kenworthsouthflorida.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth Certified", "South Florida Hub"],
        "rating": 4.5,
        "review_count": 145,
        "hours": "Mon-Fri 7AM-6PM",
        "services_offered": ["CNG Service", "Heavy Duty Repair", "Parts Sales", "Fleet Support"]
    },
    {
        "id": "se-002",
        "name": "Kenworth of Central Florida - Ocala",
        "address": "3700 NW Blitchton Rd",
        "city": "Ocala",
        "state": "FL",
        "zip_code": "34475",
        "latitude": 29.2012,
        "longitude": -82.1912,
        "phone": "(352) 629-5055",
        "website": "https://www.kenworthcentralflorida.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth Dealer", "I-75 Corridor"],
        "rating": 4.4,
        "review_count": 112,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Repair", "Truck Service", "Parts"]
    },
    {
        "id": "se-003",
        "name": "MHC Kenworth - Little Rock",
        "address": "10524 Maumelle Blvd",
        "city": "North Little Rock",
        "state": "AR",
        "zip_code": "72113",
        "latitude": 34.8412,
        "longitude": -92.4012,
        "phone": "(501) 945-0065",
        "website": "https://mhc.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth Certified", "Arkansas Hub"],
        "rating": 4.5,
        "review_count": 123,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG/LNG Service", "Truck Repair", "Parts Sales"]
    },
    {
        "id": "se-004",
        "name": "Peterbilt of Mississippi - Jackson",
        "address": "3530 I-55 S Frontage Rd",
        "city": "Jackson",
        "state": "MS",
        "zip_code": "39212",
        "latitude": 32.2312,
        "longitude": -90.2012,
        "phone": "(601) 373-0080",
        "website": "https://www.peterbiltofmississippi.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Peterbilt Dealer", "Mississippi Hub"],
        "rating": 4.4,
        "review_count": 98,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Service", "Heavy Duty Repair", "Parts"]
    },
    # ==================== ADDITIONAL US COVERAGE - MIDWEST ====================
    {
        "id": "mw-001",
        "name": "Kenworth of Indianapolis",
        "address": "8350 Bash St",
        "city": "Indianapolis",
        "state": "IN",
        "zip_code": "46256",
        "latitude": 39.9112,
        "longitude": -86.0312,
        "phone": "(317) 577-1700",
        "website": "https://www.kenworthindy.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth PremierCare Gold", "Crossroads Hub"],
        "rating": 4.6,
        "review_count": 167,
        "hours": "Mon-Fri 7AM-6PM",
        "services_offered": ["CNG/LNG Service", "Fleet Maintenance", "Parts Warehouse"]
    },
    {
        "id": "mw-002",
        "name": "Kenworth of Cincinnati",
        "address": "11757 Mosteller Rd",
        "city": "Cincinnati",
        "state": "OH",
        "zip_code": "45241",
        "latitude": 39.2912,
        "longitude": -84.4112,
        "phone": "(513) 771-8100",
        "website": "https://www.kenworthcincy.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth Certified", "Tri-State Region"],
        "rating": 4.5,
        "review_count": 145,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Service", "Truck Repair", "Parts Sales"]
    },
    {
        "id": "mw-003",
        "name": "MHC Kenworth - St. Louis",
        "address": "3880 Elm Point Industrial Dr",
        "city": "St. Charles",
        "state": "MO",
        "zip_code": "63301",
        "latitude": 38.7912,
        "longitude": -90.5112,
        "phone": "(636) 946-4700",
        "website": "https://mhc.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth PremierCare Gold", "Gateway Hub"],
        "rating": 4.7,
        "review_count": 189,
        "hours": "Mon-Fri 7AM-6PM, Sat 8AM-12PM",
        "services_offered": ["CNG/LNG Service", "Fleet Support", "24 Service Bays"]
    },
    {
        "id": "mw-004",
        "name": "Kenworth of Wisconsin - Milwaukee",
        "address": "7500 N Teutonia Ave",
        "city": "Milwaukee",
        "state": "WI",
        "zip_code": "53209",
        "latitude": 43.1512,
        "longitude": -87.9612,
        "phone": "(414) 352-3300",
        "website": "https://www.kenworthwi.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth Dealer", "Wisconsin Hub"],
        "rating": 4.5,
        "review_count": 134,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Service", "Heavy Duty Repair", "Parts"]
    },
    {
        "id": "mw-005",
        "name": "Allstate Peterbilt - Omaha",
        "address": "4700 S 116th St",
        "city": "Omaha",
        "state": "NE",
        "zip_code": "68137",
        "latitude": 41.2012,
        "longitude": -96.0812,
        "phone": "(402) 896-2111",
        "website": "https://www.allstatepeterbilt.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["Peterbilt Certified", "I-80 Corridor"],
        "rating": 4.6,
        "review_count": 145,
        "hours": "Mon-Fri 7AM-6PM",
        "services_offered": ["CNG/LNG Service", "Natural Gas Repair", "Fleet Support"]
    },
    # ==================== ADDITIONAL US COVERAGE - MOUNTAIN/WEST ====================
    {
        "id": "west-001",
        "name": "Kenworth Sales Company - Billings",
        "address": "5548 King Ave E",
        "city": "Billings",
        "state": "MT",
        "zip_code": "59101",
        "latitude": 45.7712,
        "longitude": -108.4812,
        "phone": "(406) 252-6655",
        "website": "https://www.kenworthsalesco.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth Dealer", "Montana Hub"],
        "rating": 4.4,
        "review_count": 87,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Service", "Truck Repair", "Parts Sales"]
    },
    {
        "id": "west-002",
        "name": "Kenworth Sales Company - Cheyenne",
        "address": "4810 Campstool Rd",
        "city": "Cheyenne",
        "state": "WY",
        "zip_code": "82001",
        "latitude": 41.1012,
        "longitude": -104.7612,
        "phone": "(307) 634-4411",
        "website": "https://www.kenworthsalesco.com",
        "fuel_specializations": ["CNG", "LNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth Certified", "I-80/I-25 Hub"],
        "rating": 4.5,
        "review_count": 98,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG/LNG Service", "Fleet Maintenance", "Parts"]
    },
    {
        "id": "west-003",
        "name": "Papé Kenworth - Spokane",
        "address": "6111 E Broadway Ave",
        "city": "Spokane",
        "state": "WA",
        "zip_code": "99212",
        "latitude": 47.6512,
        "longitude": -117.3312,
        "phone": "(509) 535-1581",
        "website": "https://www.papekenworth.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth PremierCare Gold", "Inland Northwest Hub"],
        "rating": 4.6,
        "review_count": 134,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Service", "Heavy Duty Repair", "Fleet Support"]
    },
    {
        "id": "west-004",
        "name": "Papé Kenworth - Sacramento",
        "address": "4701 Roseville Rd",
        "city": "North Highlands",
        "state": "CA",
        "zip_code": "95660",
        "latitude": 38.6712,
        "longitude": -121.3812,
        "phone": "(916) 332-7702",
        "website": "https://www.papekenworth.com",
        "fuel_specializations": ["CNG", "Electric"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth Certified", "CARB Compliant", "EV Ready"],
        "rating": 4.5,
        "review_count": 156,
        "hours": "Mon-Fri 6AM-6PM",
        "services_offered": ["CNG Service", "EV Maintenance", "Fleet Support", "Parts Sales"]
    },
    {
        "id": "west-005",
        "name": "Papé Kenworth - Eugene",
        "address": "4035 W 11th Ave",
        "city": "Eugene",
        "state": "OR",
        "zip_code": "97402",
        "latitude": 44.0512,
        "longitude": -123.1312,
        "phone": "(541) 484-9421",
        "website": "https://www.papekenworth.com",
        "fuel_specializations": ["CNG"],
        "service_type": "In-Shop",
        "certifications": ["Kenworth Dealer", "I-5 Corridor"],
        "rating": 4.5,
        "review_count": 112,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["CNG Service", "Truck Repair", "Parts"]
    },
    # ==================== PROPANE/LPG SPECIALISTS ====================
    {
        "id": "lpg-001",
        "name": "Alliance AutoGas - Nashville",
        "address": "1410 Donelson Pike",
        "city": "Nashville",
        "state": "TN",
        "zip_code": "37217",
        "latitude": 36.1312,
        "longitude": -86.6812,
        "phone": "(615) 399-0900",
        "website": "https://www.allianceautogas.com",
        "fuel_specializations": ["LPG"],
        "service_type": "Both",
        "certifications": ["Propane Conversion Specialist", "PERC Certified"],
        "rating": 4.7,
        "review_count": 145,
        "hours": "Mon-Fri 8AM-5PM",
        "services_offered": ["Propane Conversions", "LPG System Service", "Fleet Conversion Programs"]
    },
    {
        "id": "lpg-002",
        "name": "Roush CleanTech Service Center - Livonia",
        "address": "12249 Levan Rd",
        "city": "Livonia",
        "state": "MI",
        "zip_code": "48150",
        "latitude": 42.3912,
        "longitude": -83.3912,
        "phone": "(800) 59-ROUSH",
        "website": "https://www.roushcleantech.com",
        "fuel_specializations": ["LPG", "CNG"],
        "service_type": "In-Shop",
        "certifications": ["Ford Authorized", "Propane/CNG Specialist"],
        "rating": 4.8,
        "review_count": 198,
        "hours": "Mon-Fri 7AM-6PM",
        "services_offered": ["Propane System Service", "CNG Repair", "Ford F-Series Conversions"]
    },
    # ==================== BIODIESEL SPECIALISTS ====================
    {
        "id": "bio-001",
        "name": "Optimus Technologies Service Center - Pittsburgh",
        "address": "4738 Centre Ave",
        "city": "Pittsburgh",
        "state": "PA",
        "zip_code": "15213",
        "latitude": 40.4512,
        "longitude": -79.9512,
        "phone": "(412) 345-8734",
        "website": "https://optimustec.com",
        "fuel_specializations": ["Biodiesel"],
        "service_type": "In-Shop",
        "certifications": ["Vector System Certified", "B100 Specialist"],
        "rating": 4.7,
        "review_count": 112,
        "hours": "Mon-Fri 8AM-5PM",
        "services_offered": ["Vector System Installation", "B100 System Service", "Fleet Consulting"]
    },
    # ==================== ADDITIONAL EV TRUCK SERVICE ====================
    {
        "id": "ev-003",
        "name": "Freightliner eCascadia Service - Ontario",
        "address": "15400 E Valley Blvd",
        "city": "City of Industry",
        "state": "CA",
        "zip_code": "91744",
        "latitude": 34.0112,
        "longitude": -117.9112,
        "phone": "(626) 964-9291",
        "website": "https://www.daimler-truck.com",
        "fuel_specializations": ["Electric"],
        "service_type": "In-Shop",
        "certifications": ["Freightliner eCascadia Certified", "High Voltage Trained", "SoCal Hub"],
        "rating": 4.6,
        "review_count": 134,
        "hours": "Mon-Fri 6AM-6PM",
        "services_offered": ["Electric Truck Service", "Battery Diagnostics", "Charging Infrastructure"]
    },
    {
        "id": "ev-004",
        "name": "Volvo Trucks Electric Service - San Leandro",
        "address": "14747 Catalina St",
        "city": "San Leandro",
        "state": "CA",
        "zip_code": "94577",
        "latitude": 37.7112,
        "longitude": -122.1512,
        "phone": "(510) 352-6600",
        "website": "https://www.volvotrucks.us",
        "fuel_specializations": ["Electric"],
        "service_type": "In-Shop",
        "certifications": ["Volvo VNR Electric Certified", "Zero Emission Hub"],
        "rating": 4.7,
        "review_count": 145,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["Electric Truck Repair", "Battery Service", "Fleet Electrification Support"]
    },
    # ==================== ADDITIONAL HYDROGEN SERVICE ====================
    {
        "id": "h2-003",
        "name": "Hyzon Motors Service Center - Rochester",
        "address": "1740 Scottsville Rd",
        "city": "Rochester",
        "state": "NY",
        "zip_code": "14623",
        "latitude": 43.0712,
        "longitude": -77.6512,
        "phone": "(585) 360-7550",
        "website": "https://www.hyzonmotors.com",
        "fuel_specializations": ["Hydrogen"],
        "service_type": "In-Shop",
        "certifications": ["Hyzon Authorized", "Fuel Cell Specialist", "Heavy Duty H2"],
        "rating": 4.5,
        "review_count": 67,
        "hours": "Mon-Fri 8AM-5PM",
        "services_offered": ["Hydrogen Fuel Cell Service", "Heavy Duty Truck Repair", "Training"]
    },
    {
        "id": "h2-004",
        "name": "Hyundai XCIENT Fuel Cell Service - Oakland",
        "address": "7677 Oakport St",
        "city": "Oakland",
        "state": "CA",
        "zip_code": "94621",
        "latitude": 37.7512,
        "longitude": -122.1912,
        "phone": "(510) 633-3355",
        "website": "https://www.hyundai.com/worldwide/en/eco/xcient-fuel-cell",
        "fuel_specializations": ["Hydrogen"],
        "service_type": "In-Shop",
        "certifications": ["Hyundai Certified", "XCIENT Specialist", "CARB Compliant"],
        "rating": 4.6,
        "review_count": 89,
        "hours": "Mon-Fri 7AM-5PM",
        "services_offered": ["XCIENT Fuel Cell Service", "Hydrogen System Repair", "Fleet Support"]
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
    city: Optional[str] = Query(None, description="Filter by city"),
    refresh: bool = Query(False, description="Force refresh from latest data")
):
    """Get all service centers with optional filters"""
    count = await db.service_centers.count_documents({})
    
    # Refresh data if count is less than expected or refresh is requested
    expected_count = len(MOCK_SERVICE_CENTERS)
    if count == 0 or count < expected_count or refresh:
        # Clear existing data and repopulate
        await db.service_centers.delete_many({})
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

# Haversine formula for distance calculation
def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points using Haversine formula. Returns distance in miles."""
    R = 3959  # Earth's radius in miles
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

class ServiceCenterWithDistance(BaseModel):
    id: str
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
    distance_miles: float
    distance_km: float

@api_router.get("/service-centers/nearby/location")
async def get_nearby_service_centers(
    latitude: float = Query(..., description="User's latitude"),
    longitude: float = Query(..., description="User's longitude"),
    radius: float = Query(25, description="Search radius in miles"),
    fuel_type: Optional[str] = Query(None, description="Filter by fuel specialization"),
    service_type: Optional[str] = Query(None, description="Filter by service type"),
    limit: int = Query(20, le=50, description="Maximum number of results")
):
    """Get service centers near a specific location, sorted by distance"""
    
    # Ensure service centers are in database
    count = await db.service_centers.count_documents({})
    if count < len(MOCK_SERVICE_CENTERS):
        await db.service_centers.delete_many({})
        for center in MOCK_SERVICE_CENTERS:
            await db.service_centers.insert_one(center)
    
    # Build query
    query = {}
    if fuel_type:
        query["fuel_specializations"] = fuel_type
    if service_type:
        query["service_type"] = service_type
    
    # Get all matching service centers
    centers = await db.service_centers.find(query).to_list(1000)
    
    # Calculate distances and filter by radius
    centers_with_distance = []
    for center in centers:
        center_lat = center.get("latitude", 0)
        center_lon = center.get("longitude", 0)
        
        if center_lat and center_lon:
            distance_miles = haversine_distance(latitude, longitude, center_lat, center_lon)
            
            if distance_miles <= radius:
                distance_km = distance_miles * 1.60934
                centers_with_distance.append({
                    **center,
                    "id": center.get("id", str(center.get("_id"))),
                    "distance_miles": round(distance_miles, 1),
                    "distance_km": round(distance_km, 1)
                })
    
    # Sort by distance
    centers_with_distance.sort(key=lambda x: x["distance_miles"])
    
    # Limit results
    centers_with_distance = centers_with_distance[:limit]
    
    # Remove MongoDB _id field if present
    for center in centers_with_distance:
        center.pop("_id", None)
    
    return centers_with_distance

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
