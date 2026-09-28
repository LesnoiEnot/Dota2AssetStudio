from pathlib import Path

def test_build_script_exists():
    assert Path('build_exe.bat').exists()
