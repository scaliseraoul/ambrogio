import pytest
from unittest import mock
import libcst as cst
from ambrogio.ambr_docstring.node_collector import NodeNeedingDocstring


@pytest.fixture
def node_collector():
    return NodeNeedingDocstring()


def test_visit_class_def(node_collector, mocker):
    mock_class_def = mock.Mock(spec=cst.ClassDef)
    mock_class_def.name.value = "TestClass"
    mock_class_def.body.body = [mock.Mock(spec=cst.SimpleStatementLine)]
    mock_class_def.body.body[0].body = [mock.Mock(spec=cst.Expr)]
    mock_class_def.body.body[0].body[0].value = mock.Mock(spec=cst.SimpleString)

    node_collector.visit_ClassDef(mock_class_def)
    assert "TestClass" not in node_collector.nodes_needing_docstrings

    mock_class_def.body.body[0].body[0].value = None
    node_collector.visit_ClassDef(mock_class_def)
    assert "TestClass" in node_collector.nodes_needing_docstrings
