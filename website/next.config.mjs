import fs from 'node:fs';
import path from 'node:path';

/** @type {import('next').NextConfig} */
const isProd = process.env.NODE_ENV === 'production';

// Dynamically extract version from root pyproject.toml
let appVersion = '0.9.0';
try {
  const pyprojectPath = path.resolve(process.cwd(), '..', 'pyproject.toml');
  if (fs.existsSync(pyprojectPath)) {
    const content = fs.readFileSync(pyprojectPath, 'utf8');
    const match = content.match(/version\s*=\s*["']([^"']+)["']/);
    if (match && match[1]) {
      appVersion = match[1];
    }
  }
} catch (err) {
  console.warn('Could not read version from pyproject.toml:', err);
}

const nextConfig = {
  reactStrictMode: true,
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  basePath: process.env.NEXT_PUBLIC_BASE_PATH || (isProd ? '/losna-cli' : ''),
  env: {
    NEXT_PUBLIC_BASE_PATH: process.env.NEXT_PUBLIC_BASE_PATH || (isProd ? '/losna-cli' : ''),
    NEXT_PUBLIC_APP_VERSION: appVersion,
  },
};

export default nextConfig;
