# ARENA — Data Structures & Algorithms Implementation Guide

This document outlines the complete mapping and implementation details of all four development phases in the ARENA Tournament Management System across both the **Backend Codebase** and the **Frontend Browser UI**.

---

## Quick Reference Summary Table

| Phase | Component / Requirement | Backend Source Location | Frontend / Browser UI Location | Real-World Application Use-Case |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 1** | **Singly Linked List** | `backend/data_structures/linked_list.py`<br>`backend/data_structures/node.py` | • `/structures` → **"Roster Desk: Participant list"**<br>• `/lab` (Tab 1) → **"Participant Lineup Manager"** | Dynamic student athlete lineup order & scratch withdrawals |
| **Phase 1** | **Linked List Operations** (Insert, Delete, Traverse) | `backend/data_structures/linked_list.py`<br>`insert_at_start/end/position()`, `delete_by_id/position()` | • `/structures` → **"Add / Remove from practice list"**<br>• `/lab` (Tab 1) → **"Add Athlete (Start/End/Index)"** | Adding athletes to heat lineups, scratching players, rendering linked node arrows (`→`) |
| **Phase 1** | **Stack using Linked List** | `backend/data_structures/stack.py`<br>`Stack` (`push`, `pop`, `peek`) | • `/structures` → **"Score desk activity"** Card<br>• `/lab` (Tab 1) → **"Activity History & Undo Stack"** | Score desk audit trail, logging recent updates, undoing score entries |
| **Phase 1** | **Queue using Linked List** | `backend/data_structures/queue.py`<br>`Queue` (`enqueue`, `dequeue`, `peek`) | • `/structures` → **"Player check-in line"** Card<br>• `/lab` (Tab 1) → **"Live Check-In Desk Queue"** | Match arrival desk, calling next waiting athlete, event waiting list |
| **Phase 1** | **Simple Expression Handling using Stack** | `backend/algorithms/expression_handler.py`<br>`evaluate_simple_expression()` | • `/structures` → **"Points calculator"** Card<br>• `/lab` (Tab 1) → **"Score Formula Calculator"** | Computing complex score adjustments and tie-breaker formulas with stack precedence |
| **Phase 2** | **Binary Tree for Structured Storage** | `backend/data_structures/tree.py`<br>`TreeNode`, `BinarySearchTree` | • `/structures` → **"Scoreboard review"** Card<br>• `/lab` (Tab 2) → **"Tournament Elimination Bracket"** | Hierarchical knockout bracket structure (Quarters → Semis → Finals) |
| **Phase 2** | **Tree Traversals** (Inorder, Preorder, Postorder) | `backend/data_structures/tree.py`<br>`inorder()`, `preorder()`, `postorder()` | • `/structures` → **"Scoreboard review → See other views"**<br>• `/lab` (Tab 2) → **"Bracket Tree Match Inspector"** | Low-to-high point sorting (inorder) and hierarchical round serialization |
| **Phase 2** | **Binary Search Tree (BST)** | `backend/data_structures/tree.py`<br>`insert()`, `contains()`, `delete()` | • `/structures` → **"Scoreboard review: Example lookup"**<br>• `/lab` (Tab 2) → **"Point Search & Extrema Ledger"** | $O(\log n)$ score point lookups and min/max score discovery |
| **Phase 2** | **Basic Graph Representation** | `backend/data_structures/graph.py`<br>`Graph` (Adjacency List) | • `/structures` → **"Sample venue map"** Card<br>• `/lab` (Tab 2) → **"Interactive Canvas Game Flow Map & Navigator"** | Campus venue connectivity layout (Cricket Ground, Basketball Court, Volleyball Court, Badminton Court, Indoor Sports Complex, Tennis Court, Athletics Track) |
| **Phase 2** | **Simple Traversal — BFS** | `backend/data_structures/graph.py`<br>`bfs()`, `bfs_detailed()` | • `/structures` → **"Routes between your places"**<br>• `/lab` (Tab 2) → **"Canvas BFS Animated Path Finder & Navigator"** | Shortest path route between campus tournament venues |
| **Phase 3** | **Linear Search** | `backend/algorithms/search_sort.py`<br>`linear_search()` | • `/algorithms` → **"Participant Search (Linear)"**<br>• `/lab` (Tab 3) → **"Player Finder: Sequential Search"** | Scanning unsorted player lists to verify registrations |
| **Phase 3** | **Binary Search** | `backend/algorithms/search_sort.py`<br>`binary_search()` | • `/algorithms` → **"Participant Search (Binary)"**<br>• `/lab` (Tab 3) → **"Player Finder: Binary Search Mode"** | $O(\log n)$ instant search of athletes in sorted standings |
| **Phase 3** | **Merge Sort** | `backend/algorithms/search_sort.py`<br>`merge_sort()` | • `/algorithms` → **"Tournament Standings (Merge Sort)"**<br>• `/lab` (Tab 3) → **"Ranked Standings & Sort Benchmark"** | Stable $O(n \log n)$ ordering of leaderboard points & faction tallies |
| **Phase 4** | **Greedy Algorithm Technique** | `backend/algorithms/problem_solver.py`<br>`schedule_maximum_matches()` | • `/schedule` → **"Greedy Schedule Optimizer"**<br>• `/lab` (Tab 4) → **"Conflict-Free Event Scheduler"** | Earliest-finish-time interval scheduling to maximize match throughput |
| **Phase 4** | **Application Flow Integration** | `backend/app.py` (`phase_demo()`)<br>`backend/database.py` | • `/structures` (Operations Desk)<br>• `/schedule` (Venue Timetable Lanes)<br>• `/dashboard` (Live Timeline) | Seamless end-to-end operational pipeline connecting MySQL data to DS algorithms |
| **Phase 4** | **Testing & Algorithm Demonstration** | `backend/tests/test_phase_requirements.py`<br>`test_arena_extensions.py` | • `/lab` (Full Interactive 4-Tab Suite)<br>• `/structures` (Live Working Demo Desk) | Automated terminal test verification and live interactive browser testing tools |

