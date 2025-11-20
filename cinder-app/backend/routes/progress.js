import express from "express";
export const progressRouter = express.Router();

let currentProgress = 0;

progressRouter.get("/", (req, res) => {
  console.log("Client connected to progress stream");

  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");

  res.write(`data: ${currentProgress}\n\n`);

  const interval = setInterval(() => {
    res.write(`data: ${currentProgress}\n\n`);
  }, 500);

  req.on("close", () => {
    clearInterval(interval);
  });
});

export function updateProgress(p) {
  currentProgress = p;
}