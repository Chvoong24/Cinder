import express from "express";
import dotenv from "dotenv";
import cors from "cors";
import dataRouter from "./routes/data.js";
import connectDB from "./config/db.js";

dotenv.config();
const app = express();

app.use(cors({ origin: "*" }));
app.use(express.json());

// log incoming requests
app.use((req, res, next) => {
  console.log(`Request: ${req.method} ${req.url}`);
  next();
});

// Routes
app.use("/api/data", dataRouter);

app.get("/", (req, res) => {
  res.send("Backend is running!");
});

// Mongo connection + start
const startServer = async () => {
  try {
    await connectDB();
    const PORT = process.env.PORT || 5050;
    app.listen(PORT, () => console.log(`🚀 Server running on port ${PORT}`));
  } catch (error) {
    console.error("Failed to start server:", error);
  }
};

startServer();
