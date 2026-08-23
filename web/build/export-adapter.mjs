// Build adapter for Next.js static exports.
//
// Works around vercel/next.js#85374: with output:"export" the exporter writes
// per-segment RSC payloads as nested files (e.g.
// recommend/__next.recommend/__PAGE__.txt) while the client router requests a
// flat dot-separated name (recommend/__next.recommend.__PAGE__.txt). On some
// platforms (observed on Windows) these diverge, producing 404s during link
// prefetch/navigation. This adapter renames the exported files to the flat
// form the client expects. Remove once the upstream fix ships in a stable
// release and this project upgrades past it.

import fs from "node:fs/promises";
import path from "node:path";

function flattenRscPath(filePath) {
  const parts = filePath.split(path.sep);
  const start = parts.findIndex((part) => part.startsWith("__next."));
  if (start === -1 || start === parts.length - 1) return null;
  const head = parts.slice(0, start);
  const flatName = parts.slice(start).join(".");
  return [...head, flatName].join(path.sep);
}

const adapter = {
  name: "mandipulse-fix-rsc-prefetch-paths",
  async onBuildComplete({ outputs }) {
    let renamed = 0;
    for (const file of outputs.staticFiles) {
      const sourcePath = file.filePath;
      const targetPath = flattenRscPath(sourcePath);
      if (!targetPath || targetPath === sourcePath) continue;
      await fs.mkdir(path.dirname(targetPath), { recursive: true });
      await fs.rename(sourcePath, targetPath);
      renamed += 1;
    }
    if (renamed > 0) {
      console.log(`[rsc-path-adapter] flattened ${renamed} RSC payload path(s)`);
    }
  },
};

export default adapter;
