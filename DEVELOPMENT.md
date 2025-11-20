# Development Process

Project: Cinder Weather App
Developer: Duy Huynh
Course: COMP333
Last Updated: November 4, 2025

## Overview

Cinder is a weather app that fetches and displays NOAA weather data for Connecticut cities. Built with MERN stack (MongoDB, Express, React, Node.js) plus Python scripts for data processing.

## Timeline

### Phase 1 - Backend API (October 2025)

Goal: Create an API to serve weather data to the frontend

The team already had Python scripts for fetching GRIB2 files but no way to serve this data to a web frontend. I needed to bridge Python data processing with a Node.js backend.

Solution:

- Built Express.js API with routes for weather queries
- Created Mongoose schema for MongoDB Atlas
- Wrote grib_to_mongodb.py to parse GRIB files and populate database

Tech used:

- Express.js for REST API
- MongoDB Atlas (cloud database)
- Mongoose for data modeling
- Python with pygrib for GRIB parsing

Testing:

- Postman for API endpoints
- MongoDB Atlas browser to verify data
- Full flow test: Python → MongoDB → Express → Frontend

### Phase 2 - Frontend (October 2025)

Goal: React UI to display weather data

Implementation:

- React components for search and weather display
- Fetch API calls to backend
- TypeScript interfaces for type safety
- CSS styling

Issues fixed:

- TypeScript errors (needed to define WeatherData interface)
- Search placeholder (changed to city names only, removed zipcode)
- API port conflict (switched from 5000 to 5001)

### Phase 3 - Data Processing Update (November 2025)

Team Feedback: "Use xarray and cartopy instead of manual lat/lon calculations"

Changes:

- Refactored grib_to_mongodb.py to use xarray with cfgrib engine
- Replaced manual distance calculations with xarray's .sel(method='nearest')
- Updated requirements.txt

Why this matters:

- xarray is industry standard for scientific data
- Built-in nearest-neighbor selection is more reliable
- Better memory efficiency

Team Feedback 2: "File naming should reflect weather model format"

Changes:

- Renamed function extract_location_from_filename() to get_target_locations()
- GRIB files keep original names (nbm.t12z.conus.f01.grib2, etc)
- Location data is extracted programmatically, not from filenames

### Phase 4 - JSON Export Feature (November 2025)

New Requirement: Integrate team's grib_to_json scripts

Process:

- Fetched latest from GitHub (git fetch, git pull)
- Checked out href_viewer branch
- Merged grib_to_json folder into my frontend branch

Integration:

- Updated .gitignore to exclude large GRIB files and JSON outputs
- Added new dependencies (orjson, matplotlib)
- Updated scripts to use test data (Hartford coordinates, href_download folder)
- Created README for grib_to_json

Testing:

- grib_data_to_json.py: 48 files in ~5 sec, 92KB JSON output
- forecast_json_parser.py: Successfully reads and parses JSON
- grib_graphical.py: Generates map visualization

## Technical Decisions

Why MongoDB?

- Flexible schema for varying weather data formats
- Cloud hosting (Atlas) for team access
- Easy Express integration through Mongoose

Why two approaches (MongoDB + JSON)?

- MongoDB: Powers the API for frontend queries
- JSON: Data analysis and static file sharing
- Different use cases, both useful

Why Connecticut cities?

- Team scope: 4 cities for initial testing
- Hartford, Middletown, Bridgeport, New Haven
- Easier to verify accuracy with limited locations

## Lessons Learned

Git Workflow:

- Don't clone multiple times - use git pull for updates
- Work on feature branch, merge from other branches as needed
- Use git checkout branch -- folder/ to grab specific files

Debugging:

- Read error messages carefully (MongoDB connection issues led to finding missing database name)
- Test each component separately (Python, MongoDB, API, Frontend)
- Use logging (memory monitoring helped identify performance issues)

Code Quality:

- Keep comments concise and natural
- Remove verbose AI-sounding docstrings
- Use team's code style (spaces in this project)
- .gitignore is critical - don't commit large data files

## Project Structure

```
Cinder/
├── backend/                    # Express API
│   ├── src/
│   │   ├── models/            # Mongoose schemas
│   │   ├── routes/            # API endpoints
│   │   ├── controllers/       # Request handlers
│   │   └── server.js
│   └── package.json
├── frontend/                   # React UI
│   ├── src/
│   │   ├── components/
│   │   └── App.tsx
│   └── package.json
├── Fetch_Scripts/              # Python data fetching
│   ├── get_href.py
│   ├── get_nbm.py
│   └── get_refs.py
├── grib_to_json/               # JSON export
│   ├── grib_data_to_json.py
│   ├── forecast_json_parser.py
│   └── grib_graphical.py
├── grib_to_mongodb.py          # GRIB → MongoDB
├── fetch_all.py
└── requirements.txt
```

## Future Work

- Add more cities or allow dynamic lat/lon input
- Automate daily GRIB file fetches and database updates
- Store historical data for forecast accuracy tracking
- Deploy to production (discuss cPanel vs modern platforms)

## References

- NOAA Weather Data: https://www.noaa.gov/
- MongoDB Atlas: https://www.mongodb.com/atlas
- pygrib: https://jswhit.github.io/pygrib/
- xarray: https://docs.xarray.dev/
- Cartopy: https://scitools.org.uk/cartopy/
