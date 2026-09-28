from dataclasses import dataclass
from typing import Literal

AssetType = Literal['heroes', 'neutral_creeps', 'items']

@dataclass(frozen=True)
class AssetRecord:
    requested_name: str
    source_name: str
    url: str
    source: str

@dataclass
class ResultStats:
    total: int = 0
    downloaded: int = 0
    skipped: int = 0
    manual: int = 0
    failed: int = 0
