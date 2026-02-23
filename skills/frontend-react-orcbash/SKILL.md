---
name: frontend-react-orcbash
version: 1.0.0
last_updated: 2026-02-22
description: Use when structuring React frontend code using the Orc-BASH pattern (Orchestration, Business Logic, API, State Management, Hooks) — a hexagonal architecture that inverts dependency flow, maximizes reusability across pages, and makes every layer independently testable.
---

# Skill: Frontend React — Orc-BASH Pattern

Orc-BASH is hexagonal architecture for React frontends. The Orchestrator is the central hub that wires together four independent concerns and exposes a clean interface to the UI. Business Logic, API, and State Manager have **zero dependencies on each other** — the Orchestrator is the only layer that knows about all of them.

## Dependency Flow

```
Business Logic ──┐
API ─────────────┼──→ Orchestrator ──→ UI
State Manager ───┤
Hooks ───────────┘
```

**Arrow = dependency direction. UI depends only on Orchestrator. Orchestrator depends on everything else. Everything else depends on nothing.**

Business Logic, API, and State Manager import from shared `types/` only. They never import from each other. Dependencies flow inward through injection — passed as parameters in this priority order:
1. Data (simple values)
2. Functions (API calls, business logic methods)
3. Classes (store instances, service instances — last resort, harder to mock)

## File Structure

```
/features/<domain>/
├── types/
│   └── post.ts                    ← Shared types — the only cross-layer import
├── api/
│   └── postApi.ts                 ← Free functions, zero dependencies
├── logic/
│   └── PostService.ts             ← Class or free functions, zero dependencies
├── state/
│   ├── PostStatePort.ts           ← Interface defining all state operations
│   ├── PostStateAdapter.ts        ← Adapts concrete store to the port interface
│   └── postStore.ts               ← Zustand/Jotai/Redux store, zero dependencies
├── hooks/
│   └── usePost.ts                 ← Three sub-hooks: UI State, Business Logic, Integration
├── orchestrators/
│   ├── PostPageOrchestrator.ts    ← Imports adapter, not store directly
│   └── FeedPageOrchestrator.ts    ← Different wiring, reuses same hook
└── views/
    ├── PostPage.tsx               ← Uses PostPageOrchestrator only
    └── FeedPage.tsx               ← Uses FeedPageOrchestrator only
```

## The Six Layers

### Layer 1 — API (Free Functions)
Pure functions that make network requests. No class, no state, no dependencies.

```typescript
// api/postApi.ts
import type { Post } from '../types/post';

export const fetchPost = async (postId: string): Promise<Post> => {
  const response = await fetch(`/api/posts/${postId}`);
  if (!response.ok) throw new Error('Failed to fetch post');
  return response.json();
};
```

**Rule**: API throws on failure. It does not handle errors — that's the hook's job.

---

### Layer 2 — Business Logic (Service Class or Free Functions)
Validation, transformation, business rules. Zero dependencies outside `types/`.

Use a class when you need to group related operations or maintain configuration. Use free functions for simple stateless logic.

```typescript
// logic/PostService.ts
import type { Post } from '../types/post';

export class PostService {
  formatPost(post: Post): FormattedPost {
    return {
      ...post,
      excerpt: post.content.substring(0, 280) + (post.content.length > 280 ? '...' : ''),
      engagementScore: post.likes + (post.commentCount * 3),
    };
  }
}

export const postService = new PostService(); // Export singleton
```

**Rule**: Export a singleton. Orchestrators share the same instance — never instantiate in the orchestrator.

---

### Layer 3 — State Manager + Port/Adapter

The state layer has three parts that together implement hexagonal architecture for state:

**Port** — the interface contract that defines what state operations exist. Orchestrators and hooks depend on this interface, never on the concrete store.

```typescript
// state/PostStatePort.ts
import type { Post } from '../types/post';

export interface PostStatePort {
  post: Post | null;
  feed: string[];
  savePost: (post: Post) => void;
  updatePostLikes: (postId: string, likes: number) => void;
}
```

**Concrete Store** — the actual implementation. Zero dependencies outside `types/`. Has no knowledge of API or business logic.

