import express from "express";
import Point from "../models/Point.js";

const router = express.Router();

router.get("/", async (req, res) => {
  try {
    const { lat, lon, fh, fh_min, fh_max } = req.query;

    if (!lat || !lon) {
      return res.status(400).json({ error: "lat and lon are required" });
    }

    const query = {
      lat: Number(lat),
      lon: Number(lon)
    };


    if (
      fh_min !== undefined && fh_max !== undefined &&
      fh_min !== "" && fh_max !== ""
    ) {
      query.forecast_time = {
        $gte: Number(fh_min),
        $lte: Number(fh_max)
      };
    }
    else if (fh !== undefined && fh !== "") {
      query.forecast_time = Number(fh);
    }

    console.log("QUERY →", query);

    const points = await Point.find(query).sort({ forecast_time: 1 });

    if (!points || points.length === 0) {
      return res.status(404).json({ error: "No data found for these parameters" });
    }

    return res.json(points);

  } catch (err) {
    console.error("ROUTE ERROR:", err);
    res.status(500).json({ error: "Server error" });
  }
});

export default router;