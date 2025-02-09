import libcst as cst
from typing import Dict, List, Tuple


class NodeCollector(cst.CSTVisitor):
    """Collect nodes that need docstrings."""

    def __init__(self):
        """Initialize the node collector."""
        super().__init__()
        self.nodes_needing_docstrings: Dict[str, str] = {}
        self.current_path: List[str] = []

    def get_qualified_name(self, node_name: str) -> str:
        """Get fully qualified name for the current node."""
        return node_name

    def _has_docstring(self, node: cst.CSTNode) -> bool:
        """Check if node already has a docstring."""
        if isinstance(node, (cst.FunctionDef, cst.ClassDef)):
            if node.body.body and isinstance(node.body.body[0], cst.SimpleStatementLine):
                stmt = node.body.body[0]
                if len(stmt.body) == 1 and isinstance(stmt.body[0], cst.Expr):
                    return isinstance(stmt.body[0].value, cst.SimpleString)
        return False

    def _get_node_code(self, node: cst.CSTNode) -> str:
        """Get the source code of a node."""
        return cst.Module([node]).code.strip()

    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        """Visit a class definition node."""
        if not self._has_docstring(node):
            qualified_name = self.get_qualified_name(node.name.value)
            self.nodes_needing_docstrings[qualified_name] = self._get_node_code(node)

    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        """Visit a function definition node."""
        if not self._has_docstring(node):
            qualified_name = self.get_qualified_name(node.name.value)
            self.nodes_needing_docstrings[qualified_name] = self._get_node_code(node)