---

## Detailed Breakdown: Backend & Browser UI Positions

### Phase 1: Fundamental Linear Data Structures & Expressions

#### 1. Singly Linked List & Basic Operations (Insert, Delete, Traverse)
- **Backend Source**: `backend/data_structures/linked_list.py` & `backend/data_structures/node.py`
- **Class**: `LinkedList`, `Node`
- **Key Methods**: `insert_at_start()`, `insert_at_end()`, `insert_at_position()`, `delete_by_student_id()`, `delete_at_position()`, `delete_by_value()`, `traverse()`, `search()`.
- **Browser UI Locations**:
  1. **`/structures` (Game Day Tools → Roster Desk)**:
     - **Route**: `http://localhost:3000/structures`
     - **Component**: `<Card className="tools-card">` with section heading **"Participant game choices"**.
     - **Visual Layout**: Renders an interactive linked node track with visual arrows: `[ATH-101 | Rohan] → [ATH-102 | Priya] → [ATH-103 | Vikram]`.
     - **Interactive Controls**: Inputs for *Player ID* and *Participant Name*, buttons for **"Add to practice list"**, **"Remove from practice list"**, and **"Review roster order"**.
  2. **`/lab` (Search & Find Lab → Tab 1: "lineup")**:
     - **Route**: `http://localhost:3000/lab`
     - **Tab**: **"Lineups & Desk"** (1st Tab)
     - **Component**: **"Event Lineups (Singly Linked List)"** panel.
     - **Interactive Controls**: Allows inserting athletes at Head, Tail, or specific Index, deleting by ID, and moving athletes within the line.
- **Automated Test**: `PhaseOneTests.test_linked_list_insert_traverse_delete_and_tail_recovery`.

---

