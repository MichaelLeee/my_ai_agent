import { test, expect } from "@playwright/test";

test.describe("Second Brain", () => {
  test.use({ storageState: ".playwright/.auth/user.json" });

  test("create, search, and delete a note", async ({ page }) => {
    await page.goto("/en/second-brain");
    await expect(page.getByRole("heading", { name: /second brain/i })).toBeVisible();

    // Create a note
    await page.getByRole("button", { name: /new note/i }).click();
    await page.getByPlaceholder(/title/i).first().fill("E2E Test Note");
    await page.getByPlaceholder(/content/i).first().fill("Playwright created this.");
    await page.getByPlaceholder(/tags|journal/).fill("test,e2e");
    await page.getByRole("button", { name: /save/i }).click();
    await expect(page.getByText(/note created|note saved/i)).toBeVisible({ timeout: 5000 });

    // Wait for list refresh and verify note appears
    await expect(page.getByText("E2E Test Note").first()).toBeVisible({ timeout: 5000 });

    // Delete the note — click trash icon on the note card
    const card = page.locator("[class*='grid'] > *").filter({ hasText: "E2E Test Note" }).first();
    await card.locator("button").last().click();
    await page.getByRole("button", { name: /delete/i }).click();
    await expect(page.getByText(/note deleted/i)).toBeVisible({ timeout: 5000 });
  });

  test("knowledge graph loads", async ({ page }) => {
    await page.goto("/en/second-brain");
    await page.getByRole("button", { name: /show graph/i }).click();
    await expect(page.locator("svg")).toBeVisible({ timeout: 10000 });
  });
});
