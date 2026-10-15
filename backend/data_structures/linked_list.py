from data_structures.node import Node


class LinkedList:
    """Singly linked list for tournament participants and enrollment records."""

    def __init__(self):
        self.head = None
        self.tail = None
        self.length = 0

    def insert_at_end(self, data):
        node = Node(data)
        if self.tail is None:
            self.head = self.tail = node
        else:
            self.tail.next = node
            self.tail = node
        self.length += 1

    def insert_at_start(self, data):
        node = Node(data)
        node.next = self.head
        self.head = node
        if self.tail is None:
            self.tail = node
        self.length += 1

    def insert_at_position(self, position, data):
        """Insert at 0-indexed position (0 to length). Raises IndexError on invalid position."""
        if position < 0 or position > self.length:
            raise IndexError(f"Position {position} is out of bounds for list of length {self.length}.")
        if position == 0:
            self.insert_at_start(data)
            return
        if position == self.length:
            self.insert_at_end(data)
            return
        current = self.head
        for _ in range(position - 1):
            current = current.next
        node = Node(data)
        node.next = current.next
        current.next = node
        self.length += 1

    def traverse(self):
        current, values = self.head, []
        while current is not None:
            values.append(current.data)
            current = current.next
        return values

    def to_list(self):
        return self.traverse()

    def search(self, query, field=None):
        """Search by value or dictionary field; returns (index, data) or (-1, None)."""
        current = self.head
        index = 0
        target = str(query).casefold()
        while current:
            val = current.data.get(field) if (field and isinstance(current.data, dict)) else current.data
            if str(val).casefold() == target:
                return index, current.data
            current = current.next
            index += 1
        return -1, None

    def delete_by_student_id(self, student_id):
        previous, current = None, self.head
        while current:
            if isinstance(current.data, dict) and current.data.get("student_id") == student_id:
                if previous is None:
                    self.head = current.next
                else:
                    previous.next = current.next
                if self.tail is current:
                    self.tail = previous
                self.length -= 1
                return current.data
            previous, current = current, current.next
        return None

    def delete_by_value(self, value, field=None):
        """Delete first occurrence matching value or field value. Returns deleted data or None."""
        previous, current = None, self.head
        target = str(value).casefold()
        while current:
            val = current.data.get(field) if (field and isinstance(current.data, dict)) else current.data
            if str(val).casefold() == target:
                if previous is None:
                    self.head = current.next
                else:
                    previous.next = current.next
                if self.tail is current:
                    self.tail = previous
                self.length -= 1
                return current.data
            previous, current = current, current.next
        return None

    def delete_at_position(self, position):
        """Delete node at 0-indexed position. Raises IndexError on invalid position."""
        if self.is_empty() or position < 0 or position >= self.length:
            raise IndexError(f"Position {position} is out of bounds for list of length {self.length}.")
        if position == 0:
            deleted = self.head.data
            self.head = self.head.next
            if self.head is None:
                self.tail = None
            self.length -= 1
            return deleted
        current = self.head
        for _ in range(position - 1):
            current = current.next
        deleted = current.next.data
        if current.next is self.tail:
            self.tail = current
        current.next = current.next.next
        self.length -= 1
        return deleted

    def is_empty(self):
        return self.head is None

    def __len__(self):
        return self.length