#### 2. Stack using Linked List
- **Backend Source**: `backend/data_structures/stack.py`
- **Class**: `Stack` (implemented with singly linked nodes tracking `top`).
- **Key Methods**: `push(value)`, `pop()`, `peek()`, `is_empty()`, `to_list()`.
- **Browser UI Locations**:
  1. **`/structures` (Score Desk Activity)**:
     - **Route**: `http://localhost:3000/structures`
     - **Component**: Left card under **"Game-Day Operations"**.
     - **Visual Layout**: Displays `<div className="stack-card">` with badge **"LATEST UPDATE"** highlighting the top element.
     - **Interactive Controls**: **"Log a score update"** (`push`) and **"Undo latest update"** (`pop`).
  2. **`/lab` (Tab 1: "lineup")**:
     - **Route**: `http://localhost:3000/lab`
     - **Component**: **"Recent Score Changes & Undo (LIFO Stack)"** widget showing a vertical action card stack with instant pop/push controls.
- **Automated Test**: `PhaseOneTests.test_linked_stack_is_lifo`.

---

#### 3. Queue using Linked List
- **Backend Source**: `backend/data_structures/queue.py`
- **Class**: `Queue` (singly linked nodes tracking both `front` and `rear` pointers).
- **Key Methods**: `enqueue(value)`, `dequeue()`, `peek()`, `is_empty()`, `to_list()`.
- **Browser UI Locations**:
  1. **`/structures` (Player Check-In Line)**:
     - **Route**: `http://localhost:3000/structures`
     - **Component**: Right card under **"Game-Day Operations"**.
     - **Visual Layout**: `<div className="queue-card">` with badge **"UP NEXT"** showing the front player.
     - **Interactive Controls**: Input field for *Player or team name*, button **"Join check-in line"** (`enqueue`), and button **"Call next player"** (`dequeue`).
  2. **`/lab` (Tab 1: "lineup")**:
     - **Route**: `http://localhost:3000/lab`
     - **Component**: **"Live Check-In Desk (FIFO Queue)"** card displaying the queue depth badge, next called athlete card, and waiting lineup queue chips.
- **Automated Test**: `PhaseOneTests.test_linked_queue_is_fifo_and_recovers_after_empty`.

---

#### 4. Simple Expression Handling using Stack
- **Backend Source**: `backend/algorithms/expression_handler.py`
- **Functions**: `evaluate_simple_expression()`, `evaluate_expression_detailed()`.
- **Browser UI Locations**:
  1. **`/structures` (Points Calculator)**:
     - **Route**: `http://localhost:3000/structures`
     - **Component**: Card with heading **"Points calculator"** under the **"SCORE DESK"** section.
     - **Visual Layout**: Input field prefilled with sample expression (e.g., `1200 + 40 * 2`), button **"Calculate"**, and formatted answer badge.
  2. **`/lab` (Tab 1: "lineup")**:
     - **Route**: `http://localhost:3000/lab`
     - **Component**: **"Tournament Score Calculator (Shunting-Yard & Stack)"** panel.
     - **Visual Layout**: Includes formula input presets (`(3 * 3) + 1`, `100 - (15 * 4)`), calculates dynamically via `POST /api/expression`, and displays step-by-step token and stack evaluation traces.
- **Automated Test**: `PhaseOneTests.test_stack_based_expression_evaluation`.

---

### Phase 2: Hierarchical Trees & Graph Structures

#### 1. Binary Tree for Structured Storage & BST
- **Backend Source**: `backend/data_structures/tree.py`
- **Classes**: `TreeNode`, `BinarySearchTree`, `TournamentBinaryTree`.
- **Key Methods**: `insert()`, `contains()`, `delete()`, `find_min()`, `find_max()`.
- **Browser UI Locations**:
  1. **`/structures` (Scoreboard Review)**:
     - **Route**: `http://localhost:3000/structures`
     - **Component**: Right card under **"SCORE DESK"** section.
     - **Visual Layout**: Shows points ordered from low to high (`inorder()`), and example lookup search status (`Found / Did not find`).
  2. **`/lab` (Tab 2: "bracket")**:
     - **Route**: `http://localhost:3000/lab`
     - **Tab**: **"Brackets & Venues"** (2nd Tab)
     - **Component**: **"Tournament Elimination Bracket (Binary Tree)"** rendering knockout tree rounds (Quarterfinals → Semifinals → Championship Final).
- **Automated Test**: `PhaseTwoTests.test_bst_storage_traversals_and_search`.

