import { test, expect } from "@playwright/test";

test.describe("Dashboard", () => {
  test.use({ storageState: ".playwright/.auth/user.json" });

  test("loads with stats and greeting", async ({ page }) => {
    await page.goto("/en/dashboard");
    await expect(page.getByText(/good morning|good afternoon|good evening/i)).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/second brain/i).first()).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(/operational/i)).toBeVisible();
    await expect(page.locator("text=Notes")).toBeVisible();
  });
});
