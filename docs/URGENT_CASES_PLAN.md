# Urgent Cases — Dedicated Page & UX Enhancement
### Developer Handoff Document
> **Status:** Awaiting developer implementation via agents  
> **Created:** 2026-05-04  
> **Project:** SVU Helper Admin Dashboard (`dashboard_api/` + `dashboard_ui/`)

---

## Context & Background

The admin dashboard already has a working backend endpoint (`GET /api/projects/urgent`) and a React hook (`useUrgentProjects`) that fetches urgent cases. However, this data is only loosely shown on the overview page.

The **goal of this task** is to build a fully dedicated Urgent Cases experience:
- A **separate page** at `/urgent` (nested under Projects in the sidebar)
- A **notification badge** on the sidebar button showing the live count
- **Grouped sections** by urgency type (not a flat list)
- **Context-aware action buttons** per case type (not just a generic "Details" button)
- **Preloaded count** at app startup for instant sidebar feedback

---

## ⚠️ Open Questions — Must Be Answered Before Coding

> These are blockers. Resolve with the project owner before writing code.

### Q1 — Payment Approval Status Transition
When the admin clicks **"Approve Payment"** on a `awaiting_verification` project, what should the new project `status` be?
- **Assumption:** `awaiting_verification` → `accepted`
- **Confirm:** Is this correct? Should anything else be updated (e.g., payment record status)?

### Q2 — Payment Rejection Behaviour
When the admin clicks **"Reject Payment"**, what should happen?
- **Option A (Deny Project):** Trigger `DenyProjectService` — project is fully denied and student is notified. Same as denying any other project.
- **Option B (Re-upload Request):** Set payment status to `rejected` and notify the student to re-upload proof. Project stays in `awaiting_verification`.
- **Assumption:** Option A (deny project). **Confirm or specify Option B.**

### Q3 — Preload Full Urgent List at Login?
Should the full urgent project list be prefetched immediately on login (so the page is instant when first visited), or is it acceptable to fetch on-demand when the user navigates to `/urgent`?
- **Option A (Prefetch at login):** `queryClient.prefetchQuery(['projects', 'urgent'])` added to `App.jsx`. Costs one extra API call at login.
- **Option B (On-demand):** Fetch only when navigating to `/urgent`. Shows a ~1-2s spinner on first visit.
- **Recommendation:** Prefetch the **count only** at login (already planned). Prefetch the **full list** only if the owner confirms Option A.

---

## Mandatory Reading Before Writing Any Code

Before touching any file, read these two skill/rule files:

1. **`AGENTS.md`** (project root) — Bot-level architectural rules (i18n, helpers, logging, keyboards)
2. **`.agents/skills/dashboard-architecture/SKILL.md`** — Dashboard-specific rules (clean architecture layers, design tokens, no magic numbers)

---

## Architecture Overview

```
svu_helper/
├── dashboard_api/              # FastAPI backend
│   ├── api/routers/projects.py # ← MODIFY: add /urgent/count + /approve-payment
│   ├── repositories/projects_repo.py  # ← MODIFY: add count + categorized queries
│   ├── schemas/projects.py     # ← MODIFY: add UrgentReason + UrgentProjectResponse
│   └── services/projects_service.py   # ← MODIFY: tag urgent items by reason
│
└── dashboard_ui/               # React + Vite frontend
    └── src/
        ├── App.jsx             # ← MODIFY: add /urgent route
        ├── pages/
        │   └── UrgentCases.jsx # ← NEW
        ├── components/
        │   └── urgent/
        │       ├── UrgentCaseCard.jsx        # ← NEW
        │       ├── UrgentSection.jsx         # ← NEW
        │       └── PaymentApprovalModal.jsx  # ← NEW
        ├── hooks/
        │   ├── useUrgentCases.js   # ← NEW
        │   └── useProjectMutations.js  # ← MODIFY: add approvePayment
        ├── components/layout/Sidebar.jsx     # ← MODIFY: add badge
        └── styles/tokens.css       # ← MODIFY: add urgent color tokens
```

---

## Proposed Changes — Detailed

### 1. Backend — `dashboard_api/`

#### [MODIFY] `dashboard_api/schemas/projects.py`
Add an `UrgentReason` enum and an `UrgentProjectResponse` schema. This tells the frontend exactly **why** a project is urgent, enabling context-aware action buttons.

