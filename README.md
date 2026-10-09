# Game Tour DS

A responsive Next.js frontend and Python API for managing multiple game tournaments, student game choices, schedules, factions, leaderboards, and four data structures/algorithms learning phases.

## MySQL setup

1. Start MySQL and create a MySQL account that can create/use the `game_tour_ds` database and its tables. The app schema is created automatically on first API request; or run `backend/schema.sql` in Workbench.
2. Copy `backend/.env.example` to `backend/.env`, then set your private DB_USER and DB_PASSWORD. Set ADMIN_USERNAME and a strong ADMIN_PASSWORD in that same local file to provision the single administrator account. Student registration cannot create admin accounts. Keep `.env` private and uncommitted.
3. No tournaments, games, or other demo values are inserted. The tables begin empty. Students can register through the website.

## Run locally

Terminal 1:
```powershell
cd C:\game_tour_ds\backend
venv\Scripts\python.exe app.py
```
Terminal 2:
```powershell
cd C:\game_tour_ds\frontend
npm install
npm run dev
```
Open http://localhost:3000. API: http://localhost:8000.

## Features

- Student-only self-registration and authenticated student/admin pages.
- Admin creates multiple tournaments, schedules games with date/time, rounds, venue and participant capacity.
- Students submit 1–5 game choices once; the API refuses edits and enforces each game capacity.
- Dashboard greeting, personalized schedule, overall participant leaderboard and faction leaderboard.
- Dark theme, larger readable text, responsive navigation and empty states.
- Data structure/algorithm learning pages remain in the navigation.

## Data structures and algorithms phases

Phase 1: linked list insertion/deletion/traversal, linked-list stack and queue, arithmetic expressions.
Phase 2: binary tree traversals, binary search tree, graph representation, BFS and DFS.
Phase 3: linear/binary search, merge/selection sorting, efficiency comparison, integrated workflow.
Phase 4: greedy schedule selection integrated in the tournament workflow.
