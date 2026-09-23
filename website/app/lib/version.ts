/**
 * Application version extracted dynamically from pyproject.toml during build/dev
 */
export const APP_VERSION = process.env.NEXT_PUBLIC_APP_VERSION || '0.9.0';
export const DISPLAY_VERSION = `v${APP_VERSION}`;
