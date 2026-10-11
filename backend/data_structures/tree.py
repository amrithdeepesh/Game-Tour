class TreeNode:
    """A node in a binary search tree."""

    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None


class BinarySearchTree:
    """Binary tree ordered by value for efficient lookup and traversals."""

    def __init__(self):
        self.root = None
        self._length = 0

    def insert(self, value):
        if self.root is None:
            self.root = TreeNode(value)
            self._length += 1
            return
        node = self.root
        while True:
            side = "left" if value < node.value else "right"
            child = getattr(node, side)
            if child is None:
                setattr(node, side, TreeNode(value))
                self._length += 1
                return
            node = child

    def contains(self, value):
        node = self.root
        while node is not None:
            if value == node.value:
                return True
            node = node.left if value < node.value else node.right
        return False

    def inorder(self):
        result = []
        def walk(node):
            if node is not None:
                walk(node.left)
                result.append(node.value)
                walk(node.right)
        walk(self.root)
        return result

    def preorder(self):
        result = []
        def walk(node):
            if node is not None:
                result.append(node.value)
                walk(node.left)
                walk(node.right)
        walk(self.root)
        return result

    def postorder(self):
        result = []
        def walk(node):
            if node is not None:
                walk(node.left)
                walk(node.right)
                result.append(node.value)
        walk(self.root)
        return result

    def __len__(self):
        return self._length
