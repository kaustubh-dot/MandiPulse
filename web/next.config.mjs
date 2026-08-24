import path from "node:path";

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
  adapterPath: path.resolve(import.meta.dirname, "build/export-adapter.mjs"),
};

export default nextConfig;
