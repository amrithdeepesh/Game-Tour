# Tournament backend guide

## What runs

- `app.py` starts the Python HTTP API on port 8000.
- `database.py` connects to MySQL, creates or updates the tables, and performs database reads and writes.
- The Next.js website sends requests to the API. The backend does not contain frontend pages.

## Request flow

1. An API method receives a request in `Handler` in `app.py`.
2. The handler checks the request body, browser origin, and user role.
3. A function in `database.py` validates business rules and reads or updates MySQL.
4. The handler returns a JSON response.

## File map

- `data_structures/node.py`: basic node used by the linked list, stack, and queue.
- `data_structures/linked_list.py`: insert, delete, and traverse participant records.
- `data_structures/stack.py`: last-in, first-out operations.
- `data_structures/queue.py`: first-in, first-out operations.
- `data_structures/tree.py`: binary search tree, lookup, and three traversals.
- `data_structures/graph.py`: adjacency-list graph with breadth-first and depth-first traversal.
- `algorithms/expression_handler.py`: parses and evaluates basic arithmetic with an operator stack.
- `algorithms/search_sort.py`: linear search, binary search, selection sort, and merge sort.
- `algorithms/problem_solver.py`: greedy selection of non-overlapping match intervals.
- `tests/`: automated checks for DSA behavior, validation, and application integration.
- `schema.sql`: readable empty MySQL schema. The runtime also applies safe migrations and creates the configured admin account.

## Main database tables

- `users`: admin and student accounts, including each participant's faction.
- `tournaments`: tournament details and scoring rules.
- `games`: scheduled games, venues, capacity, and tournament relationship.
- `game_choices`: students' submitted choices.
- `results`: scores, places, statuses, and awarded leaderboard points.
- `sessions`: hashed sign-in session tokens.
- `result_audit`: before-and-after history for recorded results.

## Run locally

Start MySQL, then open a terminal in this folder:

```powershell
.\venv\Scripts\python.exe app.py
```

Run the backend checks in another terminal:

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Configuration and account safety

Database credentials and the configured admin login belong in `.env`, which must stay private. Passwords are stored as salted PBKDF2 hashes. Students can self-register; the admin account is provisioned from the configured admin credentials.
