import { test, expect, chromium } from '@playwright/test';

test.describe('Sign Up Page', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('http://frontend-e2e:3000/signup');
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

    test('should navigate to login page on successful registration', async ({ page, request }) => {
        await page.fill('input[name="email"]', 'test1@example.com');
        await page.fill('input[name="username"]', 'testuser');
        await page.fill('input[name="password"]', 'StrongPass1!');
        await page.fill('input[name="confirmPassword"]', 'StrongPass1!');
        await page.click('button[type="submit"]');
        await expect(page).toHaveURL('http://frontend-e2e:3000/login', { timeout: 40000 });
        await request.delete('http://backend:8000/api/delete', {
            params: {
              email: 'test1@example.com'
            },
        });
    });
});

test.describe('Login Page', () => {
    test('Submits the login form with valid input and redirects', async ({page, request}) => {
        await request.post('http://backend:8000/api/register', {
            data: {
                "email": "test3@example.com",
                "password": "securePassword123",
                "username": "testuser"
            },
        });
        await page.goto('http://frontend-e2e:3000');
        await page.locator('input[placeholder="Email"]').fill('test3@example.com');
        await page.locator('input[placeholder="Password"]').fill('securePassword123');
        await page.locator('button:has-text("Login")').click();
        await page.waitForURL('http://frontend-e2e:3000/dashboard', { timeout: 10000 });
        await request.delete('http://backend:8000/api/delete', {
            params: {
              email: 'test3@example.com'
            },
        });
    });

    test('Submits the login form with invalid input', async ({page}) => {
        await page.goto('http://frontend-e2e:3000/login');
        await page.locator('input[name="email"]').fill('invalid_user@example.com');
        await page.locator('input[name="password"]').fill('wrongpassword');
        await page.locator('button:has-text("Login")').click();
        page.on('dialog', async (dialog) => {
            console.log('Alert message:', dialog.message());
            expect(dialog.message()).toBe('Failed to login. Please try again.');
            await dialog.dismiss();
        });
        await page.waitForEvent('dialog', { timeout: 10000 });  
    });
});

//File and Job Description Input Page
test.describe('FileInput Component', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('http://frontend-e2e:3000/inputForm');
    });
  
    test('should show an error for invalid file type', async ({ page }) => {
        const invalidFile = {
            name: 'invalid-resume.docx',
            mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            buffer: Buffer.from('This is a mock DOCX file.')
        };
        await page.setInputFiles('input[type="file"]', invalidFile, { timeout: 10000 });
        page.on('dialog', async (dialog) => {
            expect(dialog.message()).toBe('Failed to upload the resume. Please try again.');
            await dialog.dismiss();
        });
        await page.waitForEvent('dialog', { timeout: 10000 });  
    });
  
    test('should show an error for oversized file', async ({ page }) => {
        const oversizedFile = {
            name: 'oversized-resume.pdf',
            mimeType: 'application/pdf',
            buffer: Buffer.alloc(3 * 1024 * 1024, 0) // 3 MB file
        };
        await page.setInputFiles('input[type="file"]', oversizedFile, { timeout: 10000 });
        page.on('dialog', async (dialog) => {
            console.log('Alert message:', dialog.message());
            expect(dialog.message()).toBe('Failed to upload the resume. Please try again.');
            await dialog.dismiss(); 
        });
        await page.waitForEvent('dialog', { timeout: 10000 });  
    });    
});

test.describe('JobInput Component', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://frontend-e2e:3000/inputForm');
  });

  test('should show an error for exceeding character limit', async ({ page }) => {
    const longDescription = 'A'.repeat(6000);
    await page.fill('textarea.input-textarea', longDescription);
    await page.click('button.submit-button');
    page.on('dialog', async (dialog) => {
      expect(dialog.message()).toBe('Failed to submit the job description. Please try again.');
      await dialog.dismiss();
    });
    await page.waitForEvent('dialog', { timeout: 10000 });
  });
});

test.describe('Resume and Job Description Matching', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://frontend-e2e:3000/inputForm');
  });
  test('should calculate fit score for a matching resume, job description and able to download updated resume', async ({ page }) => {
    const jobDescriptionContent = `
      Looking for a software engineer with strong experience in Python, AWS, and REST APIs.
      Candidates should be proficient in modern cloud technologies and web services.
      Required Skills:
      - Python
      - AWS
      - REST APIs
      Preferred Skills:
      - Docker`;
    await page.fill('textarea.input-textarea', jobDescriptionContent);
    await page.setInputFiles('input[type="file"]', "./tests/resume.pdf", { timeout: 10000 });
    await page.click('button.submit-button');
    await page.goto('http://frontend-e2e:3000/dashboard');
    const fitScoreElement = page.locator('.resume-fit-score-percentage');
    await fitScoreElement.waitFor({ state: 'visible' });
    const fitScoreText = await fitScoreElement.textContent();
    const score = parseInt(fitScoreText || '0', 10);
    expect(score).toBeGreaterThanOrEqual(75);
    expect(score).toBeLessThanOrEqual(100);
    await page.waitForSelector('.dashboard-analysis-results');
    const feedbackList = page.locator('ul.feedback-filter-list');
    const childCount = await feedbackList.locator('li').count();
    expect(childCount).toBeGreaterThan(0);
    await page.waitForSelector('.dashboard-header');
    const downloadButton = await page.locator('.download-report-btn');
    await downloadButton.click();
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      downloadButton.click(),
    ]);
    const downloadFilePath = await download.path();
    expect(downloadFilePath).toBeTruthy();
  });
});