class TreeNode:
    """A node in a binary search tree."""

    def __init__(self, value, data=None):
        self.value = value
        self.data = data
        self.left = None
        self.right = None

    def to_dict(self):
        return {
            "value": self.value,
            "data": self.data,
            "left": self.left.to_dict() if self.left else None,
            "right": self.right.to_dict() if self.right else None,
        }


class BinarySearchTree:
    """Binary Search Tree ordered by value for efficient lookup, deletion, and traversals."""

    def __init__(self):
        self.root = None
        self._length = 0

    def insert(self, value, data=None):
        if self.root is None:
            self.root = TreeNode(value, data)
            self._length += 1
            return
        node = self.root
        while True:
            side = "left" if value < node.value else "right"
            child = getattr(node, side)
            if child is None:
                setattr(node, side, TreeNode(value, data))
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

    def search(self, value):
        """Search for a node and return its node details or None."""
        node = self.root
        while node is not None:
            if value == node.value:
                return {"value": node.value, "data": node.data}
            node = node.left if value < node.value else node.right
        return None

    def find_min(self):
        """Find the minimum value in the BST. Returns None if tree is empty."""
        if self.root is None:
            return None
        node = self.root
        while node.left is not None:
            node = node.left
        return node.value

    def find_max(self):
        """Find the maximum value in the BST. Returns None if tree is empty."""
        if self.root is None:
            return None
        node = self.root
        while node.right is not None:
            node = node.right
        return node.value

    def delete(self, value):
        """
        Delete a value from the BST.
        Handles missing values, empty tree, and 0/1/2 children.
        Returns True if deleted, False if missing.
        """
        if self.root is None:
            return False

        found = [False]

        def _delete_node(node, val):
            if node is None:
                return None
            if val < node.value:
                node.left = _delete_node(node.left, val)
            elif val > node.value:
                node.right = _delete_node(node.right, val)
            else:
                found[0] = True
                # Case 1 & 2: 0 or 1 child
                if node.left is None:
                    return node.right
                if node.right is None:
                    return node.left
                # Case 3: 2 children - get in-order successor (min in right subtree)
                successor = node.right
                while successor.left is not None:
                    successor = successor.left
                node.value = successor.value
                node.data = successor.data
                node.right = _delete_node(node.right, successor.value)
            return node

        self.root = _delete_node(self.root, value)
        if found[0]:
            self._length -= 1
        return found[0]

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

    def to_dict(self):
        return self.root.to_dict() if self.root else None

    def __len__(self):
        return self._length


class BracketNode:
    """Node in a tournament progression binary tree."""

    def __init__(self, match_name, round_name, winner=None, participant_a=None, participant_b=None):
        self.match_name = match_name
        self.round_name = round_name
        self.winner = winner
        self.participant_a = participant_a
        self.participant_b = participant_b
        self.left = None
        self.right = None

    def to_dict(self):
        return {
            "match": self.match_name,
            "round": self.round_name,
            "winner": self.winner,
            "a": self.participant_a,
            "b": self.participant_b,
            "left": self.left.to_dict() if self.left else None,
            "right": self.right.to_dict() if self.right else None,
        }


class TournamentBinaryTree:
    """Binary tree representing tournament elimination bracket progression."""

    def __init__(self, root_match=None):
        self.root = root_match

    @classmethod
    def build_sample_bracket(cls):
        """Constructs an authentic 4-team / 8-participant elimination bracket."""
        # Finals
        final = BracketNode("Championship Final", "Final", winner="Falcons A", participant_a="Falcons A", participant_b="Tigers B")
        # Semifinals
        semi1 = BracketNode("Semifinal 1", "Semifinals", winner="Falcons A", participant_a="Falcons A", participant_b="Sharks A")
        semi2 = BracketNode("Semifinal 2", "Semifinals", winner="Tigers B", participant_a="Tigers B", participant_b="Eagles C")
        # Quarterfinals
        qf1 = BracketNode("Quarterfinal 1", "Quarterfinals", winner="Falcons A", participant_a="Falcons A", participant_b="Sharks B")
        qf2 = BracketNode("Quarterfinal 2", "Quarterfinals", winner="Sharks A", participant_a="Sharks A", participant_b="Eagles A")
        qf3 = BracketNode("Quarterfinal 3", "Quarterfinals", winner="Tigers B", participant_a="Tigers B", participant_b="Falcons B")
        qf4 = BracketNode("Quarterfinal 4", "Quarterfinals", winner="Eagles C", participant_a="Eagles C", participant_b="Tigers A")

        semi1.left = qf1
        semi1.right = qf2
        semi2.left = qf3
        semi2.right = qf4
        final.left = semi1
        final.right = semi2

        return cls(final)

    def inorder(self):
        res = []

        def walk(node):
            if node:
                walk(node.left)
                res.append(node.match_name)
                walk(node.right)

        walk(self.root)
        return res

    def preorder(self):
        res = []

        def walk(node):
            if node:
                res.append(node.match_name)
                walk(node.left)
                walk(node.right)

        walk(self.root)
        return res

    def postorder(self):
        res = []

        def walk(node):
            if node:
                walk(node.left)
                walk(node.right)
                res.append(node.match_name)

        walk(self.root)
        return res

    def to_dict(self):
        return self.root.to_dict() if self.root else None
