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

router.get("/", async (req, res) => {
  try {
    const { lat, lon, fh, fh_min, fh_max } = req.query;

    if (!lat || !lon) {
      return res.status(400).json({ error: "lat and lon are required" });
    }

    const LAT = Number(lat);
    const LON = Number(lon);

    const query = { lat: LAT, lon: LON };

    if (fh_min && fh_max) {
      query.forecast_time = { $gte: Number(fh_min), $lte: Number(fh_max) };
    } else if (fh) {
      query.forecast_time = Number(fh);
    }

    console.log("QUERY ->", query);

    let points = await Point.find(query).sort({ sitrep: 1 });

    if (points.length > 0) {
      console.log("DB HIT -> returning cached data");
      return res.json(points);
    }

    console.log("DB MISS -> running GRIB -> JSON script");

const gribScript = path.resolve(
  process.cwd(),"../../grib_to_json/grib_data_to_json.py");
    updateProgress(0)
    await runPython(gribScript,[LAT, LON],(p) => updateProgress(p));
    updateProgress(100)


    console.log("GRIB→JSON complete");

    const importScript = path.resolve(__dirname, "../json-to-mongodb.js");

    console.log("Running JSON→MongoDB importer...");

    await new Promise((resolve, reject) => {
      const proc = spawn("node", [importScript]);

      proc.stdout.on("data", d => console.log(`[IMPORT] ${d}`));
      proc.stderr.on("data", d => console.error(`[IMPORT-ERR] ${d}`));

      proc.on("close", code => {
        if (code === 0) resolve();
        else reject(new Error(`json-to-mongodb.js exited with code ${code}`));
      });
    });

    console.log("Import complete.");

    points = await Point.find(query).sort({ sitrep: 1 });

    if (!points || points.length === 0) {
      console.error("Still no DB results after scripts.");
      return res.status(500).json({ error: "something went wrong" });
    }

    console.log("DB REFRESH HIT → returning new data");
    return res.json(points);

  } catch (err) {
    console.error("ROUTE ERROR:", err);
    return res.status(500).json({ error: "Server error" });
  }
});

export default router;