import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'standalone',
    reactStrictMode: true,
    allowedDevOrigins: process.env.ALLOWED_DEV_ORIGINS
        ? process.env.ALLOWED_DEV_ORIGINS.split(",")
        : ["localhost:3000"],
    turbopack: {
        root: __dirname,
    },
    // Add image domains etc if needed
};

export default nextConfig;