---

#### 2. Tree Traversals (Inorder, Preorder, Postorder)
- **Backend Source**: `backend/data_structures/tree.py`
- **Methods**: `inorder()`, `preorder()`, `postorder()`.
- **Browser UI Locations**:
  1. **`/structures` (Scoreboard Review Details)**:
     - **Route**: `http://localhost:3000/structures`
     - **Component**: Expandable `<details className="tools-details">` inside **"Scoreboard review"**.
     - **Visual Display**:
       - **Inorder**: *Low to high point values*
       - **Preorder**: *Start at each parent first*
       - **Postorder**: *Visit children before parent*
  2. **`/lab` (Tab 2: "bracket")**:
     - **Route**: `http://localhost:3000/lab`
     - **Component**: Traversal chips showing pre-order match hierarchy and post-order result completion.
- **Automated Test**: `PhaseTwoTests.test_bst_storage_traversals_and_search`.

---

#### 3. Basic Graph Representation & Simple Traversal (BFS)
- **Backend Source**: `backend/data_structures/graph.py`
- **Class**: `Graph` (Adjacency List with `bfs()`, `bfs_detailed()`, `dfs()`).
- **Browser UI Locations**:
  1. **`/structures` (Sample Venue Map)**:
     - **Route**: `http://localhost:3000/structures`
     - **Component**: Card under **"EVENT SPACES: Plan movement around the venue"**.
     - **Visual Layout**: CSS node-and-edge layout linking the 7 official venues: `Cricket Ground`, `Basketball Court`, `Volleyball Court`, `Badminton Court`, `Indoor Sports Complex`, `Tennis Court`, and `Athletics Track`.
     - **Interactive Controls**: Dropdown selects for *Starting place* and *Destination*, which dynamically compute and render all BFS shortest routes and alternative routes.
  2. **`/lab` (Tab 2: "bracket")**:
     - **Route**: `http://localhost:3000/lab`
     - **Tab**: **"Brackets & Venues"** (2nd Tab)
     - **Component**: **"Interactive Campus Game Flow Map & Navigator"** featuring an **HTML5 `<canvas>`** drawing venue nodes, active match lines, and an interactive BFS Route Navigator calculating and animating shortest paths between origin and destination grounds.
- **Automated Test**: `PhaseTwoTests.test_graph_adjacency_list_bfs_dfs_and_directed_edges`.

---

### Phase 3: Searching & Sorting Algorithms

#### 1. Linear Search & Binary Search
- **Backend Source**: `backend/algorithms/search_sort.py`
- **Functions**: `linear_search()`, `linear_search_detailed()`, `binary_search()`, `binary_search_detailed()`.
- **Browser UI Locations**:
  1. **`/algorithms` (Search & Find Operations)**:
     - **Route**: `http://localhost:3000/algorithms`
     - **Component**: **"Find student athletes"** card.
     - **Interactive Controls**: Text input for student query, method selector buttons for **"Linear search (O(n))"** and **"Binary search (O(log n))"**, and a **"Find athlete"** action button.
     - **Visual Result**: Displays search result card, comparisons count, and execution time.
  2. **`/lab` (Tab 3: "finder")**:
     - **Route**: `http://localhost:3000/lab`
     - **Tab**: **"Player Finder & Standings"** (3rd Tab)
     - **Component**: **"Athlete Search Comparison Desk"** with side-by-side execution comparison between Linear Search and Binary Search, highlighting index match positions.
- **Automated Test**: `PhaseThreeTests.test_linear_and_binary_search`.

---

#### 2. Merge Sort
- **Backend Source**: `backend/algorithms/search_sort.py`
- **Functions**: `merge_sort()`, `merge_sort_detailed()`, `selection_sort()`, `benchmark_search_sort()`.
- **Browser UI Locations**:
  1. **`/algorithms` (Tournament Standings Sorter)**:
     - **Route**: `http://localhost:3000/algorithms`
     - **Component**: **"Sort tournament standings"** card.
     - **Interactive Controls**: Buttons to toggle between **"Merge sort (stable, O(n log n))"** and **"Selection sort (O(n²))"**.
     - **Visual Display**: Renders ordered athlete standings with badges for points, faction, and rank.
  2. **`/lab` (Tab 3: "finder")**:
     - **Route**: `http://localhost:3000/lab`
     - **Tab**: **"Player Finder & Standings"** (3rd Tab)
     - **Component**: **"Faction & Athlete Ranked Standings"** with a **"Run Merge Sort (O(N log N))"** button, sorted podium cards, and runtime benchmark comparison.