```typescript
// state/postStore.ts — Zustand implementation (swappable)
import { create } from 'zustand';

export const usePostStore = create<PostState>((set) => ({
  posts: {},
  savePost: (post) => set((state) => ({ posts: { ...state.posts, [post.id]: post } })),
  updatePostLikes: (postId, likes) => set((state) => ({
    posts: { ...state.posts, [postId]: { ...state.posts[postId], likes, liked: true } }
  })),
}));
```

**Adapter** — a hook that maps the concrete store to the port interface. This is the only file that changes when swapping state managers. Orchestrators import the adapter, never the store directly.

```typescript
// state/PostStateAdapter.ts
import { usePostStore } from './postStore';
import type { PostStatePort } from './PostStatePort';

export const usePostStateAdapter = (postId: string): PostStatePort => {
  const post = usePostStore(s => s.posts[postId] ?? null);
  const feed = usePostStore(s => s.feed);
  const savePost = usePostStore(s => s.savePost);
  const updatePostLikes = usePostStore(s => s.updatePostLikes);

  return { post, feed, savePost, updatePostLikes };
};
```

**To switch from Zustand to Jotai**: replace `postStore.ts` and update `PostStateAdapter.ts` to use Jotai atoms. The port interface, orchestrators, and hooks are unchanged.

**Rule**: Orchestrators import `usePostStateAdapter`, never `usePostStore` directly.

---

### Layer 4 — Hooks (Three Sub-Hooks, Dependencies Injected)

The hook layer has three sub-hooks with distinct responsibilities:

**UI State Hook** — ephemeral view state only (modals, spinners, form input). No async, no business logic.

```typescript
const usePostUiState = () => {
  const [uiState, setUiState] = useState({
    isLiking: false,
    showCommentModal: false,
    commentText: '',
  });
  const setLiking = useCallback((v: boolean) => setUiState(s => ({ ...s, isLiking: v })), []);
  const openModal = useCallback(() => setUiState(s => ({ ...s, showCommentModal: true })), []);
  return { uiState, actions: { setLiking, openModal } };
};
```

**Business Logic Hook** (optional) — a light React wrapper for service methods that need lifecycle integration: `useEffect` triggered by business rule outcomes, or local React state tied to a service computation. Use when a service method needs to interact with React's lifecycle, not just transform data.

```typescript
const usePostLogic = ({ post, formatPost }: { post: Post | null; formatPost: (p: Post) => FormattedPost }) => {
  // Memoize expensive business logic computation — needs React's useMemo
  const formattedPost = useMemo(
    () => post ? formatPost(post) : null,
    [post, formatPost]
  );
  return { formattedPost };
};
```

**Integration Hook** — composes the UI State Hook and Business Logic Hook, coordinates async operations with all injected dependencies. This is the exported hook that orchestrators use.

```typescript
// hooks/usePost.ts
export interface UsePostDependencies {
  post: Post | null;
  fetchPost: (postId: string) => Promise<Post>;
  likePost: (postId: string) => Promise<{ likes: number }>;
  formatPost: (post: Post) => FormattedPost;
  savePost: (post: Post) => void;
  updatePostLikes: (postId: string, likes: number) => void;
}

export const usePost = (postId: string, deps: UsePostDependencies) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const ui = usePostUiState();                          // UI State sub-hook
  const logic = usePostLogic({                          // Business Logic sub-hook
    post: deps.post,
    formatPost: deps.formatPost,
  });

  const fetchPost = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const fetched = await deps.fetchPost(postId);
      deps.savePost(fetched);
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, [postId, deps]);

  const like = useCallback(async () => {
    ui.actions.setLiking(true);
    try {
      const { likes } = await deps.likePost(postId);
      deps.updatePostLikes(postId, likes);
    } catch (err) {
      setError(err as Error);
    } finally {
      ui.actions.setLiking(false);
    }
  }, [postId, deps, ui.actions]);

  return {
    post: logic.formattedPost,       // from Business Logic sub-hook
    isLoading,
    error,
    uiState: ui.uiState,             // from UI State sub-hook
    actions: { fetchPost, like, openModal: ui.actions.openModal },
  };
};
```

**Rule**: The `UsePostDependencies` interface is the hook's contract. Every dependency can be mocked. If this interface exceeds 8–10 fields, the hook is doing too many things — split it.

---

### Layer 5 — Orchestrator (Per Page)
The only layer that imports from all others. Uses the state adapter (not the store). Injects dependencies into the hook. Exposes a clean interface to UI.

