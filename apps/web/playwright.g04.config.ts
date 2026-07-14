import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  globalSetup: "./e2e/global-setup.ts",
  timeout: 120_000,
  retries: 0,
  reporter: [["list"], ["html", { open: "never", outputFolder: "playwright-report-g04" }]],
  use: {
    baseURL: "http://localhost:4173",
    trace: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium-desktop-g04",
      use: { ...devices["Desktop Chrome"], viewport: { width: 1600, height: 900 } },
    },
    {
      name: "chromium-mobile-g04",
      use: { ...devices["Pixel 5"], viewport: { width: 393, height: 852 } },
    },
    {
      name: "firefox-desktop-g04",
      use: { ...devices["Desktop Firefox"], viewport: { width: 1600, height: 900 } },
    },
    {
      name: "webkit-mobile-g04",
      use: { ...devices["iPhone 13"], viewport: { width: 393, height: 852 } },
    },
  ],
  webServer: {
    command: "npm run build && npm run preview -- --port 4173 --strictPort",
    url: "http://localhost:4173",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    env: {
      VITE_API_BASE_URL: process.env.VITE_API_BASE_URL ?? "http://localhost:8000",
      VITE_NUR_ENABLE_OMEGA_RESEARCH: process.env.VITE_NUR_ENABLE_OMEGA_RESEARCH ?? "true",
      NUR_ENABLE_OMEGA_RESEARCH: process.env.NUR_ENABLE_OMEGA_RESEARCH ?? "true",
    },
  },
});
