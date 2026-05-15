import { cpSync, mkdirSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const dist = join(root, "dist");
const assetsDist = join(dist, "assets");

mkdirSync(assetsDist, { recursive: true });
cpSync(join(root, "src/pages"), dist, { recursive: true });
cpSync(
  join(root, "..", "assets", "images", "neuroflow_logo.svg"),
  join(assetsDist, "neuroflow_logo.svg"),
);
