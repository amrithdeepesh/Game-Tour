# Arena Tournament

A responsive tournament management app for organizers and students. Organizers create tournaments, schedule games, set venue and capacity, record scores and placements, and review live participant and faction standings. Students register, see the schedule, and submit up to five game choices once.

The interface is organized around running a tournament. Its roster, check-in, scoring, search, ranking, and scheduling flows also demonstrate the required data structures and algorithms.

## Deploy with Docker Compose

1. Copy `.env.deploy.example` to `.env.deploy`.
2. Set unique private values for `DB_PASSWORD`, `MYSQL_ROOT_PASSWORD`, `ADMIN_USERNAME`, and `ADMIN_PASSWORD`. The administrator password must be at least 12 characters.
3. Build and start the production services:

```powershell
docker compose --env-file .env.deploy up --build -d
```

4. Open [http://localhost:3000](http://localhost:3000).

The stack contains a production Next.js server, the Python API, and MySQL 8.4. The database volume persists between container restarts. The first API request creates the empty application tables and the configured administrator account. No tournaments, games, participants, scores, or demo rows are seeded. Student accounts are created from the registration page; it cannot create administrator accounts.

Stop the services with:

```powershell
docker compose --env-file .env.deploy down
```

This keeps the database volume. Back up the volume before moving or replacing deployment hosts.

## Run locally for development

Configure the local MySQL credentials and administrator account in the private `backend/.env` file, then start the backend:

```powershell
cd C:\game_tour_ds\backend
venv\Scripts\python.exe app.py
```

In another terminal:

```powershell
cd C:\game_tour_ds\frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The Next.js proxy forwards `/api/*` to the Python service while keeping browser session cookies on the same site.

## Verify without connecting to MySQL

The algorithm and data structure tests use Python's standard test runner and mock the tournament data reads. They do not open a MySQL connection:

```powershell
cd C:\game_tour_ds\backend
venv\Scripts\python.exe -m unittest discover -s tests -v
```

The frontend can be type-checked and built without contacting MySQL:

```powershell
cd C:\game_tour_ds\frontend
npx tsc --noEmit
npm run build
```

## Course requirement coverage

| Requirement | Implementation in the running product |
|---|---|
| Project records and linked list insert, delete, traverse | Participant game-choice records are loaded into a linked list; the operations view supports adding and removing practice records and traversing the roster. |
| Stack and queue using linked nodes | Score/action history uses a LIFO stack; match check-in uses a FIFO queue. Both have interactive controls. |
| Basic expression handling with a stack | A shunting-yard operator stack evaluates arithmetic with precedence, parentheses, unary signs, and division-by-zero checks. |
| Binary tree, three traversals, and BST lookup | Tournament scores populate a binary search tree; the operations view shows inorder, preorder, postorder, and a BST search. |
| Graph representation and traversal | Arena venues are stored in an adjacency list and shown with breadth-first and depth-first routes. |
| Linear and binary search | Participants can be found by either method; binary search sorts names before searching. |
| One or two sorts and efficiency comparison | Selection sort and merge sort rank the leaderboard; the interface explains their O(n²) and O(n log n) running times. |
| Search and sorting in the project workflow | Search and sort run on the tournament participant leaderboard. |
| Greedy, dynamic programming, or backtracking problem | Earliest-finish interval scheduling selects a maximum compatible set of tournament fixtures and shows selected and skipped games. |
| Integration and final demonstration | The schedule planner uses real tournament fixtures; the operations pages provide linked-list, stack, queue, tree, graph, search, sort, and scheduling demonstrations. |

## Main product pages

- **Dashboard:** personalized greeting, selected games, schedule timeline, and quick links.
- **Games & schedule:** tournament creation, fixture scheduling, capacity, venue, and rounds.
- **My game choices:** one-time student selection, capped at five games.
- **Participant leaderboard:** game results and individual scores.
- **Faction leaderboard:** aggregate standings by faction.
- **Competition operations:** roster and venue structures used by tournament workflows.
- **Standings tools:** searching, sorting, efficiency comparison, and conflict-free scheduling.
