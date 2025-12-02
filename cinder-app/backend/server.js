import express from "express";
import dotenv from "dotenv";
import cors from "cors";
import dataRouter from "./routes/data.js";
import connectDB from "./config/db.js";
import { progressRouter } from "./routes/progress.js";

dotenv.config();
const app = express();
app.use("/progress", progressRouter);

app.use(cors({ origin: process.env.CLIEANT_URL, credentials: true}));
app.use(express.json());

app.use((req, res, next) => {
  console.log(`Request received: ${req.method} ${req.url}`);
  next();
});

// Routes
app.use("/api/data", dataRouter);

app.get("/", (req, res) => {
  console.log("Root route hit");
  res.send("Backend is running!");
});

const startServer = async () => {
  try {
    await connectDB();
    const PORT = process.env.PORT || 5050;
    app.listen(PORT, "0.0.0.0", () => console.log(`Server running on port ${PORT}`));
  } catch (error) {
    console.error("Failed to start server:", error);
  }
};

startServer();