- **Automated Test**: `PhaseThreeTests.test_selection_and_merge_sorts_are_correct_and_non_mutating`.

---

### Phase 4: Applied Problem Solving, Integration & Demonstration

#### 1. Greedy Technique Implementation
- **Backend Source**: `backend/algorithms/problem_solver.py`
- **Functions**: `schedule_maximum_matches()`, `schedule_tournament_events()`.
- **Algorithm**: Earliest Finish Time Greedy Interval Scheduling.
- **Browser UI Locations**:
  1. **`/schedule` (Venue Lane Timetable & Conflict Solver)**:
     - **Route**: `http://localhost:3000/schedule`
     - **Component**: **"Schedule Optimizer & Conflict Resolution"** banner and timetable lane renderer.
     - **Visual Display**: Visualizes match time blocks across Court 1, Court 2, Stadium, and Track. Overlapping conflicts are flagged and resolved by the greedy scheduler.
  2. **`/lab` (Tab 4: "schedule")**:
     - **Route**: `http://localhost:3000/lab`
     - **Tab**: **"Schedule Optimizer"** (4th Tab)
     - **Component**: **"Conflict-Free Match Scheduler (Greedy Algorithm)"** panel.
     - **Interactive Controls**: Button **"Optimize Today's Fixtures (Greedy Selection)"**, which executes `schedule_maximum_matches()` via `POST /api/schedule/solve` and renders non-overlapping match cards.
- **Automated Test**: `PhaseFourTests.test_greedy_scheduler_selects_maximum_compatible_intervals`.

---

#### 2. Application Flow Integration
- **Backend Source**: `backend/app.py` (`phase_demo()`), `backend/database.py` (`_check_venue_conflict()`).
- **REST Endpoints**:
  - `GET /api/demo`: Returns bundled state of all custom structures for the frontend.
  - `POST /api/schedule/solve`: Runs the greedy interval scheduler on match intervals.
  - `POST /api/expression`: Evaluates formulas via the stack calculator.
  - `POST /api/search`: Executes linear/binary search over participant records.
  - `POST /api/sort`: Executes merge/selection sort over standings.
- **Browser UI Locations**:
  - **`/structures`**: Connected to `/api/demo` to hydrate Linked List, Stack, Queue, Tree, and Graph states.
  - **`/lab`**: Master interactive hub accessing all 4 phase endpoints simultaneously.
  - **`/schedule`**: Connected to `/api/schedule/solve` for dynamic match rescheduling.
- **Automated Test**: `PhaseFourTests.test_application_demo_integrates_structures_without_mysql`.

---

#### 3. Final Testing & Interactive Demonstrations
- **Automated Terminal Execution**:
  ```powershell
  # Run all 33 Phase 1-4 tests
  .\backend\venv\Scripts\python.exe -m unittest discover -s backend/tests -v
  ```
- **Browser Demonstration Guide**:
  - **`/lab`**: Complete interactive showcase demonstrating:
    - *Tab 1*: Linked List manipulation, Check-in Queue, Stack calculator with token trace.
    - *Tab 2*: HTML5 Canvas Graph BFS path animation and Binary Bracket Tree.
    - *Tab 3*: Linear Search vs Binary Search comparison & Merge Sort standings.
    - *Tab 4*: Greedy Interval Scheduler maximizing non-overlapping matches.
  - **`/structures`**: Operational game day desk with working Stack, Queue, Linked List, BST traversals, and Graph path routes.
  - **`/algorithms`**: Standalone educational desk for search and sort runtime comparisons.
  - **`/schedule`**: Production multi-venue match scheduling timetable.
