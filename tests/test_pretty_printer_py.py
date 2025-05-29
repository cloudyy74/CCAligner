import shutil
from pathlib import Path
import pytest

from lexical_analysis.pretty_printing import PrettyPrinterPy

def setup_dirs(tmp_path, code: str, filename: str = "sample.py"):
    src = tmp_path / "code"
    dst = tmp_path / "pretty"
    src.mkdir()
    dst.mkdir()
    file = src / filename
    file.write_text(code, encoding="utf-8")
    return src, dst, file.name

@pytest.mark.parametrize("source_code, expected_output", [
    (
        """
# it is comment
def foo(x, y):
    z = x + y  # inline comment
    return z

# also comment
        """,
        """
defVAR(VAR,VAR):
    VAR=VAR+VAR
    returnVAR
        """.strip()
    ),
    (
        """
# it is comment
0; 0; print(42); 0; 0

# more comments
        """,
        """
VAR(integer)
        """.strip()
    ),
    (
        '''
# это комментарий
def main(): ## smth
    """main"""
    x = 0
    x += 1; x = 2; print(x); 0

# ещё коммент
        ''',
        """
defVAR():
    VAR=integer
    VAR+=integer
    VAR=integer
    VAR(VAR)
        """.strip()
    ),
(    """
x = 0; 0
for i in range(42):
    for _ in range(13):
        if x == 1:
            print(15)
        elif x == 3:
            x = 2
        else:
            x = 4; print(15)
    """,
    """
VAR=integer
forVARinVAR(integer):
    forVARinVAR(integer):
        ifVAR==integer:
            VAR(integer)
        elifVAR==integer:
            VAR=integer
        else:
            VAR=integer
            VAR(integer)
""".strip()
)
])
def test_process_single_file(tmp_path, source_code, expected_output):
    src, dst, filename = setup_dirs(tmp_path, source_code)
    printer = PrettyPrinterPy(str(src), str(dst), language="python")
    assert printer.run()

    out_file = printer.dst_root / filename
    assert out_file.exists()
    got = out_file.read_text(encoding="utf-8").strip()
    assert got == expected_output

def test_idempotence(tmp_path):
    source_code = '''
## comment
def foo(a, b):
    """foooooooooo""" 
    return a +b ## commeeeent
    '''
    src, dst, filename = setup_dirs(tmp_path, source_code)
    printer = PrettyPrinterPy(str(src), str(dst), language="python")
    printer.run()
    first = (printer.dst_root / filename).read_text("utf-8")

    shutil.rmtree(dst)
    dst.mkdir()
    printer = PrettyPrinterPy(str(src), str(dst), language="python")
    printer.run()
    second = (printer.dst_root / filename).read_text("utf-8")

    assert first == second

def test_empty_file(tmp_path):
    src, dst, filename = setup_dirs(tmp_path, "", filename="empty.py")
    printer = PrettyPrinterPy(str(src), str(dst), language="python")
    assert printer.run()

    out = (printer.dst_root / filename).read_text("utf-8")
    assert out == ""
