import shutil
from pathlib import Path
import pytest

from lexical_analysis.pretty_printing import PrettyPrinterPy

SIMPLE_CODE = """
# это комментарий
def foo(x, y):
    z = x + y  # inline comment
    return z

# ещё коммент
"""

EXPECTED_OUTPUT = """
defVAR(VAR,VAR):
    VAR=VAR+VAR
    returnVAR
""".strip()

@pytest.fixture
def setup_dirs(tmp_path):
    src = tmp_path / "code"
    dst = tmp_path / "pretty"
    src.mkdir()
    dst.mkdir()
    file = src / "sample.py"
    file.write_text(SIMPLE_CODE, encoding="utf-8")
    return src, dst

def test_process_single_file(setup_dirs):
    src, dst = setup_dirs
    printer = PrettyPrinterPy(str(src), str(dst), language="python")
    assert printer.run()

    out_file = printer.dst_root / "sample.py"
    assert out_file.exists()
    got = out_file.read_text(encoding="utf-8").strip()
    assert got == EXPECTED_OUTPUT

def test_idempotence(setup_dirs):
    src, dst = setup_dirs
    printer = PrettyPrinterPy(str(src), str(dst), language="python")
    printer.run()
    first = (printer.dst_root / "sample.py").read_text("utf-8")

    shutil.rmtree(dst)
    dst.mkdir()
    printer = PrettyPrinterPy(str(src), str(dst), language="python")
    printer.run()
    second = (printer.dst_root / "sample.py").read_text("utf-8")

    assert first == second

def test_empty_file(tmp_path):
    src = tmp_path / "code"
    dst = tmp_path / "pretty"
    src.mkdir() 
    dst.mkdir()
    (src / "empty.py").write_text("", encoding="utf-8")

    printer = PrettyPrinterPy(str(src), str(dst), language="python")
    assert printer.run()

    out = (printer.dst_root / "empty.py").read_text("utf-8")
    assert out == ""
