# FuelPoint Navigator - Complete Code Archive
# Generated: February 24, 2025
# Version: 1.0.0 (Beta Ready)

================================================================================
# APPLICATION OVERVIEW
================================================================================

FuelPoint Navigator is a cross-platform mobile application for the Alternative 
Fuels market, helping truckers and fleet managers find fuel stations, service 
centers, and plan routes with optimal refueling stops.

## Tech Stack
- Frontend: React Native with Expo (SDK 54)
- Backend: Python FastAPI
- Database: MongoDB
- Maps: Leaflet.js (web + mobile via WebView)
- API: AFDC/NREL for live fuel station data

## Key Features
1. Live Fuel Station Data (AFDC API integration)
2. 118 Service Centers (US + Canada coverage)
3. Find Nearest with Geolocation
4. Turn-by-Turn Navigation (Google Maps, Apple Maps, Waze)
5. Route Planner with Optimal Fuel Stops
6. Offline Mode for areas with poor connectivity
7. Regulations & Standards Library
8. Certified Inspector Directory
9. Fuel System Providers Directory
10. User Feedback/Support System

================================================================================
# DIRECTORY STRUCTURE
================================================================================

/app
├── backend/
│   ├── .env                    # Environment variables (MongoDB, API keys)
│   ├── server.py               # Main FastAPI application (3700+ lines)
│   ├── requirements.txt        # Python dependencies
│   └── tests/
│       └── test_service_centers.py
│
├── frontend/
│   ├── .env                    # Expo environment variables
│   ├── app.json                # Expo configuration
│   ├── package.json            # Node dependencies
│   ├── tsconfig.json           # TypeScript configuration
│   │
│   ├── app/                    # Expo Router pages (file-based routing)
│   │   ├── _layout.tsx         # Main 6-tab navigation
│   │   ├── +html.tsx           # Custom HTML for Leaflet CSS (web)
│   │   ├── index.tsx           # Stations screen (home)
│   │   ├── regulations.tsx     # Regulations library
│   │   ├── services.tsx        # Service centers directory
│   │   ├── inspectors.tsx      # Certified inspectors
│   │   ├── providers.tsx       # Fuel system providers
│   │   ├── profile.tsx         # User profile + Offline settings
│   │   ├── station/[id].tsx    # Station detail page
│   │   ├── service/[id].tsx    # Service center detail
│   │   ├── regulation/[id].tsx # Regulation detail
│   │   ├── inspector/[id].tsx  # Inspector detail
│   │   └── provider/[id].tsx   # Provider detail
│   │
│   └── src/
│       ├── components/         # Reusable UI components
│       │   ├── FilterModal.tsx
│       │   ├── FuelTypeChip.tsx
│       │   ├── LoadingSpinner.tsx
│       │   ├── MapWrapper.tsx          # Cross-platform map (Leaflet)
│       │   ├── NavigationButton.tsx    # Turn-by-turn navigation
│       │   ├── OfflineBanner.tsx       # Offline status indicator
│       │   ├── OfflineSettings.tsx     # Offline data management
│       │   ├── RatingStars.tsx
│       │   ├── RoutePlannerModal.tsx   # Route planning UI
│       │   ├── ServicesFilterModal.tsx
│       │   ├── StationCard.tsx
│       │   └── StationsFilterModal.tsx
│       │
│       ├── constants/
│       │   └── index.ts        # Colors, fuel types, etc.
│       │
│       ├── hooks/
│       │   ├── useLocation.ts      # Geolocation hook
│       │   └── useNetworkStatus.ts # Network detection hook
│       │
│       ├── services/
│       │   ├── api.ts              # API client (axios)
│       │   └── offlineCache.ts     # AsyncStorage caching
│       │
│       ├── types/
│       │   └── index.ts        # TypeScript interfaces
│       │
│       └── utils/
│           └── navigation.ts   # Map app deep linking
│
└── memory/
    └── PRD.md                  # Product Requirements Document

================================================================================
# API ENDPOINTS
================================================================================

Base URL: https://fuel-hub-app.preview.emergentagent.com/api

## Stations
GET  /stations                    - Live fuel stations (AFDC API)
GET  /stations/{id}               - Station details

## Service Centers
GET  /service-centers             - All 118 service centers
GET  /service-centers/{id}        - Service center details
GET  /service-centers/nearby/location?lat=X&lng=Y&radius=25
                                  - Nearby service centers with distance

