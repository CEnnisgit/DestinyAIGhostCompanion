# Phase 5C: Auth UI

> **Status:** 🔲 Not Started
> **Objective:** Build the login screen and connect it to the Bungie OAuth flow from Phase 4B.
> **Location:** `apps/desktop/src/`
> **Depends On:** Phase 5B (design system), Phase 4B (backend auth routes)

---

## Context for the Agent

The Rust backend (Phase 4B) exposes:
- `GET /auth/login` — Redirects the user to Bungie's OAuth consent screen.
- `GET /auth/callback?code={code}` — Exchanges the code for tokens and returns a `BungieMembershipId`.

Your job is to build the frontend screens that initiate the login, handle the redirect, and manage session state.

## Deliverables

### 1. `apps/desktop/src/pages/LoginPage.tsx`
A full-screen landing page with the Destiny aesthetic:
- Large Ghost mark icon centered.
- "Ghost Companion" title with the gold eyebrow text.
- A prominent "Sign in with Bungie" button.
- The button should:
  - **Web:** Navigate to `{API_BASE_URL}/auth/login` (which redirects to Bungie).
  - **Electron:** Open the Bungie OAuth URL in the system browser using `shell.openExternal()`, then listen for the callback via a local deep link or polling.
- Subtle animated background particles or the radial gradient from the design system.

### 2. `apps/desktop/src/pages/AuthCallbackPage.tsx`
A loading screen shown while the OAuth callback is being processed:
- Display a pulsing Ghost mark with "Linking to Bungie..." text.
- Parse the `?code=` query parameter from the URL.
- Call the backend: `GET /auth/callback?code={code}`.
- On success: store the `membership_id` in React context and redirect to the main app.
- On failure: show an error message with a "Try Again" button.

### 3. `apps/desktop/src/context/AuthContext.tsx`
Create a React context for session state:
```typescript
interface AuthState {
  isAuthenticated: boolean;
  membershipId: string | null;
  login: () => void;
  logout: () => void;
}
```
- Persist the session in `localStorage` (key: `ghost-auth-session`).
- On app load, check if a valid session exists. If not, redirect to `LoginPage`.
- Provide a `logout()` function that clears storage and redirects to login.

### 4. `apps/desktop/src/components/ProtectedRoute.tsx`
A wrapper component that redirects to the login page if the user is not authenticated:
```typescript
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" />;
  return children;
}
```

### 5. Routing Setup
Install React Router and configure routes:
```bash
npm install react-router-dom
```
```typescript
<Routes>
  <Route path="/login" element={<LoginPage />} />
  <Route path="/auth/callback" element={<AuthCallbackPage />} />
  <Route path="/" element={
    <ProtectedRoute>
      <AppLayout />
    </ProtectedRoute>
  } />
</Routes>
```

## Electron-Specific Considerations
- In Electron, the OAuth callback can be handled via a **custom protocol** (e.g., `ghostcompanion://auth/callback?code=xxx`). Register this in `electron/main.ts`:
  ```typescript
  app.setAsDefaultProtocolClient('ghostcompanion');
  ```
- Alternatively, the backend can redirect to `http://localhost:5173/auth/callback?code=xxx` during development.

## Verification
- [ ] Navigating to `http://localhost:5173` redirects to `/login`.
- [ ] Clicking "Sign in with Bungie" redirects to Bungie's OAuth page.
- [ ] After approving on Bungie, the callback lands back in the app and displays the main layout.
- [ ] Refreshing the page maintains the session (localStorage).
- [ ] Clicking "Logout" clears the session and returns to the login page.

## ADR References
- **ADR 005**: Delegated Authentication — 100% Bungie OAuth2 SSO.

## Next Phase
Once verified, proceed to → [Phase 5D: Voice Interface](./PHASE_5D_Voice_Interface.md) or [Phase 5E: Inventory UI](./PHASE_5E_Inventory_UI.md)
