from data_structures.node import Node


class Stack:
    """LIFO collection implemented with singly linked nodes."""

    def __init__(self):
        self.top = None
        self._length = 0

    def push(self, data):
        node = Node(data)
        node.next = self.top
        self.top = node
        self._length += 1

    def pop(self):
        """Pop top element. Returns None on stack underflow."""
        if self.top is None:
            return None
        data = self.top.data
        self.top = self.top.next
        self._length -= 1
        return data

    def peek(self):
        """Return top element without removing, or None if empty."""
        return None if self.top is None else self.top.data

    def is_empty(self):
        return self.top is None

    def to_list(self):
        values, node = [], self.top
        while node is not None:
            values.append(node.data)
            node = node.next
        return values

    def display(self):
        """Alias for to_list() to satisfy viva / syllabus requirement."""
        return self.to_list()

    def __len__(self):
        return self._length
