# MASTER PROMPT: SECURE GOOGLE GEMINI API INTEGRATION

I have already developed my website using Google Antigravity AI. Now I want to integrate Google Gemini AI API into my existing website.

Your task is to integrate the Gemini API professionally, securely, and without affecting my existing website.

## 1. FIRST: ANALYZE THE EXISTING PROJECT

- Carefully inspect the entire existing project structure.
- Identify the frontend framework, backend technology, dependencies, and architecture.
- Understand how the existing website works before making changes.
- Identify the correct location for Gemini API integration.
- Do not make assumptions about my project structure.

## 2. PRESERVE MY EXISTING WEBSITE

This is extremely important.

- Do not redesign my website.
- Do not change the existing UI or UX.
- Do not modify the existing color scheme, typography, animations, spacing, or layout.
- Do not remove any existing features or components.
- Do not break existing functionality.
- Do not unnecessarily modify existing files.
- Maintain the existing responsive design.
- Only make changes that are necessary for Gemini API integration.

## 3. API KEY SECURITY

Implement industry-standard API key security.

- Never hardcode the API key in frontend code.
- Never expose the API key in HTML, CSS, JavaScript, React components, or browser source files.
- Never store the API key in localStorage, sessionStorage, cookies, or browser-accessible storage.
- Store the API key using server-side environment variables.
- Use a `.env` file for local development.
- Add `.env` and other secret files to `.gitignore`.
- Never commit API keys to GitHub.
- Never print API keys in terminal logs, browser console, or application logs.
- Never return the API key in API responses.
- Never expose secrets through error messages.
- Do not use frontend environment variables with public prefixes for storing secrets.
- Use only trusted server-side code to communicate with Google Gemini.

## 4. BACKEND INTEGRATION

- Create or reuse a secure backend API endpoint.
- The frontend must communicate only with my backend.
- The backend must communicate with the official Google Gemini API.
- Keep all Gemini API authentication on the server side.
- Validate all incoming user requests.
- Sanitize inputs where appropriate.
- Implement proper error handling.
- Prevent unauthorized or excessive API usage.
- Add rate limiting.
- Set reasonable request size limits and timeouts.
- Use secure HTTP communication.
- Do not allow users to access arbitrary backend resources through the AI endpoint.

## 5. GEMINI API INTEGRATION

- Use the official Google Gemini API and supported SDK.
- Use a currently supported Gemini model.
- Keep model configuration in the backend.
- Implement proper request and response handling.
- Handle API errors, invalid requests, quota limits, and network failures.
- Avoid unnecessary API calls.
- Do not expose internal API configuration to the frontend.

## 6. FRONTEND INTEGRATION

- Connect the existing website to the new backend endpoint.
- Maintain the existing UI design.
- Display appropriate loading indicators.
- Display user-friendly error messages.
- Prevent duplicate submissions when a request is already processing.
- Handle empty input and invalid input.
- Ensure the integration works on desktop, tablet, and mobile devices.
- Do not expose any secret information in frontend responses.

## 7. PERFORMANCE AND RELIABILITY

- Avoid unnecessary API requests.
- Implement appropriate request timeouts.
- Handle network failures gracefully.
- Avoid duplicate API calls.
- Keep the existing website performance unaffected.
- Follow clean and maintainable coding practices.

## 8. ENVIRONMENT CONFIGURATION

Create the required environment configuration.

Example:

GEMINI_API_KEY=your_actual_api_key

Requirements:

- Never insert an actual API key into source code.
- Never invent or generate an API key.
- Ask me to configure the secret in the appropriate environment.
- Provide an `.env.example` file containing placeholder values only.
- Ensure `.env` is excluded from Git.
- Explain how to configure environment variables in local development and production hosting.

## 9. TESTING AND SECURITY VERIFICATION

After implementation, perform the following checks:

- Verify that the Gemini API integration works.
- Verify that the API key is not exposed in browser developer tools.
- Verify that the API key is not present in frontend build files.
- Verify that the API key is not included in API responses.
- Verify that the backend handles invalid requests safely.
- Verify that rate limiting works.
- Verify that errors do not reveal sensitive information.
- Verify that existing website features still work.
- Check for broken imports, missing dependencies, and build errors.

Do not claim a security test passed unless you have actually performed it.

## 10. FINAL REPORT

After completing the implementation, provide:

1. Files created.
2. Files modified.
3. Backend architecture used.
4. Where to configure the Gemini API key.
5. How to run the project.
6. How to deploy it securely.
7. Security measures implemented.
8. Tests performed and their results.
9. Any remaining security limitations or manual steps.

## STRICT DEVELOPMENT RULES

- Analyze before modifying.
- Make minimal and targeted changes.
- Preserve the complete existing website.
- Never expose API keys.
- Never overwrite existing project files unnecessarily.
- Never delete existing features.
- Never fake test results.
- Never assume deployment secrets are automatically configured.
- Ask for my approval before destructive or irreversible changes.
- If any required information is missing, ask me before making risky changes.

## FINAL OBJECTIVE

Integrate Google Gemini AI into my existing website with strong security, clean backend architecture, reliable API communication, and zero unnecessary changes to my existing website design or functionality.

Work carefully, step by step, and verify the implementation before declaring it complete.





IMPORTANT: Do not ask me to paste my actual Gemini API key into this chat. First complete the backend setup and explain exactly where I should securely configure my API key. I will add the actual key myself through my local environment file or secure deployment environment variables. After that, verify the integration without exposing or logging the secret.