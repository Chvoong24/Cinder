import mongodb from "mongodb";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";

const { MongoClient } = mongodb;

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const uri = 'mongodb://127.0.0.1:27017/ModelData'
const client = new MongoClient(uri);
export async function run() {
    try {
        const aggDB = client.db('filteredDB');
        const pipeline = [];
        pipeline.push({
            $match: {
            forecast_time: 1,
            },
        });
        for await (const document of aggregationResult) {
        console.log(document);
        }
    } finally {
        await client.close();
    }
}

run().catch(console.dir);