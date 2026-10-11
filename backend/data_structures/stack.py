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
        if self.top is None:
            return None
        data = self.top.data
        self.top = self.top.next
        self._length -= 1
        return data

    def peek(self):
        return None if self.top is None else self.top.data

    def is_empty(self):
        return self.top is None

    def to_list(self):
        values, node = [], self.top
        while node is not None:
            values.append(node.data)
            node = node.next
        return values

    def __len__(self):
        return self._length
