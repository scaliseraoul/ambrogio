import libcst as cst
import pytest

from ambrogio.ambr_docstring.ambr_docstring import DocstringTransformer


@pytest.fixture
def transformer():
    """Fixture that provides a DocstringTransformer instance with predefined docstring mappings.

    This fixture initializes a DocstringTransformer with a mapping for the class 'MyClass',
    allowing for easy transformation of docstrings during testing.

    Returns:
        DocstringTransformer: An instance of DocstringTransformer configured with
        a docstring mapping for 'MyClass'."""
    docstring_map = {"MyClass": '"""This is MyClass."""'}
    return DocstringTransformer(docstring_map)


def test_leave_ClassDef_adds_docstring(transformer):
    """Test the leave_ClassDef method of the transformer.

    This test verifies that the transformer correctly adds a docstring
    to a ClassDef node when the leave_ClassDef method is called. It
    checks that the returned node is still a ClassDef and that the
    first body element contains the expected docstring.

    Args:
        transformer: An instance of the transformer being tested.

    Returns:
        None"""
    original_node = cst.ClassDef(
        name=cst.Name(value="MyClass"), body=cst.IndentedBlock(body=[])
    )
    updated_node = cst.ClassDef(
        name=cst.Name(value="MyClass"), body=cst.IndentedBlock(body=[])
    )
    modified_node = transformer.leave_ClassDef(original_node, updated_node)
    assert isinstance(modified_node, cst.ClassDef)
    assert modified_node.body.body[0].body[0].value.value == '"""This is MyClass."""'
