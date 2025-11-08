import express from "express";
import mongoose from "mongoose";
import cors from "cors";
import dotenv from "dotenv";
import postsRouter from "./routes/posts.js";

dotenv.config();
const app = express();

app.use(cors());
app.use(express.json());
app.use("/posts", postsRouter);

// Sample route
app.get("/", (req, res) => {
  res.send("Backend is running!");
});

// Connect to MongoDB
mongoose.connect(process.env.MONGO_URI)
  .then(() => console.log("MongoDB connected"))
  .catch((err) => console.error(err));

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`🚀 Server running on port ${PORT}`));