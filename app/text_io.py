from pathlib import Path

def read_names(path: Path) -> list[str]:
    text = path.read_text(encoding='utf-8-sig')
    out: list[str] = []
    seen: set[str] = set()
    for line in text.splitlines():
        name = line.strip()
        if not name or name.startswith('#'):
            continue
        key = normalize(name)
        if key not in seen:
            seen.add(key)
            out.append(name)
    return out

def normalize(value: str) -> str:
    value = value.strip().lower()
    value = value.replace('’', "'").replace('–','-').replace('—','-')
    for ch in "_-/\\()[]{}:,.!?'\"":
        value = value.replace(ch, ' ')
    return ' '.join(value.split())
