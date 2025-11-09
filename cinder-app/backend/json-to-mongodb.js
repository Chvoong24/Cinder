import mongodb from 'mongodb';
import fs from 'fs'
import path from "path";
import { fileURLToPath } from "url";

const { MongoClient } = mongodb;

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const uri = 'mongodb://localhost:27017/ModelData';
const client = new MongoClient(uri);

async function run() {
    try {
        await client.connect();
        const database = client.db('ModelData');
        const collection = database.collection('points');

        const filePath = path.join(__dirname, "models", "data", "nbm06z_for_24.02619,-107.421197.json");
        const data = fs.readFileSync(filePath, "utf-8");

        // const points = JSON.parse(data)
        let points = JSON.parse(data);
        if (!Array.isArray(points)) {
            if (points.data && Array.isArray(points.data)) {
                points = points.data;
            } else {
                points = [points];
            }
        }
        const result = await collection.insertMany(points);
        console.log(`${result.insertedCount} documents were inserted`);

    } finally {
        await client.close();
    }
}

run().catch(console.dir);