## Regulations
GET  /regulations                 - All regulations
GET  /regulations/{id}            - Regulation details

## Inspectors
GET  /inspectors                  - All inspectors
GET  /inspectors/{id}             - Inspector details
GET  /inspector-lookup-links      - External lookup URLs (AFVi, CSA)

## Providers
GET  /providers                   - Fuel system providers
GET  /providers/{id}              - Provider details

## Route Planner
POST /route-planner               - Plan route with fuel stops
GET  /route-planner/fuel-prices   - Current fuel price estimates

## User
GET  /profile                     - User profile
PUT  /profile                     - Update profile
POST /feedback                    - Submit feedback

================================================================================
# ENVIRONMENT VARIABLES
================================================================================

## Backend (.env)
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
NREL_API_KEY="your-afdc-api-key"

## Frontend (.env)
EXPO_TUNNEL_SUBDOMAIN=fuel-hub-app
EXPO_PACKAGER_HOSTNAME=https://your-app.preview.emergentagent.com
EXPO_PUBLIC_BACKEND_URL=https://your-app.preview.emergentagent.com
EXPO_USE_FAST_RESOLVER="1"

================================================================================
# DEPLOYMENT INSTRUCTIONS
================================================================================

## 1. Deploy Backend (Emergent Platform)
   - Click "Deploy" button in Emergent interface
   - Wait 10-15 minutes for deployment
   - Note the production URL

## 2. Update Frontend for Production
   - Update EXPO_PUBLIC_BACKEND_URL with production URL
   - Rebuild the app

## 3. Distribute Mobile App

### Option A: Expo Go (Quick Testing)
   expo publish
   # Share the published link with testers

### Option B: Standalone Apps (Production)
   # iOS (requires Apple Developer account)
   eas build --platform ios
   # Upload to TestFlight

   # Android
   eas build --platform android
   # Upload to Google Play or distribute APK directly

================================================================================
# KEY DEPENDENCIES
================================================================================

## Backend (Python)
fastapi==0.109.0
uvicorn==0.27.0
motor==3.3.2
httpx==0.26.0
pydantic==2.5.3
python-dotenv==1.0.0

## Frontend (Node)
expo: ~54.0.35
react-native: ~0.79.0
expo-router: ~5.0.4
expo-location: ~18.0.6
@react-native-async-storage/async-storage: ~2.1.0
@react-native-community/netinfo: ^12.0.1
react-native-webview: ^13.16.0
axios: ^1.6.5

================================================================================
# DATA MODELS
================================================================================

## FuelStation (from AFDC API)
{
  id: string
  name: string
  street_address: string
  city: string
  state: string
  zip: string
  latitude: number
  longitude: number
  fuel_type: string
  status: string
  access_hours: string
  phone: string
}

## ServiceCenter
{
  id: string
  name: string
  address: string
  city: string
  state: string
  zip_code: string
  latitude: number
  longitude: number
  phone: string
  website: string
  fuel_specializations: string[]
  service_type: "In-Shop" | "Mobile" | "Both"
  certifications: string[]
  rating: number
  review_count: number
  hours: string
  services_offered: string[]
}

## RoutePlan
{
  origin: RouteLocation
  destination: RouteLocation
  total_distance_miles: number
  total_distance_km: number
  estimated_total_time_hours: number
  fuel_stops: FuelStop[]
  segments: RouteSegment[]
  total_fuel_needed_dge: number
  estimated_fuel_cost: number
  vehicle_settings: VehicleSettings
  warnings: string[]
}

================================================================================
# IMPORTANT NOTES
================================================================================

1. DO NOT use react-native-maps - it crashes Expo Go. Use the WebView+Leaflet
   solution in MapWrapper.tsx instead.

2. Canadian provinces are supported (AB, BC, ON, QC) in filters.

3. The AFDC API key is required for live station data. Get one free at:
   https://developer.nrel.gov/signup/

4. Offline mode caches data for 24 hours in AsyncStorage.

5. Route planner uses Haversine formula for distance calculation.
   For production, consider integrating Google Directions API for
   actual road distances.

================================================================================
# CONTACT & SUPPORT
================================================================================

For questions about this codebase, refer to:
- /app/memory/PRD.md for full product requirements
- /app/test_reports/ for testing results

================================================================================
# END OF ARCHIVE
================================================================================
