# TASK: PARAMETERIZE PORT CONFIGURATION

## 1. OBJECTIVE
Modify the project configuration to use a configurable port, as the default `3000` is occupied on the staging server.

## 2. PROBLEM
- `playwright.config.ts` has a hardcoded `baseURL: 'http://localhost:3000'`.
- The Next.js `dev` and `start` scripts will default to port `3000`.
- This creates an environmental conflict.

## 3. REQUIRED ACTIONS

### A. Parameterize Next.js Server
- Modify the `start` script in `package.json` to respect the `PORT` environment variable.
  - `next start -p $PORT` (for Linux/macOS) or use a cross-platform solution.
- **Default:** The application should run on port `3001` if `PORT` is not set.

### B. Update Playwright Config
- Modify `playwright.config.ts` to read from an environment variable.
- The `baseURL` should be constructed from `process.env.TEST_BASE_URL` or default to `http://localhost:3001`.

## 4. EXECUTION
- Update `package.json`.
- Update `playwright.config.ts`.
- **Optional:** Add a `.env.development` file setting `PORT=3001` for local convenience.

## 5. OUTPUT
- Modified `package.json`.
- Modified `playwright.config.ts`.
