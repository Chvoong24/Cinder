import express from "express";
import Point from "../models/Point.js";

const router = express.Router();

router.get("/", async (req, res) => {
  const { lat, lon, fh, name } = req.query;

  if (!lat || !lon) {
    return res
      .status(400)
      .json({ error: "Missing lat or lon query parameters" });
  }

  try {
    const query = {
      lat: parseFloat(lat),
      lon: parseFloat(lon),
    };

    if (name) {
      query.name = name;
    }

    if (fh) {
      query.forecast_time = parseInt(fh);
    }

    const points = await Point.find(query);

    if (!points.length) {
      return res
        .status(404)
        .json({ error: "No data found for these coordinates" });
    }

    const grouped = {};
    points.forEach((point) => {
      const key = point.threshold;
      if (!grouped[key]) {
        grouped[key] = [];
      }
      grouped[key].push({
        value: point.value,
        forecast_time: point.forecast_time,
        step_length: point.step_length,
      });
    });

    res.json({
      location: {
        lat: parseFloat(lat),
        lon: parseFloat(lon),
        name: points[0]?.name || name || "Unknown",
      },
      forecast_hour: fh ? parseInt(fh) : null,
      data: grouped,
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

export default router;
