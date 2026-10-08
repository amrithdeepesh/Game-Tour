from data_structures.node import Node

class LinkedList:
    """Singly linked list for tournament participants."""
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

    def traverse(self):
        current, values = self.head, []
        while current is not None:
            values.append(current.data)
            current = current.next
        return values

    def delete_by_student_id(self, student_id):
        previous, current = None, self.head
        while current:
            if current.data.get("student_id") == student_id:
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
