# FuelPoint Navigator - Product Requirements Document

## Original Problem Statement
A mobile app named "FuelPoint Navigator" for the Alternative Fuels market with the following features:
1. **Fuel Station Locator:** Map and list view of nearby fuel stations
2. **Regulations & Standards Library:** A searchable library of regulations
3. **Service & Inspection Directory:** A directory of certified service centers
4. **Certified Inspector Finder:** A directory to find certified inspectors
5. **Profile Screen:** A basic user profile section

## User Personas
- Fleet managers needing alternative fuel infrastructure information
- Commercial truck operators using CNG/LNG/Electric/Hydrogen vehicles
- Service technicians and inspectors in the alternative fuels industry

## Core Requirements
- Cross-platform mobile app (iOS/Android via Expo)
- Web application support
- Real-time fuel station data via AFDC API
- Comprehensive service center directory
- Interactive maps on web and mobile

## What's Been Implemented

### Phase 1: Core MVP (Completed)
- Six-tab navigation: Stations, Regulations, Services, Inspectors, Providers, Profile
- Live fuel station data from AFDC API
- Basic regulations, inspectors, and providers data

### Phase 2: Enhanced Features (Completed - Feb 2025)
- **Interactive Maps:** Leaflet.js on web, WebView+Leaflet on mobile
- **Support Center:** User feedback form in Profile tab
- **Advanced Filtering:** Modal-based filters for Stations and Services tabs
- **New Providers Section:** 15 curated fuel system providers

### Phase 3: Data Expansion (Completed - Feb 23, 2025)
- **Comprehensive Service Center Database:**
  - Expanded from 5 to 118 service centers
  - Coverage: 40 US states and Canadian provinces
  - 12 Canadian locations (AB, BC, ON, QC)
  - Networks: Rush Truck Centers, Cummins, Kenworth/MHC, Velocity, Peterbilt, and more
  - Fuel types: CNG (108), LNG (46), Electric (17), Hydrogen (9), LPG (2), Biodiesel (1)
- **Canadian Province Support:** Filter dropdowns now include Canadian provinces

### Phase 4: Geolocation Feature (Completed - Feb 23, 2025)
- **"Find Nearest" Feature:**
  - Added to both Stations and Services tabs
  - Uses device geolocation (expo-location on mobile, browser geolocation on web)
  - 25-mile (40 km) default search radius
  - Distance display in both miles and kilometers
  - Distance badges on service center cards when in nearby mode
  - Backend endpoint: `GET /api/service-centers/nearby/location`
  - Haversine formula for accurate distance calculation

## Tech Stack
- **Frontend:** React Native, Expo, Expo Router, TypeScript
- **Backend:** Python, FastAPI, Pydantic
- **Database:** MongoDB (with in-memory mock data)
- **Mapping:** Leaflet.js (web), WebView+Leaflet (mobile)
- **API:** AFDC/NREL API for live fuel station data

## API Endpoints
- `GET /api/stations` - Live AFDC fuel station data
- `GET /api/regulations` - Regulations library
- `GET /api/service-centers` - 118 service centers (filterable)
- `GET /api/inspectors` - Certified inspectors
- `GET /api/providers` - Fuel system providers
- `POST /api/feedback` - User feedback submission

## Prioritized Backlog

### P0 - Next Up
- **Safety Bulletins Feature:** New tab with safety bulletins content

### P1 - High Priority
- Technical Documentation Library
- Industry News Feed

### P2 - Medium Priority
- Events Calendar
- Migrate mock data to MongoDB persistence

### P3 - Future
- User Accounts & Authentication
- Fleet Management Features
- Push Notifications

## Known Constraints
- Do NOT use `react-native-maps` (causes Expo Go crashes)
- Use WebView+Leaflet for mobile maps
- Canadian provinces use standard 2-letter codes (AB, BC, ON, QC, etc.)

## Third-Party Integrations
- **AFDC API:** Real-time fuel station data (API Key in backend/.env)
- **Leaflet.js:** Map rendering (via CDN)

## Testing Status
- Backend: 24 pytest tests passing
- Frontend: Verified via screenshots and testing agent
- Service center filtering: Verified for state, fuel type, service type
