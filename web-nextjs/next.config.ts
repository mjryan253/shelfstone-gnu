import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  output: 'standalone', // Enables the standalone output mode for optimized Docker images
};

export default nextConfig;