```python
from enum import Enum

class UrgentReason(str, Enum):
    PENDING_TOO_LONG = "pending_too_long"   # status=pending, created >6h ago
    PAYMENT_AWAITING = "payment_awaiting"   # status=awaiting_verification, payment >6h ago
    NEAR_DEADLINE    = "near_deadline"      # status=accepted/offered, delivery ≤2 days

class UrgentProjectResponse(ProjectResponse):
    urgent_reason: UrgentReason
    payment: Optional[PaymentResponse] = None  # only populated for payment_awaiting
```

#### [MODIFY] `dashboard_api/repositories/projects_repo.py`
Add two new functions:

```python
async def get_urgent_count() -> int:
    """Cheap count query for the sidebar badge. Does NOT fetch full documents."""
    ...

async def get_urgent_projects_categorized() -> dict:
    """Returns {'pending_too_long': [...], 'payment_awaiting': [...], 'near_deadline': [...]}"""
    # Uses the same 3-cursor logic already in infrastructure/repositories/project.py
    # but returns them as separate lists (not merged) so the service can tag urgent_reason
    ...
```

#### [MODIFY] `dashboard_api/services/projects_service.py`
Update `get_urgent_projects_list` to:
1. Call `get_urgent_projects_categorized()` to get 3 separate lists.
2. Tag each document with its `urgent_reason`.
3. For `payment_awaiting` items, fetch payment doc and attach it.
4. Return `List[UrgentProjectResponse]`.

#### [MODIFY] `dashboard_api/api/routers/projects.py`
- Change `GET /urgent` response model to `List[UrgentProjectResponse]`
- **Add** `GET /urgent/count` → returns `{"count": N}` (uses `get_urgent_count()`)
- **Add** `POST /{proj_id}/approve-payment` → approves payment + transitions project to `accepted`

```python
@router.get("/urgent/count", response_model=UrgentCountResponse)
async def get_urgent_count_endpoint(...):
    ...

@router.post("/{proj_id}/approve-payment", response_model=ActionResponse)
async def approve_payment(proj_id: int, ...):
    # 1. Set payment.status = "approved"
    # 2. Set project.status = "accepted"  (confirm with Q1 above)
    # 3. Notify student via Telegram (background task)
    # 4. Log audit event
    ...
```

> **Note:** Add a new `UrgentCountResponse` schema: `class UrgentCountResponse(BaseModel): count: int`

---

### 2. Frontend — `dashboard_ui/`

#### [MODIFY] `src/styles/tokens.css` + `tailwind.config.js`
Add urgency color tokens:
```css
:root {
  --color-urgent-critical: #ef4444;  /* red   — pending too long */
  --color-urgent-warning:  #f59e0b;  /* amber — payment awaiting */
  --color-urgent-moderate: #f97316;  /* orange — near deadline */
}
```
Expose in `tailwind.config.js` as `text-urgent-critical`, `bg-urgent-warning`, etc.

> **Rule:** All hex values go in `tokens.css` only. Components must use Tailwind classes. Never write raw hex inside JSX.

#### [NEW] `src/hooks/useUrgentCases.js`
```js
// Full list — fetched when navigating to /urgent
export function useUrgentCases() {
  return useQuery({
    queryKey: ['projects', 'urgent'],
    queryFn: () => apiClient.get('/projects/urgent').then(r => r.data),
    staleTime: 2 * 60 * 1000,
    refetchInterval: 2 * 60 * 1000,  // auto-refresh every 2 min
  });
}

// Count only — used by sidebar badge
export function useUrgentCount() {
  return useQuery({
    queryKey: ['projects', 'urgent', 'count'],
    queryFn: () => apiClient.get('/projects/urgent/count').then(r => r.data.count),
    staleTime: 30_000,
    refetchInterval: 60_000,  // refresh every 60s
  });
}
```

#### [MODIFY] `src/App.jsx`
- Import `UrgentCases` page
- Add route: `<Route path="/urgent" element={<ProtectedRoute><UrgentCases /></ProtectedRoute>} />`
- **Preload count at startup:**
```js
queryClient.prefetchQuery({
  queryKey: ['projects', 'urgent', 'count'],
  queryFn: () => apiClient.get('/projects/urgent/count').then(r => r.data.count),
});
```

#### [MODIFY] `src/components/layout/Sidebar.jsx`
- Add `{ to: '/urgent', icon: AlertTriangle, label: 'Urgent Cases' }` nav entry (after Projects)
- Import `useUrgentCount`, render badge:
```jsx
import { useUrgentCount } from '../../hooks/useUrgentCases';

// Inside the nav item for /urgent:
{count > 0 && (
  <span className="ml-auto text-xs font-bold bg-urgent-critical text-white px-1.5 py-0.5 rounded-full min-w-[20px] text-center">
    {count}
  </span>
)}
```

