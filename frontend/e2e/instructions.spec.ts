import { test, expect } from "@playwright/test";

test.describe("Custom Instructions", () => {
  test.use({ storageState: ".playwright/.auth/user.json" });

  test("create, toggle, and delete an instruction", async ({ page }) => {
    await page.goto("/en/instructions");
    await expect(page.getByText(/custom instructions/i).first()).toBeVisible({ timeout: 10000 });

    // Create
    await page.getByRole("button", { name: /new instruction/i }).click();
    await page.getByPlaceholder(/instruction name/i).fill("E2E Test Instruction");
    await page.getByPlaceholder(/instruction content/i).fill("Test content for E2E.");
    await page.getByRole("button", { name: /save/i }).click();
    await expect(page.getByText(/instruction created/i)).toBeVisible({ timeout: 5000 });
    await expect(page.getByText("E2E Test Instruction")).toBeVisible({ timeout: 5000 });

    // Delete — click trash button
    const card = page.locator("[class*='grid'] > *").filter({ hasText: "E2E Test Instruction" }).first();
    await card.getByRole("button").last().click();
    await page.getByRole("button", { name: /delete/i }).click();
    await expect(page.getByText(/instruction deleted/i)).toBeVisible({ timeout: 5000 });
  });
});
