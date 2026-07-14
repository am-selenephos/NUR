import { defineConfig } from "@playwright/test";
import base from "./playwright.config";
export default defineConfig({
  ...base,
  webServer: undefined,
  use: {
    ...(base as any).use,
    screenshot: "only-on-failure",
    headless: false,
    launchOptions: {
      executablePath: "/tmp/chromium",
      args: ["--headless=new", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", "--no-zygote"],
    },
  },
});
