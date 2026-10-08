# Game Tour DS · Tournament & Live Leaderboard

A Python API and Next.js dashboard for a game tournament, with interactive demonstrations aligned to the four data-structures-and-algorithms phases.

## Run locally

Requirements: Python 3.10+ and Node.js 20+.

1. In a terminal, start the API:
   `cd C:\game_tour_ds\backend`
   `python app.py`
2. In another terminal, start the frontend:
   `cd C:\game_tour_ds\frontend`
   `npm install`
   `npm run dev`
3. Open http://localhost:3000. The API listens at http://localhost:8000.

The backend uses only Python's standard library. Participant registrations are held in memory and reset when the API restarts. `backend/schema.sql` provides the planned MySQL schema; configure a MySQL connection and persistence layer before using this for durable or multi-user records.

## Phase coverage

- **Phase 1 — Linear structures:** linked-list participant insertion/traversal/deletion, linked-list-backed stack and queue, safe arithmetic expression evaluation.
- **Phase 2 — Hierarchical and graph:** binary search tree with inorder/preorder/postorder methods; arena adjacency graph with BFS and DFS.
- **Phase 3 — Searching and sorting:** linear and binary search implementations, selection and merge sort implementations, efficiency comparison, integrated leaderboard workflow.
- **Phase 4 — Problem solving:** greedy interval scheduling implementation for non-overlapping matches, shown in the algorithm lab.

## API

- `GET /api/health`
- `GET /api/dashboard`, `GET /api/players`
- `GET /api/demo`
- `POST /api/players` with `{"name":"Player"}`
- `POST /api/expression` with `{"expression":"1200 + 40 * 2"}`
- `POST /api/greedy` with optional `{"matches":[...]}`
- `POST /api/search` with `{"method":"linear|binary","query":"Mira Patel"}`
- `POST /api/sort` with `{"method":"selection|merge"}`

The supplied project directory did not contain a Git repository or remote when inspected. No GitHub remote is configured here.
