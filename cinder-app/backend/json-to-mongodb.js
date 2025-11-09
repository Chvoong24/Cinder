import mongodb from "mongodb";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const { MongoClient } = mongodb;

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const uri = "mongodb://localhost:27017/ModelData";
const client = new MongoClient(uri);

async function run() {
  try {
    await client.connect();
    const database = client.db("ModelData");
    const collection = database.collection("points");

    const filePath = path.join(
      __dirname,
      "models",
      "data",
      "nbm06z_for_24.02619,-107.421197.json"
    );
    const data = fs.readFileSync(filePath, "utf-8");

    let parsed = JSON.parse(data);

    // ✅ Extract lat/lon from metadata
    const lat = parsed.metadata?.location?.lat;
    const lon = parsed.metadata?.location?.lon;

    if (!lat || !lon) {
      throw new Error("Missing lat/lon in metadata!");
    }

    // ✅ Attach lat/lon to each data entry
    let points = parsed.data.map((entry) => ({
      ...entry,
      lat,
      lon,
    }));

    const result = await collection.insertMany(points);
    console.log(`✅ Inserted ${result.insertedCount} documents with lat/lon`);
  } catch (err) {
    console.error("❌ Error:", err);
  } finally {
    await client.close();
  }
}

run().catch(console.dir);