import mongodb from "mongodb";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";

const { MongoClient } = mongodb;

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
