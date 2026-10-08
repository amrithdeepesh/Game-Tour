from data_structures.node import Node


class Queue:
    def __init__(self):
        self.front = None
        self.rear = None

    def enqueue(self, data):
        new_node = Node(data)

        if self.rear is None:
            self.front = new_node
            self.rear = new_node
            return

        self.rear.next = new_node
        self.rear = new_node

    def dequeue(self):
        if self.front is None:
            print("Queue is empty.")
            return None

        removed_data = self.front.data
        self.front = self.front.next

        if self.front is None:
            self.rear = None

        return removed_data

    def peek(self):
        if self.front is None:
            print("Queue is empty.")
            return None

        return self.front.data