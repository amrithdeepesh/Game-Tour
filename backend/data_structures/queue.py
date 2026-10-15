from data_structures.node import Node


class Queue:
    """FIFO collection implemented with singly linked nodes."""

    def __init__(self):
        self.front = None
        self.rear = None
        self._length = 0

    def enqueue(self, data):
        node = Node(data)
        if self.rear is None:
            self.front = self.rear = node
        else:
            self.rear.next = node
            self.rear = node
        self._length += 1

    def dequeue(self):
        """Dequeue front element. Returns None on empty queue."""
        if self.front is None:
            return None
        data = self.front.data
        self.front = self.front.next
        if self.front is None:
            self.rear = None
        self._length -= 1
        return data

    def peek(self):
        """Return front element without removing, or None if empty."""
        return None if self.front is None else self.front.data

    def get_front(self):
        """Alias for peek / front element."""
        return self.peek()

    def is_empty(self):
        return self.front is None

    def to_list(self):
        values, node = [], self.front
        while node is not None:
            values.append(node.data)
            node = node.next
        return values

    def display(self):
        """Alias for to_list() to satisfy viva / syllabus requirement."""
        return self.to_list()

    def __len__(self):
        return self._length
