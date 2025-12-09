import express from "express";
import Point from "../models/Point.js";
import { runPython } from "../utils/runPython.js";
import { spawn } from "child_process";
import path from "path";
import { updateProgress } from "./progress.js";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const router = express.Router();

// HELPERS
function useValid(v) {
  return v !== undefined && v !== null && v !== "";
}

function validateFH(fh) {
  return Number.isInteger(fh) && fh >= 0 && fh <= 48;
}

function getModelRun(analDateString) {
  if (!analDateString) return null;

  const d = new Date(analDateString.replace(" ", "T") + "Z");
  const hour = d.getUTCHours();

  if (hour < 6) return "00z";
  if (hour < 12) return "06z";
  if (hour < 18) return "12z";
  return "18z";
}


// Correct forecast-hour conversion:
// FH = hours since analysis UTC time
function convertLocalToFH(dayOffset, hour) {
  if (dayOffset == null || hour == null) return null;

  return Number(dayOffset) * 24 + Number(hour);
}
async function runImporter() {
  const importScript = path.resolve(__dirname, "../json-to-mongodb.js");

  return new Promise((resolve, reject) => {
    const proc = spawn("node", [importScript]);

    proc.stdout.on("data", (d) => console.log(`[IMPORT] ${d}`));
    proc.stderr.on("data", (d) => console.error(`[IMPORT-ERR] ${d}`));

    proc.on("close", (code) => {
      code === 0 ? resolve() : reject(new Error("Importer failed"));
    });
  });
}

router.get("/", async (req, res) => {
  try {
    console.log("Request received:", req.url);

    const {
      lat,
      lon,
      dayOffset,
      hour,
      dayOffset_min,
      hour_min,
      dayOffset_max,
      hour_max,
    } = req.query;

    if (!lat || !lon)
      return res.status(400).json({ error: "lat and lon are required" });

    const LAT = Number(lat);
    const LON = Number(lon);

    let query = { lat: LAT, lon: LON };

    const sample = await Point.findOne({ lat: LAT, lon: LON });
    const analDateString = sample?.anal_date || null;

    if (!analDateString) {
      console.log("No anal_date in DB -> running importer");
      await runImporter();
    }

    // RANGE MODE
    if (
        useValid(dayOffset_min) &&
        useValid(hour_min) &&
        useValid(dayOffset_max) &&
        useValid(hour_max)
      ) {
        const fhMin = convertLocalToFH(Number(dayOffset_min), Number(hour_min));
        const fhMax = convertLocalToFH(Number(dayOffset_max), Number(hour_max));

        if (!validateFH(fhMin) || !validateFH(fhMax) || fhMin > fhMax) {
          return res.status(400).json({
            error: `Invalid range. FH must be between 0–23 and fhMin ≤ fhMax.`,
            fhMin,
            fhMax
          });
        }

        query.forecast_time = { $gte: fhMin, $lte: fhMax };
      }
    // SINGLE MODE
    else if (useValid(dayOffset) && useValid(hour)) {
          const fh = convertLocalToFH(Number(dayOffset), Number(hour));

          if (!validateFH(fh)) {
            return res.status(400).json({
              error: `Invalid forecast hour: ${fh}. Must be between 0 and 24.`,
              fh
            });
          }

          query.forecast_time = fh;
        }
    // NO TIME -> return FULL dataset
    else {
      console.log("NO TIME PROVIDED -> returning full dataset.");
    }

    console.log("QUERY ->", query);

    let points = await Point.find(query).sort({
      sitrep: 1,
      name: 1,
      forecast_time: 1,
    });

    if (points.length > 0) return res.json(
                            points.map(p => ({
                              ...p.toObject(),
                              model_run: getModelRun(p.anal_date)
                            }))
                          );

    // DB MISS -> regenerate data
    console.log("DB MISS -> running GRIB -> JSON");

    const gribScript = path.resolve(
      process.cwd(),
      "../../grib_to_json/grib_data_to_json.py"
    );

    updateProgress(0);
    await runPython(gribScript, [LAT, LON], (p) => updateProgress(p));
    updateProgress(100);

    // Import JSON -> DB
    await runImporter();

    // Try again
    points = await Point.find(query).sort({
      sitrep: 1,
      name: 1,
      forecast_time: 1,
    });

    if (!points.length)
      return res.status(500).json({ error: "No data after processing" });

    return res.json(
    points.map(p => ({
      ...p.toObject(),
      model_run: getModelRun(p.anal_date)
    }))
);
  } catch (err) {
    console.error("ROUTE ERROR:", err);
    return res.status(500).json({ error: "Server error" });
  }
});

export default router;