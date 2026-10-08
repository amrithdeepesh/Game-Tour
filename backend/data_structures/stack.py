from data_structures.node import Node


class Stack:
    def __init__(self):
        self.top = None

    def push(self, data):
        new_node = Node(data)

        new_node.next = self.top
        self.top = new_node

    def pop(self):
        if self.top is None:
            print("Stack is empty.")
            return None

        removed_data = self.top.data
        self.top = self.top.next

        return removed_data

    def peek(self):
        if self.top is None:
            print("Stack is empty.")
            return None

        return self.top.data

    def is_empty(self):
        return self.top is None