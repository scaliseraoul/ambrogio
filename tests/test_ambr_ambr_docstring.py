import libcst as cst
import pytest

from ambrogio.ambr_docstring.ambr_docstring import DocstringTransformer


@pytest.fixture
def transformer():
    docstring_map = {"MyClass": '"""This is MyClass."""'}
    return DocstringTransformer(docstring_map)


def test_leave_ClassDef_adds_docstring(transformer):
    original_node = cst.ClassDef(
        name=cst.Name(value="MyClass"), body=cst.IndentedBlock(body=[])
    )
    updated_node = cst.ClassDef(
        name=cst.Name(value="MyClass"), body=cst.IndentedBlock(body=[])
    )
    modified_node = transformer.leave_ClassDef(original_node, updated_node)
    assert isinstance(modified_node, cst.ClassDef)
    assert modified_node.body.body[0].body[0].value.value == '"""This is MyClass."""'
