# Game Tour DS · Tournament & Live Leaderboard

A Python API and Next.js dashboard for a game tournament, with interactive demonstrations aligned to the four data-structures-and-algorithms phases. Tournament games, student participation, schedules, scores, and match results are stored in MySQL.

## First-time MySQL setup

1. Make sure the local MySQL server is running and create the `game_tour_ds` database. You can run `backend/schema.sql` in MySQL Workbench or the MySQL command-line client. The script only creates the app's prefixed `tournament_*` tables; it does not delete or alter the older unprefixed project tables.
2. Create a MySQL account with access to `game_tour_ds`. The API needs permission to create/use its tables and to select, insert, update, and delete rows.
3. Copy `backend/.env.example` to `backend/.env` and set your local connection values. Keep the password in that file and do not commit or share it:
   ```text
   DB_HOST=127.0.0.1
   DB_PORT=3306
   DB_NAME=game_tour_ds
   DB_USER=your-local-mysql-user
   DB_PASSWORD=your-local-mysql-password
   ```
4. Install the backend dependency once:
   `cd C:\game_tour_ds\backend`
   `venv\Scripts\python.exe -m pip install -r requirements.txt`
   If using the system Python instead, run `python -m pip install -r requirements.txt`.

The API creates any missing `tournament_*` tables at startup/first request and adds example games, players, and fixtures only when all four new `tournament_*` tables are empty. It never drops existing tables or reseeds non-empty data. If the MySQL settings are missing or invalid, API requests return an actionable error instead of silently falling back to volatile memory.

## Run locally

1. Start the API:
   `cd C:\game_tour_ds\backend`
   `venv\Scripts\python.exe app.py`
2. In another terminal, start the frontend:
   `cd C:\game_tour_ds\frontend`
   `npm install`
   `npm run dev`
3. Open http://localhost:3000. The API listens at http://localhost:8000.

## Dashboard and roles

The overview keeps to three quick counts, role-specific next steps, and a compact game leaderboard. The Admin/Student switch changes the demonstration views; it is not account authentication or a security boundary.

- **Admin:** publish games, review and approve participation requests, record winners and both participants' scores.
- **Student:** choose a game, submit participation details, and check the game-by-game leaderboard.
- **Leaderboard:** shows each game's top scorer and highlights first and second place.
- **Theme and layout:** saved light/dark theme, larger text, and responsive pages.

## Phase coverage

- **Phase 1 — Linear structures:** linked-list participant insertion/traversal/deletion, linked-list-backed stack and queue, safe arithmetic expression evaluation.
- **Phase 2 — Hierarchical and graph:** binary search tree with inorder/preorder/postorder; arena adjacency graph with BFS and DFS.
- **Phase 3 — Searching and sorting:** linear and binary search, selection and merge sort, efficiency comparison, integrated leaderboard workflow.
- **Phase 4 — Problem solving:** greedy interval scheduling for non-overlapping matches, shown in the algorithm lab.

## API

- `GET /api/health`
- `GET /api/dashboard`, `GET /api/players`
- `GET /api/demo`
- `GET /api/games`, `POST /api/games`
- `POST /api/players`, `PATCH /api/players/{student_id}/status`, `DELETE /api/players/{student_id}`
- `GET /api/leaderboard?game=Chess`
- `GET /api/results`, `POST /api/results`
- `POST /api/expression`, `POST /api/greedy`, `POST /api/search`, `POST /api/sort`