```typescript
// orchestrators/PostPageOrchestrator.ts
import * as postApi from '../api/postApi';
import { postService } from '../logic/PostService';
import { usePostStateAdapter } from '../state/PostStateAdapter';   // ← adapter, not store
import { usePost } from '../hooks/usePost';

export const usePostPageOrchestrator = (postId: string) => {
  const state = usePostStateAdapter(postId);   // all state via adapter

  const hook = usePost(postId, {
    post: state.post,
    fetchPost: postApi.fetchPost,
    likePost: postApi.likePost,
    formatPost: postService.formatPost.bind(postService),
    savePost: state.savePost,
    updatePostLikes: state.updatePostLikes,
  });

  useEffect(() => {
    if (!state.post) hook.actions.fetchPost();
  }, [state.post]);

  return {
    post: hook.post,
    isLoading: hook.isLoading,
    error: hook.error,
    isLiking: hook.uiState.isLiking,
    onLike: hook.actions.like,
  };
};
```

**Rule**: If an orchestrator exceeds ~200–300 lines, split it or extract shared wiring into a factory function.

---

### Layer 6 — UI (Orchestrator Only)
UI sees nothing below the orchestrator.

```typescript
// views/PostPage.tsx
export const PostPage = ({
  postId,
  useOrchestrator = usePostPageOrchestrator,
}: {
  postId: string;
  useOrchestrator?: typeof usePostPageOrchestrator;
}) => {
  const { post, isLoading, error, isLiking, onLike } = useOrchestrator(postId);

  if (error) return <ErrorView error={error} />;
  if (isLoading || !post) return <LoadingView />;
  return <Card title={post.title} onLike={onLike} isLiking={isLiking} />;
};
```

Injecting the orchestrator as a prop with a default enables full UI testing without any state or API setup.

## Error Handling

| Layer | Responsibility |
|---|---|
| API | Throws on HTTP failure |
| Hook | Catches, sets `error` state |
| Orchestrator | Exposes `error` to UI |
| UI | Renders error state |

## DDD Scaling

Each domain gets its own complete BASH structure:

```
/features/
├── posts/    ← types/ api/ logic/ state/ hooks/ orchestrators/ views/
├── comments/ ← types/ api/ logic/ state/ hooks/ orchestrators/ views/
└── payments/ ← types/ api/ logic/ state/ hooks/ orchestrators/ views/
```

Cross-domain communication happens through orchestrators, not between domain internals.

## When to Use

✅ Use Orc-BASH when:
- Multiple pages need the same hook logic (feed, profile, search all show posts)
- Cross-feature coordination required (liking updates feed, profile, analytics)
- Web + mobile sharing the same business logic (80% code reuse — only UI layer differs)
- Large team where layers are owned by different people
- State manager swap is a realistic future concern

❌ Don't use Orc-BASH when:
- Simple CRUD feature used in one place — no reusability to gain
- Rapid prototyping — too much ceremony
- Small team (1–3 devs) on a short-lived feature

**Decision tree:**
- Max reusability + minimal dependency → Orc-BASH
- Speed and simplicity → SUIF (fusion hook)
- Enterprise-scale, class-heavy → SHARP

## Anti-Patterns

**Importing the store directly in the orchestrator**: Defeats the port/adapter pattern. When state manager changes, every orchestrator breaks. Always import the adapter.

**God orchestrator**: Orchestrator exceeding 200–300 lines. Split or extract a shared wiring factory function.

**Instantiating in the orchestrator**: `new PostService()` creates a new instance per render. Use exported singletons.

**Cross-layer imports**: Business logic importing from state, hooks importing from API directly. All cross-layer wiring belongs in the orchestrator only.

**Skipping the Business Logic Hook when React lifecycle is needed**: Calling service methods directly in the Integration Hook without wrapping in `useMemo`/`useCallback` when those methods have referential equality implications. Use the Business Logic sub-hook for any service interaction that needs lifecycle awareness.

**Verbose dependency interface as ignored signal**: `UsePostDependencies` growing past 8–10 fields means the hook has too many responsibilities. Split it into domain-specific hooks.

## Full Implementation Reference

See `AI-Dev-Shop/skills/frontend-react-orcbash/references/` for complete working examples:
- `post-feature-example.md` — full Reddit posts feature with all 6 layers including state adapter
