import { test, expect, chromium } from '@playwright/test';

const mockApiResponse = {
    token: 'fake-token',
};

test.describe('Login Page', () => {
    test('Submits the form with valid input and redirects', async ({page}) => {
        await page.route('http://localhost:8000/api/login', (route) => {
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({ data: mockApiResponse }),
            });
        });
        await page.goto('http://localhost:3000');
        await page.locator('input[placeholder="Email"]').fill('user@example.com');
        await page.locator('input[placeholder="Password"]').fill('password123');
        await page.locator('button:has-text("Login")').click();
        await page.waitForURL('http://localhost:3000/dashboard');
    });
});