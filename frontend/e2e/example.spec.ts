import { test, expect } from '@playwright/test';

const mockLoginResponse = {
    token: 'fake-token',
};
const mockApplicationApi = (route, response, status = 200) => {
    route.fulfill({
      status,
      contentType: 'application/json',
      body: JSON.stringify(response),
    });
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
        await page.locator('text=Password is too weak.').waitFor({ state: 'visible' });
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
                body: JSON.stringify({ data: mockLoginResponse }),
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
        page.on('dialog', async (dialog) => {
            console.log('Alert message:', dialog.message());
            expect(dialog.message()).toBe('Failed to login. Please try again.');
            await dialog.dismiss();
        });
        await page.waitForEvent('dialog');  
    });
});

//File and Job Description Input Page
test.describe('FileInput Component', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('http://localhost:3000/inputForm');
    });
  
    test('should upload a valid file successfully', async ({ page }) => {
        await page.route('http://localhost:8000/api/resume-upload', (route) => {
            route.fulfill({
            status: 200,
            body: JSON.stringify({
                message: 'Resume uploaded successfully.',
                status: 'success',
                character_count: 1234,
                session_id: 'test-session-id',
            }),
            contentType: 'application/json',
            });
        });
        const validFile = {
            name: 'valid-resume.pdf',
            mimeType: 'application/pdf',
            buffer: Buffer.from('%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj')
        };
        await page.setInputFiles('input[type="file"]', validFile);
        page.on('dialog', async (dialog) => {
            expect(dialog.message()).toBe('Resume uploaded successfully.');
            await dialog.dismiss();
        });
        await page.waitForEvent('dialog');  
    });
  
    test('should show an error for invalid file type', async ({ page }) => {
        await page.route('http://localhost:8000/api/resume-upload', (route) => {
            mockApplicationApi(route, {
                error: 'Invalid file type. Only PDF files are allowed.',
                status: 'error',
            }, 400);
        });
        const invalidFile = {
            name: 'invalid-resume.docx',
            mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            buffer: Buffer.from('This is a mock DOCX file.')
        };
        await page.setInputFiles('input[type="file"]', invalidFile);
        page.on('dialog', async (dialog) => {
            expect(dialog.message()).toBe('Failed to upload the resume. Please try again.');
            await dialog.dismiss();
        });
        await page.waitForEvent('dialog');  
    });
  
    test('should show an error for oversized file', async ({ page }) => {
        await page.route('http://localhost:8000/api/resume-upload', (route) => {
            mockApplicationApi(route, {
                error: 'File size exceeds the 2MB limit.',
                status: 'error',
            }, 400);
        });
            const oversizedFile = {
            name: 'oversized-resume.pdf',
            mimeType: 'application/pdf',
            buffer: Buffer.alloc(3 * 1024 * 1024, 0) // 3 MB file
        };
        await page.setInputFiles('input[type="file"]', oversizedFile);
        page.on('dialog', async (dialog) => {
            console.log('Alert message:', dialog.message());
            expect(dialog.message()).toBe('Failed to upload the resume. Please try again.');
            await dialog.dismiss(); 
        });
        await page.waitForEvent('dialog');  
    });    
});

test.describe('JobInput Component', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000/inputForm');
  });

  test('should submit a job description successfully', async ({ page }) => {
    await page.route('http://localhost:8000/api/job-description', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          message: 'Job description submitted successfully.',
          status: 'success',
        }),
        contentType: 'application/json',
      });
    });
    const validDescription = 'This is a valid job description.';
    await page.fill('textarea.input-textarea', validDescription);
    await page.click('button.submit-button');
    page.on('dialog', async (dialog) => {
      expect(dialog.message()).toBe('Job description submitted successfully.');
      await dialog.dismiss();
    });
    await page.waitForEvent('dialog');
  });

  test('should show an error for exceeding character limit', async ({ page }) => {
    await page.route('http://localhost:8000/api/job-description', (route) => {
      route.fulfill({
        status: 400,
        body: JSON.stringify({
          error: 'Job description exceeds character limit.',
          status: 'error',
        }),
        contentType: 'application/json',
      });
    });
    const longDescription = 'A'.repeat(6000);
    await page.fill('textarea.input-textarea', longDescription);
    await page.click('button.submit-button');
    page.on('dialog', async (dialog) => {
      expect(dialog.message()).toBe('Failed to submit the job description. Please try again.');
      await dialog.dismiss();
    });
    await page.waitForEvent('dialog');
  });

  test('should show an error if no resume is uploaded', async ({ page }) => {
    await page.route('http://localhost:8000/api/job-description', (route) => {
      route.fulfill({
        status: 400,
        body: JSON.stringify({
          error: 'No resume uploaded.',
          status: 'error',
        }),
        contentType: 'application/json',
      });
    });
    const validDescription = 'This is a valid job description.';
    await page.fill('textarea.input-textarea', validDescription);
    await page.click('button.submit-button');
    page.on('dialog', async (dialog) => {
      expect(dialog.message()).toBe('Failed to submit the job description. Please try again.');
      await dialog.dismiss();
    });
    await page.waitForEvent('dialog');
  });
});

