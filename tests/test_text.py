from pathlib import Path
from app.text_io import read_names

def test_read_names(tmp_path):
    p=tmp_path/'x.txt'; p.write_text('Anti-Mage\nanti mage\n# comment\nAxe\n',encoding='utf-8')
    assert read_names(p)==['Anti-Mage','Axe']
