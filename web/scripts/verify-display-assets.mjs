import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const webRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const sourceDir = path.resolve(webRoot, "..", "data", "processed");
const runtimeDir = path.resolve(webRoot, "public", "data");
const assets = [
  "landmarks_demo.geojson",
  "timeline_demo_sizheng.json",
];

for (const asset of assets) {
  const sourcePath = path.join(sourceDir, asset);
  const runtimePath = path.join(runtimeDir, asset);

  if (!fs.existsSync(sourcePath)) {
    throw new Error(`Display asset source not found: ${sourcePath}`);
  }
  if (!fs.existsSync(runtimePath)) {
    throw new Error(`Runtime copy not found: ${runtimePath}`);
  }

  const sourceBytes = fs.readFileSync(sourcePath);
  const runtimeBytes = fs.readFileSync(runtimePath);

  if (!sourceBytes.equals(runtimeBytes)) {
    throw new Error(`Runtime copy differs from source: ${asset}`);
  }

  console.log(`verified ${asset}`);
}