#### [NEW] `src/components/urgent/UrgentSection.jsx`
Collapsible section container:
- Props: `title`, `count`, `colorClass`, `children`
- Renders a colored section header with count badge + collapse toggle
- Defaults to expanded

#### [NEW] `src/components/urgent/UrgentCaseCard.jsx`
Single project card:
- Props: `project` (UrgentProjectResponse), `onOffer`, `onDeny`, `onFinish`, `onViewPayment`
- Renders: project ID, student name, subject name, status badge, urgency reason tag
- **Context-aware action buttons:**

| `urgent_reason`      | Buttons shown                         |
|----------------------|---------------------------------------|
| `pending_too_long`   | `[Send Offer]` + `[Deny]`             |
| `payment_awaiting`   | `[View Payment → Approve / Reject]`   |
| `near_deadline`      | `[Mark Finished]` + `[View Details]`  |

#### [NEW] `src/components/urgent/PaymentApprovalModal.jsx`
Modal for payment review:
- Fetches `GET /api/files/{file_id}` to show/download payment proof
- **Approve** → calls `approvePayment.mutate(projId)` → `POST /projects/{id}/approve-payment`
- **Reject** → calls `denyProject.mutate(projId)` → `POST /projects/{id}/deny`
- Shows loading state, success/error feedback inline

#### [NEW] `src/pages/UrgentCases.jsx`
Main page structure:
```
┌──────────────────────────────────────────────────┐
│ ⚠️  Urgent Cases                   [Auto-refresh] │
│ Filter: [All] [Pending] [Payments] [Deadlines]   │
├──────────────────────────────────────────────────┤
│ 🔴 Pending Too Long                     (N)  ▼  │
│   [UrgentCaseCard] ...                           │
├──────────────────────────────────────────────────┤
│ 🟡 Payment Awaiting Approval            (N)  ▼  │
│   [UrgentCaseCard] ...                           │
├──────────────────────────────────────────────────┤
│ 🟠 Near Deadline (≤ 2 days)             (N)  ▼  │
│   [UrgentCaseCard] ...                           │
└──────────────────────────────────────────────────┘
```

State:
- `activeFilter` — one of `'all' | 'pending_too_long' | 'payment_awaiting' | 'near_deadline'`
- Filtering is **client-side** (no extra API calls) — just show/hide sections based on filter
- All modals managed here (`isOfferModalOpen`, `isPaymentModalOpen`, `confirmModalState`)

#### [MODIFY] `src/hooks/useProjectMutations.js`
Add:
```js
approvePayment: useMutation({
  mutationFn: (projId) => apiClient.post(`/projects/${projId}/approve-payment`),
  onSuccess: () => {
    queryClient.invalidateQueries(['projects', 'urgent']);
    queryClient.invalidateQueries(['projects', 'urgent', 'count']);
  },
}),
```

---

## Design Rules (Must Follow)

1. **Design Tokens:** Every color, size, blur, shadow must go through `tokens.css` → `tailwind.config.js` → Tailwind class. **Never** write raw hex or pixel values in JSX.
2. **Premium UI:** Cards should use glassmorphism-style backgrounds (`bg-surface-elevated`, `backdrop-blur`), subtle shadows, and smooth hover transitions. No plain white boxes.
3. **Logging:** Use `structlog` in all new backend code. No `import logging`.
4. **Schemas:** Every new endpoint must have a typed Pydantic `response_model`.
5. **Repos only touch DB:** No MongoDB queries inside services or routers.
6. **Thin routers:** Routers extract params → call service → return result. No business logic.

---

## Verification Checklist

- [ ] `GET /api/projects/urgent` returns `urgent_reason` field on each item
- [ ] `GET /api/projects/urgent/count` returns `{"count": N}`
- [ ] `POST /api/projects/{id}/approve-payment` transitions project to `accepted`
- [ ] Sidebar badge shows correct count and hides when count = 0
- [ ] Three sections render on `/urgent`, each collapsible
- [ ] Filter tabs correctly show/hide sections (client-side, no re-fetch)
- [ ] `pending_too_long` card: clicking Send Offer opens OfferModal
- [ ] `payment_awaiting` card: clicking View Payment opens PaymentApprovalModal with download link
- [ ] PaymentApprovalModal: Approve → project disappears from urgent list after 2-min refresh or immediate invalidation
- [ ] `near_deadline` card: clicking Mark Finished opens confirm modal
- [ ] All new colors defined as tokens (no raw hex in JSX)
- [ ] No `import logging` in any new Python file
