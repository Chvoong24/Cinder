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

    const dirPath = path.join(__dirname, "models", "data");
    const files = fs.readdirSync(dirPath);

    for (const file of files) {
      const filePath = path.join(dirPath, file);
      const raw = fs.readFileSync(filePath, "utf-8");
      const parsed = JSON.parse(raw);

      const lat = parsed.metadata?.location?.lat;
      const lon = parsed.metadata?.location?.lon;

      if (!lat || !lon) {
        console.warn(`Skipping ${file}: missing lat/lon`);
        continue;
      }

      const points = parsed.data.map((entry) => ({
        ...entry,
        lat,
        lon,
      }));

      const result = await collection.insertMany(points);
      console.log(`Inserted ${result.insertedCount} docs from ${file}`);
    }
  } catch (err) {
    console.error("Error:", err);
  } finally {
    await client.close();
  }
}

run().catch(console.dir);