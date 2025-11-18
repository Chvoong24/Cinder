import { spawn } from "child_process";

export function runPython(scriptPath, args = []) {
  return new Promise((resolve, reject) => {
    const py = spawn("python3", [scriptPath, ...args], {
      stdio: ["ignore", "pipe", "pipe"]
    });

    let stdoutData = "";
    let stderrData = "";

    py.stdout.on("data", (data) => {
      stdoutData += data.toString();
      console.log("[PYTHON]", data.toString());
    });

    py.stderr.on("data", (data) => {
      stderrData += data.toString();
      console.log("[PYTHON-ERR]", data.toString());
    });

    py.on("close", (code) => {
      if (code !== 0) {
        return reject(
          new Error(`Python script exited with code ${code}\n${stderrData}`)
        );
      }

      resolve(stdoutData);
    });
  });
}