from collections import deque


class Graph:
    """Adjacency-list graph for connected tournament venues."""

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
        if start not in self.adjacency:
            return []
        visited, order = {start}, []
        pending = deque([start])
        while pending:
            vertex = pending.popleft()
            order.append(vertex)
            for neighbor in self.adjacency[vertex]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    pending.append(neighbor)
        return order

    def dfs(self, start):
        if start not in self.adjacency:
            return []
        visited, order, pending = set(), [], [start]
        while pending:
            vertex = pending.pop()
            if vertex in visited:
                continue
            visited.add(vertex)
            order.append(vertex)
            pending.extend(reversed(self.adjacency[vertex]))
        return order
