# Team Q&A - Notes for Discussions

## General Questions

Q: What did you work on?
A: Built the Express API backend to serve weather data, created React UI for displaying forecasts, and wrote grib_to_mongodb.py to parse GRIB files into MongoDB. Also integrated the team's grib_to_json tools and documented everything.

Q: Why create grib_to_mongodb.py instead of using grib_to_json?
A: Different purposes. grib_to_json creates static JSON files for analysis. grib_to_mongodb feeds the API so the frontend can query data dynamically. Need both approaches.

## Backend & API

Q: Why Express instead of Flask?
A: More familiar with MERN stack, team agreed we just needed one API for displaying data. Express works well with MongoDB through Mongoose and easy to test with Postman.

Q: Why MongoDB Atlas?
A: Cloud hosting means whole team can access it without running local databases. Connection string is in .env file.

Q: Why only one API endpoint?
A: Team decision - just need /api/weather/current/:locationName for now. Can add more later if needed.

Q: What if someone searches for a city we don't have?
A: API returns empty, frontend shows "Failed to fetch data". Currently only have 4 CT cities as test data.

## Data Processing

Q: Why switch from pygrib to xarray?
A: Team requested it. xarray has built-in .sel(method='nearest') for finding grid points, more reliable than manual calculations. It's the industry standard.

Q: How does grib_to_mongodb.py work?
A: Reads GRIB2 files, extracts weather parameters (temp, precip, wind, humidity, pressure) for our 4 CT cities using nearest-neighbor selection, inserts into MongoDB with location, timestamp, and forecast data.

Q: Why are some values null?
A: HREF probability files don't have standard weather metrics - they're probability forecasts. Need NBM or BLEND files for actual weather data.

Q: How do you handle location-specific data?
A: Defined 4 CT cities with lat/lon coordinates. For each GRIB file, use xarray to find nearest grid point and extract the value.

## Frontend

Q: Why can't we search by zipcode?
A: Database stores city names, not zipcodes. Would need a zipcode-to-city mapping. Search placeholder says "city name" to guide users.

Q: Why React?
A: Modern standard, component-based architecture is maintainable, familiar with MERN stack.

Q: Why TypeScript?
A: Already set up. Catches errors at compile-time which helps in team projects.

## Git & Workflow

Q: Why so many commits?
A: Each commit = specific change or fix. Easier to track progress and roll back if needed.

Q: Why frontend branch instead of main?
A: Team branching strategy - feature branches → Dev → main.

Q: How did you integrate grib_to_json from href_viewer?
A: Used git checkout href_viewer -- grib_to_json/ to grab that folder, then updated scripts to use our test data.

## Testing & Debugging

Q: How did you test the API?
A: Postman for endpoints, MongoDB Atlas browser for data, React frontend for end-to-end. Checked logs for debugging.

Q: Main issues you ran into?
A: MongoDB connection (needed database name in connection string), port conflicts (5000 → 5001), TypeScript errors (needed interfaces), HREF files don't have complete data.

Q: Why does visualization look sparse?
A: Test data is HREF probability files with limited coverage. Original visualization used BLEND file with full data. Code works correctly, just different data.

## Dependencies

Q: Why so many Python packages?
A: xarray/cfgrib/pygrib for GRIB processing, cartopy/matplotlib for maps, pymongo for MongoDB, orjson for JSON, psutil for memory monitoring, python-dotenv for env vars.

Q: Why both xarray and pygrib?
A: grib_to_mongodb uses xarray (team requested). grib_to_json uses pygrib (team's original code). Both work, different approaches.

## Deployment

Q: Can we use university cPanel?
A: Frontend can go on cPanel after building, but Express backend needs Node.js support. Most cPanel doesn't handle Node well. Options: frontend on cPanel + backend on Render, or everything on Vercel + Render.

Q: What's needed before deployment?
A: Build React (npm run build), set environment variables, ensure MongoDB Atlas allows hosting IPs, update API URL in frontend, test with production data.

## Documentation

Q: What's DEVELOPMENT.md for?
A: Professor wanted process documentation. Shows timeline, challenges, technical decisions, lessons learned, debugging process.

Q: Why create grib_to_json/README.md?
A: Explains how to use the scripts - requirements, data location, dependencies. Makes it easier for team.

## Future Work

Q: What's next?
A: More cities or dynamic lat/lon, get NBM/BLEND files for complete data, automate daily fetching, historical data tracking, better UI.

Q: Can we extend to other states?
A: Yes, just add locations to get_target_locations() with their coordinates. GRIB files cover all of CONUS.

## Key Points

- Followed team feedback (xarray, file naming)
- Tested everything with available data
- Documented the process
- Made practical decisions (MERN stack, cloud DB)
- Code is clean and maintainable
- Understand limitations (HREF vs BLEND data)

If you don't know something: "Let me check that" or "We should discuss as team" - don't make up answers.
