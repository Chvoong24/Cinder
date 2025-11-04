# Development Process Documentation

**Project**: Cinder Weather Application  
**Developer**: Duy Huynh  
**Course**: COMP333  
**Last Updated**: November 4, 2025

---

## Project Overview

Cinder is a weather forecasting application that fetches, processes, and displays NOAA weather data for Connecticut cities. The project uses a MERN stack (MongoDB, Express.js, React, Node.js) with Python data processing scripts.

---

## Development Timeline

### Phase 1: Initial Setup & Backend API (October 2025)

**Goal**: Create an API to serve weather data from the existing Python data fetching scripts.

**Challenges Faced**:

- The team had Python scripts for fetching GRIB2 weather files, but no API to serve this data to a frontend
- Needed to bridge Python data processing with a Node.js backend

**Solution**:

1. Built Express.js API server with routes for weather data queries
2. Created Mongoose schema to store weather data in MongoDB Atlas
3. Developed `grib_to_mongodb.py` bridge script to parse GRIB files and populate database

**Technologies Used**:

- Express.js for REST API
- MongoDB Atlas for cloud database
- Mongoose for data modeling
- Python with pygrib for GRIB file parsing

**Testing Process**:

- Used Postman to test API endpoints
- Verified MongoDB connection through Atlas browser
- Tested data flow: Python → MongoDB → Express → Frontend

### Phase 2: Frontend Integration (October 2025)

**Goal**: Build React interface to display weather data.

**Implementation**:

- React components for search and weather display
- Fetch API calls to Express backend
- TypeScript interfaces for type safety
- CSS styling for modern UI

**Iterations**:

- Fixed TypeScript errors by properly typing state variables
- Updated search placeholder to match API capabilities (city names only, not zipcodes)
- Adjusted API port to 5001 to resolve conflicts

### Phase 3: Data Processing Refinement (November 2025)

**Team Feedback #1**: "Use xarray and cartopy libraries instead of manual lat/lon calculations"

**Changes Made**:

1. Refactored `grib_to_mongodb.py` to use xarray with cfgrib engine
2. Replaced manual distance calculations with xarray's `.sel(method='nearest')`
3. Updated dependencies in `requirements.txt`

**Why This Matters**:

- xarray is industry-standard for scientific data
- Built-in nearest-neighbor selection is more reliable
- Better memory efficiency for large datasets

**Team Feedback #2**: "File naming should reflect weather model format, not locations"

**Changes Made**:

- Renamed function from `extract_location_from_filename()` to `get_target_locations()`
- Clarified that GRIB files keep original names (e.g., `nbm.t12z.conus.f01.grib2`)
- Files are not renamed by location - location data is extracted programmatically

### Phase 4: JSON Export Feature (November 2025)

**New Requirement**: Integrate team's `grib_to_json` scripts for data export.

**Process**:

1. Fetched latest updates from GitHub using `git fetch` and `git pull`
2. Checked out `href_viewer` branch to review team's work
3. Merged `grib_to_json` folder into my `frontend` branch using `git checkout href_viewer -- grib_to_json/`

**Integration Steps**:

- Updated `.gitignore` to exclude large GRIB data files and generated JSON
- Added new dependencies (orjson, matplotlib) to `requirements.txt`
- Updated scripts to use test data (Hartford coordinates, href_download folder)
- Created README for the grib_to_json folder

**Testing Each Script**:

1. `grib_data_to_json.py`:

   - Processes 48 GRIB files using 8 threads
   - Generates JSON output in ~5 seconds
   - Peak memory usage: ~216 MB
   - Output: 92KB JSON file

2. `forecast_json_parser.py`:

   - Successfully reads and parses generated JSON
   - Displays metadata and sample data records

3. `grib_graphical.py`:
   - Fixed missing file reference
   - Generates matplotlib map visualization
   - Shows weather probability data with cartopy geographic features

---

## Technical Decisions

### Why MongoDB?

- Flexible schema for varying weather data formats
- Cloud-hosted (Atlas) for team accessibility
- Easy integration with Express.js through Mongoose

### Why Two Approaches (MongoDB + JSON)?

- **MongoDB approach**: Powers the API for frontend queries
- **JSON approach**: Enables data analysis and sharing static files
- Both serve different use cases and complement each other

### Why Connecticut Cities?

- Team scope: Focus on 4 cities for initial testing
- Cities: Hartford, Middletown, Bridgeport, New Haven
- Easier to verify data accuracy with limited locations

---

## Lessons Learned

### Git Workflow

- **Don't clone multiple times**: Use `git pull` to get updates
- **Branch strategy**: Work on feature branch (frontend), merge from other branches as needed
- **Selective merging**: Use `git checkout branch -- folder/` to grab specific files

### Debugging Process

1. **Check error messages carefully**: MongoDB connection errors led to discovering missing database name in connection string
2. **Test incrementally**: Test each component (Python script, MongoDB, API, Frontend) separately
3. **Use logging**: Memory monitoring in scripts helped identify performance issues

### Code Quality

- Keep comments concise and natural
- Remove verbose docstrings that sound AI-generated
- Use team's existing code style (spaces, not tabs in this case)
- `.gitignore` is critical - don't commit large data files or generated outputs

---

## Current Project Structure

```
Cinder/
├── backend/                    # Express.js API
│   ├── src/
│   │   ├── models/            # Mongoose schemas
│   │   ├── routes/            # API endpoints
│   │   ├── controllers/       # Request handlers
│   │   └── server.js          # Entry point
│   └── package.json
├── frontend/                   # React UI
│   ├── src/
│   │   ├── components/        # React components
│   │   └── App.tsx            # Main app
│   └── package.json
├── Fetch_Scripts/              # Python data fetching
│   ├── get_href.py
│   ├── get_nbm.py
│   └── get_refs.py
├── grib_to_json/               # JSON export tools
│   ├── grib_data_to_json.py   # GRIB → JSON converter
│   ├── forecast_json_parser.py # JSON reader
│   ├── grib_graphical.py      # Visualization
│   └── README.md
├── grib_to_mongodb.py          # GRIB → MongoDB bridge
├── fetch_all.py                # Run all fetching scripts
└── requirements.txt            # Python dependencies
```

---

## Future Improvements

1. **Expand location coverage**: Add more Connecticut cities or allow dynamic lat/lon input
2. **Automate data updates**: Schedule daily GRIB file fetches and database updates
3. **Historical data**: Store and display forecast accuracy over time
4. **Deployment**: Deploy to production using cPanel or modern platforms (Vercel/Render)

---

## References

- NOAA Weather Data: https://www.noaa.gov/
- MongoDB Atlas: https://www.mongodb.com/atlas
- pygrib Documentation: https://jswhit.github.io/pygrib/
- xarray Documentation: https://docs.xarray.dev/
- Cartopy Documentation: https://scitools.org.uk/cartopy/
