import express from "express";
import Point from "../models/Point.js";

const router = express.Router();

router.get("/", async (req, res) => {
  const { lat, lon } = req.query; 

  if (!lat || !lon) {
    return res.status(400).json({ error: "Missing lat or lon query parameters" });
  }

  try {
    const points = await Point.find({
      lat: parseFloat(lat),
      lon: parseFloat(lon),
      
    });

    if (!points.length) {
      return res.status(404).json({ error: "No data found for these coordinates" });
    }

    res.json(points);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

export default router;