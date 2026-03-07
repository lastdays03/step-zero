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
    images: {
        remotePatterns: [
            ...(process.env.NEXT_PUBLIC_API_URL ? [{
                protocol: new URL(process.env.NEXT_PUBLIC_API_URL).protocol.replace(':', ''),
                hostname: new URL(process.env.NEXT_PUBLIC_API_URL).hostname,
            }] : []),
            ...(process.env.NEXT_PUBLIC_STORAGE_URL ? [{
                protocol: new URL(process.env.NEXT_PUBLIC_STORAGE_URL).protocol.replace(':', ''),
                hostname: new URL(process.env.NEXT_PUBLIC_STORAGE_URL).hostname,
            }] : []),
        ],
    },
};

export default nextConfig;
