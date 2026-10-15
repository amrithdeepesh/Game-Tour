from data_structures.queue import Queue


class Graph:
    """Adjacency-list graph for campus sports tournament venues."""

    def __init__(self, vertices=(), directed=False):
        self.adjacency = {}
        self.directed = directed
        for vertex in vertices:
            self.add_vertex(vertex)

    def add_vertex(self, vertex):
        self.adjacency.setdefault(vertex, [])

    def add_edge(self, first, second):
        self.add_vertex(first)
        self.add_vertex(second)
        if second not in self.adjacency[first]:
            self.adjacency[first].append(second)
        if not self.directed and first not in self.adjacency[second]:
            self.adjacency[second].append(first)

    def bfs(self, start):
        """Standard Breadth-First Search using custom Queue."""
        if start not in self.adjacency:
            return []
        visited = {start}
        order = []
        q = Queue()
        q.enqueue(start)
        while not q.is_empty():
            vertex = q.dequeue()
            order.append(vertex)
            for neighbor in self.adjacency.get(vertex, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    q.enqueue(neighbor)
        return order

    def bfs_detailed(self, start):
        """BFS with step-by-step queue states and execution trace for the Data Structures Lab."""
        if start not in self.adjacency:
            return {
                "order": [],
                "steps": [],
                "error": f"Starting venue '{start}' does not exist in graph.",
                "visited": [],
            }

        visited = {start}
        order = []
        steps = []
        q = Queue()
        q.enqueue(start)

        steps.append({
            "step": 1,
            "current": None,
            "action": f"Initialize BFS at venue '{start}'. Enqueue '{start}'.",
            "queue": q.display(),
            "visited": list(visited),
            "order": list(order),
        })

        step_counter = 2
        while not q.is_empty():
            vertex = q.dequeue()
            order.append(vertex)
            newly_discovered = []
            for neighbor in self.adjacency.get(vertex, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    q.enqueue(neighbor)
                    newly_discovered.append(neighbor)

            action_desc = f"Visited '{vertex}'."
            if newly_discovered:
                action_desc += f" Discovered and enqueued: {', '.join(newly_discovered)}."
            else:
                action_desc += " No unvisited adjacent venues."

            steps.append({
                "step": step_counter,
                "current": vertex,
                "action": action_desc,
                "queue": q.display(),
                "visited": list(visited),
                "order": list(order),
            })
            step_counter += 1

        return {
            "order": order,
            "steps": steps,
            "visited": list(visited),
            "total_vertices": len(self.adjacency),
        }

    def dfs(self, start):
        """Depth-First Search traversal."""
        if start not in self.adjacency:
            return []
        visited = set()
        order = []
        pending = [start]
        while pending:
            vertex = pending.pop()
            if vertex in visited:
                continue
            visited.add(vertex)
            order.append(vertex)
            pending.extend(reversed(self.adjacency.get(vertex, [])))
        return order

    def dfs_detailed(self, start):
        """DFS with step-by-step trace."""
        if start not in self.adjacency:
            return {"order": [], "steps": [], "error": f"Starting venue '{start}' not found."}
        visited = set()
        order = []
        steps = []
        stack = [start]
        step_idx = 1
        while stack:
            vertex = stack.pop()
            if vertex in visited:
                continue
            visited.add(vertex)
            order.append(vertex)
            to_add = [n for n in reversed(self.adjacency.get(vertex, [])) if n not in visited]
            stack.extend(to_add)
            steps.append({
                "step": step_idx,
                "current": vertex,
                "stack": list(stack),
                "visited": list(visited),
                "order": list(order),
                "action": f"Visit '{vertex}'. Push unvisited neighbors onto stack."
            })
            step_idx += 1
        return {"order": order, "steps": steps}

    def display(self):
        """Return adjacency list dictionary."""
        return dict(self.adjacency)

    def get_vertices(self):
        return list(self.adjacency.keys())

    def get_edges(self):
        edges = []
        seen = set()
        for u, neighbors in self.adjacency.items():
            for v in neighbors:
                if self.directed or (v, u) not in seen:
                    edges.append((u, v))
                    seen.add((u, v))
        return edges
