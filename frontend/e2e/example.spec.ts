import { test, expect, chromium } from '@playwright/test';

const mockApiResponse = {
    token: 'fake-token',
};
const mockError = {
    error: 'fake-error',
};

test.describe('Sign Up Page', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('http://localhost:3000/signup');
    });

    test('should load the signup form', async ({ page }) => {
        await expect(page.locator('h2')).toHaveText('Sign Up');
        await expect(page.locator('form')).toBeVisible();
    });

    test('should display password strength feedback', async ({ page }) => {
        const passwordInput = page.locator('input[name="password"]');
        const strengthFeedback = page.locator('.password-strength');

        await passwordInput.fill('weak');
        await expect(strengthFeedback).toHaveText('Password Strength: Weak');

        await passwordInput.fill('Moderate1');
        await expect(strengthFeedback).toHaveText('Password Strength: Moderate');

        await passwordInput.fill('StrongPass1!');
        await expect(strengthFeedback).toHaveText('Password Strength: Strong');
    });

    test('should show error when passwords do not match', async ({ page }) => {
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="username"]', 'testuser');
        await page.fill('input[name="password"]', 'StrongPass1!');
        await page.fill('input[name="confirmPassword"]', 'DifferentPass');
        await page.click('button[type="submit"]');
        const errorMessages = page.locator('text=Passwords do not match.');
        await expect(errorMessages.first()).toBeVisible();
    });

    test('should show error when password is weak', async ({ page }) => {
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="username"]', 'testuser');
        await page.fill('input[name="password"]', 'weak');
        await page.fill('input[name="confirmPassword"]', 'weak');
        await page.click('button[type="submit"]');
        await page.locator('text=Password is too weak.');
    });

    test('should navigate to login page on successful registration', async ({ page }) => {
        await page.route('http://localhost:8000/api/register', async (route) => {
            await route.fulfill({
                status: 200,
                body: JSON.stringify({ message: 'Registration successful' }),
            });
        });
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="username"]', 'testuser');
        await page.fill('input[name="password"]', 'StrongPass1!');
        await page.fill('input[name="confirmPassword"]', 'StrongPass1!');
        await page.click('button[type="submit"]');
        await expect(page).toHaveURL('http://localhost:3000/login');
    });

    test('should display registration error on failure', async ({ page }) => {
        // Mock the API response for registration failure
        await page.route('http://localhost:8000/api/register', async (route) => {
            await route.fulfill({
                status: 400,
                body: JSON.stringify({ message: 'Registration failed' }),
            });
        });
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="username"]', 'testuser');
        await page.fill('input[name="password"]', 'StrongPass1!');
        await page.fill('input[name="confirmPassword"]', 'StrongPass1!');
        await page.click('button[type="submit"]');
        const errorMessages = page.locator('text=Registration failed');
        await expect(errorMessages.first()).toBeVisible();
    });
});

test.describe('Login Page', () => {
    test('Submits the login form with valid input and redirects', async ({page}) => {
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

    test('Submits the login form with invalid input', async ({page}) => {
        const mockError = { message: 'Invalid credentials' };
        await page.route('http://localhost:8000/api/login', (route) => {
        route.fulfill({
            status: 400,
            contentType: 'application/json',
            body: JSON.stringify({ error: mockError }),
        });
        });
        await page.goto('http://localhost:3000/login');
        await page.locator('input[name="email"]').fill('invalid_user@example.com');
        await page.locator('input[name="password"]').fill('wrongpassword');
        await page.getByRole('button', { name: /login/i }).click();
        await page.locator('text=Invalid credentials');
    });
});