# Running the Mobile App Locally

> Guide for Android development on Windows with emulator

## Prerequisites

- Android Studio with SDK installed
- Pixel 6 emulator (or physical device)
- Docker Desktop running
- Repo at short path (e.g., `C:\github\pcd`)

---

## Quick Start

```bash
# Terminal 1: Start Docker + Backend
docker compose -f infra/docker/docker-compose.yml up -d
pnpm --filter @pcd/backend dev

# Terminal 2: Start Metro bundler
cd apps/mobile-technician
pnpm start

# Android Studio: Start Pixel 6 emulator

# Terminal 3: Deploy to emulator
cd apps/mobile-technician
pnpm android
```

**Login:** `tech@pcd.local` / `password123`

---

## First-Time Setup

### 1. Verify Android Environment

```bash
adb devices  # Should show emulator-5554 or similar
```

### 2. Database Setup

Ensure `apps/backend/.env` has:
```
DATABASE_URL=postgres://pcd:pcd123@localhost:5432/plumbers_compliance
JWT_SECRET=your-secret-here
```

Then seed the database:
```bash
pnpm --filter @pcd/backend db:push
pnpm --filter @pcd/backend db:seed
```

### 3. API URL (already configured)

`apps/mobile-technician/src/lib/api.ts` uses `__DEV__` flag:
- **Development:** `http://10.0.2.2:3001` (emulator → host)
- **Production:** Uses staging/prod backend URL

---

## Test Accounts

| Email | Password | Role |
|-------|----------|------|
| tech@pcd.local | password123 | TECHNICIAN |
| company@pcd.local | password123 | COMPANY_ADMIN |
| admin@pcd.local | password123 | PLATFORM_ADMIN |

---

## Troubleshooting

### "Network request failed"
- Backend not running → start with `pnpm --filter @pcd/backend dev`
- Wrong API URL → emulator needs `10.0.2.2` not `localhost`

### "Password authentication failed"
- `.env` doesn't match Docker config
- Fix: `DATABASE_URL=postgres://pcd:pcd123@localhost:5432/plumbers_compliance`

### Build fails with "path too long"
- Windows 260-char limit
- Solution: Move repo to short path like `C:\github\pcd`

### Metro cache issues
```bash
pnpm start --reset-cache
```
