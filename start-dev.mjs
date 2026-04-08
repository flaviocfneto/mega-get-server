#!/usr/bin/env node

import { spawn, spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const backendDir = path.join(__dirname, "api");
const frontendDir = path.join(__dirname, "web");

const apiHost = process.env.API_HOST || "127.0.0.1";
const apiPort = process.env.API_PORT || "8000";
const uiPort = process.env.UI_PORT || "5173";

const isWindows = process.platform === "win32";
const npmCmd = isWindows ? "npm.cmd" : "npm";

function commandExists(cmd, args = ["--version"]) {
  const result = spawnSync(cmd, args, { stdio: "ignore", shell: false });
  return result.status === 0;
}

function resolvePython() {
  const venvPythonUnix = path.join(__dirname, ".venv", "bin", "python");
  const venvPythonWin = path.join(__dirname, ".venv", "Scripts", "python.exe");
  if (existsSync(venvPythonUnix) && commandExists(venvPythonUnix)) return venvPythonUnix;
  if (existsSync(venvPythonWin) && commandExists(venvPythonWin)) return venvPythonWin;
  if (commandExists("python3")) return "python3";
  if (commandExists("python")) return "python";
  return null;
}

function runOrFail(cmd, args, options = {}) {
  const result = spawnSync(cmd, args, {
    stdio: "inherit",
    shell: false,
    ...options,
  });
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

function startChild(cmd, args, options = {}) {
  return spawn(cmd, args, {
    stdio: "inherit",
    shell: false,
    ...options,
  });
}

if (!existsSync(path.join(backendDir, "requirements.txt"))) {
  console.error(`Missing backend requirements file at ${path.join(backendDir, "requirements.txt")}`);
  process.exit(1);
}

const pythonCmd = resolvePython();
if (!pythonCmd) {
  console.error("python3/python is required but was not found.");
  process.exit(1);
}

if (!commandExists(npmCmd)) {
  console.error("npm is required but was not found.");
  console.error("Install Node.js from https://nodejs.org/ or via your package manager.");
  process.exit(1);
}

if (!existsSync(path.join(frontendDir, "node_modules"))) {
  console.log("web/node_modules not found. Running npm install...");
  runOrFail(npmCmd, ["install"], { cwd: frontendDir });
}

console.log(`Starting backend on http://${apiHost}:${apiPort} ...`);
const backend = startChild(
  pythonCmd,
  ["-m", "uvicorn", "api_main:app", "--host", apiHost, "--port", String(apiPort)],
  { cwd: backendDir }
);

console.log(`Starting frontend on http://localhost:${uiPort} ...`);
const frontend = startChild(npmCmd, ["run", "dev"], {
  cwd: frontendDir,
  env: {
    ...process.env,
    API_PROXY_TARGET: `http://${apiHost}:${apiPort}`,
    PORT: String(uiPort),
  },
});

console.log(`Backend PID: ${backend.pid}`);
console.log(`Frontend PID: ${frontend.pid}`);
console.log("Press Ctrl+C to stop both processes.");

let shuttingDown = false;
function shutdown(signal) {
  if (shuttingDown) return;
  shuttingDown = true;
  if (backend.pid) backend.kill(signal);
  if (frontend.pid) frontend.kill(signal);
}

process.on("SIGINT", () => shutdown("SIGINT"));
process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("exit", () => shutdown("SIGTERM"));

backend.on("exit", (code) => {
  if (!shuttingDown) {
    console.error(`Backend exited (${code ?? 1}), stopping frontend...`);
    shutdown("SIGTERM");
    process.exit(code ?? 1);
  }
});

frontend.on("exit", (code) => {
  if (!shuttingDown) {
    console.error(`Frontend exited (${code ?? 1}), stopping backend...`);
    shutdown("SIGTERM");
    process.exit(code ?? 1);
  }
});
