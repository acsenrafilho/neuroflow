import { cpSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const dist = join(root, "dist");
const assetsDist = join(dist, "assets");

mkdirSync(assetsDist, { recursive: true });
cpSync(join(root, "src/pages"), dist, { recursive: true });
const jsDist = join(dist, "js");
mkdirSync(jsDist, { recursive: true });
cpSync(join(root, "src/js"), jsDist, { recursive: true });
const repoAssets = join(root, "..", "assets", "images");
cpSync(join(repoAssets, "neuroflow_logo.svg"), join(assetsDist, "neuroflow_logo.svg"));
cpSync(join(repoAssets, "neuroflow_logo.png"), join(assetsDist, "neuroflow_logo.png"));
