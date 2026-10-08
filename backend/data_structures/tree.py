class TreeNode:
    def __init__(self, value):
        self.value, self.left, self.right = value, None, None

class BinarySearchTree:
    def __init__(self):
        self.root = None
    def insert(self, value):
        if self.root is None:
            self.root = TreeNode(value)
            return
        node = self.root
        while True:
            side = "left" if value < node.value else "right"
            child = getattr(node, side)
            if child is None:
                setattr(node, side, TreeNode(value))
                return
            node = child
    def inorder(self):
        result = []
        def walk(node):
            if node:
                walk(node.left); result.append(node.value); walk(node.right)
        walk(self.root)
        return result
    def preorder(self):
        result = []
        def walk(node):
            if node:
                result.append(node.value); walk(node.left); walk(node.right)
        walk(self.root)
        return result
    def postorder(self):
        result = []
        def walk(node):
            if node:
                walk(node.left); walk(node.right); result.append(node.value)
        walk(self.root)
        return result
