import fs from "fs";
import path from "path";
import { MongoClient } from "mongodb";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
 
const client = new MongoClient(process.env.MONGO_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
});

async function run() {
  try {
    
    await client.connect();
    console.log("[MONGO] Connected to MongoDB");

    
    const db = client.db("modelData");
    const collection = db.collection("points");

    
    const preferred = path.resolve(__dirname, "..", "cinder-app", "backend", "models", "data");
    const fallback = path.resolve(__dirname, "models", "data");

    let jsonDir;
    if (fs.existsSync(preferred) && fs.statSync(preferred).isDirectory()) {
      jsonDir = preferred;
    } else if (fs.existsSync(fallback) && fs.statSync(fallback).isDirectory()) {
      jsonDir = fallback;
    } else {
      
      const alt = path.resolve(__dirname, "models", "data");
      if (fs.existsSync(alt) && fs.statSync(alt).isDirectory()) {
        jsonDir = alt;
      } else {
        console.error("[IMPORT] JSON data directory not found.");
        console.error(`Searched: ${preferred}`);
        console.error(`Searched: ${fallback}`);
        console.error(`Searched: ${alt}`);
        return;
      }
    }

    console.log(`[IMPORT] Using JSON directory: ${jsonDir}`);

    const files = fs.readdirSync(jsonDir).filter((f) => f.endsWith(".json"));

    if (files.length === 0) {
      console.log("[IMPORT] No JSON files found.");
      return;
    }

    for (const file of files) {
      const fullPath = path.join(jsonDir, file);
      console.log(`[IMPORT] Reading ${file} ...`);

      let raw;
      try {
        raw = fs.readFileSync(fullPath, "utf8");
      } catch (err) {
        console.error(`[IMPORT-ERR] Failed to read ${file}:`, err);
        continue;
      }

      let json;
      try {
        json = JSON.parse(raw);
      } catch (err) {
        console.error(`[IMPORT-ERR] Failed to parse ${file} as JSON:`, err);
        continue;
      }

      const meta = json.metadata || {};
      const lat = meta.location?.lat;
      const lon = meta.location?.lon;

      if (typeof lat === "undefined" || typeof lon === "undefined") {
        console.warn(`[IMPORT] Skipping ${file} — metadata.location.lat/lon missing`);
        continue;
      }

      
      const docs = json.data.map(item => ({
        ...item,
        lat,
        lon,
        sitrep: meta.sitrep, 
        anal_date: meta.anal_date
      }));

      if (docs.length > 0) {
          try {
            const res = await collection.insertMany(docs, { ordered: false });
            console.log(`[IMPORT] Inserted ${res.insertedCount} docs from ${file}`);
          } catch (err) {

            if (err.code === 11000) {
              console.warn(
                `[IMPORT-WARN] Duplicate entries detected & skipped in ${file}`
              );
            } else {
              console.error(`[IMPORT-ERR] Error inserting docs from ${file}:`, err);
            }

          }
      } else {
        console.log(`[IMPORT] SKIPPED — no data inside ${file}`);
      }
    }
  } catch (err) {
    console.error("[IMPORT-ERR] Fatal:", err);
  } finally {
    try {
      await client.close();
      console.log("[MONGO] Connection closed. Import complete.");
    } catch (err) {
      console.error("[MONGO-ERR] Error closing client:", err);
    }
  }
}

run().catch((err) => {
  console.error("[IMPORT-ERR] Uncaught:", err);
});