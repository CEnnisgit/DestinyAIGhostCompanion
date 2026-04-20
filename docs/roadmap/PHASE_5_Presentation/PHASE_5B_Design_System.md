# Phase 5B: Design System

> **Status:** 🔲 Not Started
> **Objective:** Harvest the existing Destiny-themed CSS from `webapp/index.html` and formalize it into a reusable React component library.
> **Location:** `apps/desktop/src/`
> **Depends On:** Phase 5A (Vite project running)

---

## Context for the Agent

The file `webapp/index.html` (648 lines) contains a **production-quality Destiny 2 design system** with:
- CSS custom properties for a dark, sci-fi aesthetic (`--bg-0`, `--accent`, `--gold`, etc.).
- Glassmorphism panels with `backdrop-filter: blur(18px)`.
- Radial gradient backgrounds simulating Destiny's lighting.
- Chat bubble styles (user = blue gradient, ghost = dark with gold border, system = red).
- Responsive breakpoints for desktop, tablet, and mobile.
- A Ghost eye-mark SVG/CSS icon.

Your job is to **extract** these design tokens into the new React project and create reusable components.

## Deliverables

### 1. `apps/desktop/src/styles/tokens.css`
Extract ALL CSS custom properties from `webapp/index.html` into a dedicated token file:
```css
:root {
  color-scheme: dark;
  --bg-0: #06101a;
  --bg-1: #0a1522;
  --bg-2: rgba(12, 21, 35, 0.86);
  --bg-3: rgba(17, 29, 44, 0.96);
  --line: rgba(140, 184, 255, 0.18);
  --line-strong: rgba(126, 224, 255, 0.34);
  --text: #edf4ff;
  --muted: #8ba0c1;
  --accent: #80e2ff;
  --accent-strong: #4fb2ff;
  --gold: #f4c76a;
  --danger: #ff9a9a;
  --shadow: 0 30px 120px rgba(0, 0, 0, 0.45);
  --radius-xl: 28px;
  --radius-lg: 22px;
  --radius-md: 18px;
  --font: "Segoe UI", "Trebuchet MS", sans-serif;
}
```

### 2. `apps/desktop/src/styles/global.css`
Extract the global styles (body background, box-sizing, scrollbar hiding, keyframe animations).

### 3. React Components
Create the following reusable components using the design tokens:

#### `apps/desktop/src/components/Panel.tsx`
The glassmorphism sidebar container.

#### `apps/desktop/src/components/Shell.tsx`
The main content area with the gradient header, quick-action chips, and content slot.

#### `apps/desktop/src/components/ChatBubble.tsx`
```typescript
interface ChatBubbleProps {
  role: 'user' | 'ghost' | 'system';
  content: string;
  timestamp?: Date;
}
```
Style each role with the matching bubble gradient from the legacy CSS.

#### `apps/desktop/src/components/Composer.tsx`
The text input + "Transmit" button at the bottom of the chat. Support `Enter` to submit and `Shift+Enter` for newlines.

#### `apps/desktop/src/components/QuickAction.tsx`
The pill-shaped chip buttons for preset prompts ("Weekly priorities", "Lore summary", etc.).

#### `apps/desktop/src/components/GhostMark.tsx`
The CSS-only Ghost eye icon from the legacy design. Port the `::before` and `::after` pseudo-elements into a React component.

#### `apps/desktop/src/components/StatusCard.tsx`
The connection status indicators (Backend, WebSocket, Auth).

### 4. `apps/desktop/src/layouts/AppLayout.tsx`
The two-column responsive layout (`340px sidebar + 1fr main`) with mobile collapse breakpoints at 1100px and 720px.

### 5. Storybook (Optional but Recommended)
If time permits, add Storybook for isolated component development:
```bash
npx -y storybook@latest init
```

## Design Constraints
- **DO NOT use TailwindCSS.** Use vanilla CSS with the design tokens.
- **DO NOT change the color palette.** The existing palette is carefully tuned to match Destiny 2's UI aesthetic.
- **DO add micro-animations.** Port the `@keyframes rise` animation. Add hover effects on chips and buttons (subtle glow, scale transform).
- **Use Google Fonts.** Replace "Segoe UI" with `Inter` or `Outfit` for cross-platform consistency.

## Verification
- [ ] `npm run dev` renders the full two-column layout with the Ghost mark, sidebar, and chat area.
- [ ] All components use CSS custom properties from `tokens.css` — no hardcoded colors.
- [ ] The layout collapses correctly on mobile viewport widths.
- [ ] Chat bubbles animate in with the `rise` keyframe.

## Next Phase
Once verified, proceed to → [Phase 5C: Auth UI](./PHASE_5C_Auth_UI.md)
