import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "*.bestbuy.com",
      },
      {
        protocol: "https",
        hostname: "*.ebayimg.com",
      },
      {
        protocol: "https",
        hostname: "i.ebayimg.com",
      },
      {
        protocol: "https",
        hostname: "pisces.bbystatic.com",
      },
    ],
  },
};

export default nextConfig;
