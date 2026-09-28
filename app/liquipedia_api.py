import json
import time
from pathlib import Path
from urllib.parse import urlencode
from .http_client import HttpClient
from .text_io import normalize
from .models import AssetRecord

API = 'https://liquipedia.net/commons/api.php'
# Liquipedia asks automated clients to identify themselves and provide contact information.
USER_AGENT = 'Dota2AssetStudio/2.0 (Windows desktop asset downloader; contact: project maintainer via GitHub repository)'

CATEGORIES = {
    'heroes': ['Category:Dota 2 hero icons'],
    'neutral_creeps': ['Category:Dota 2 unit icons'],
    # Include the dedicated neutral-item category too, so "items" covers both normal
    # and neutral item icons without depending on subcategory expansion behavior.
    'items': ['Category:Dota 2 item icons', 'Category:Dota 2 neutral item icons'],
}

class LiquipediaCatalog:
    def __init__(self, cache_dir: Path, logger):
        self.cache_dir = cache_dir
        self.logger = logger
        self.http = HttpClient(USER_AGENT)
        self.maps: dict[str, dict[str, AssetRecord]] = {}

    def refresh_all(self):
        for asset_type in CATEGORIES:
            self.refresh(asset_type)

    def refresh(self, asset_type: str):
        all_records: dict[str, AssetRecord] = {}
        for category in CATEGORIES[asset_type]:
            self.logger(f'Liquipedia API: {category}…')
            records = self._fetch_category(category)
            for rec in records:
                all_records.setdefault(normalize(rec.source_name), rec)
            # The API policy is at most one request every 2 seconds; _fetch_category
            # spaces continuation requests internally, and this pauses between categories.
            time.sleep(2.05)
        records = list(all_records.values())
        self.maps[asset_type] = {normalize(r.source_name): r for r in records}
        cache = self.cache_dir / f'{asset_type}.json'
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps([r.__dict__ for r in records], ensure_ascii=False, indent=2), encoding='utf-8')
        self.logger(f'Liquipedia API: {asset_type}: {len(records)} файлов в кэше')

    def _fetch_category(self, category: str) -> list[AssetRecord]:
        params = {
            'action': 'query', 'format': 'json',
            'generator': 'categorymembers',
            'gcmtitle': category,
            'gcmnamespace': '6',
            'gcmlimit': 'max',
            'prop': 'imageinfo',
            'iiprop': 'url',
        }
        records: list[AssetRecord] = []
        while True:
            url = API + '?' + urlencode(params)
            data = self._api_json(url)
            records.extend(self._parse(data))
            cont = data.get('continue')
            if not cont:
                break
            time.sleep(2.05)
            params = params | cont
        return records

    def load_cache(self):
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        for asset_type in CATEGORIES:
            p = self.cache_dir / f'{asset_type}.json'
            if not p.exists():
                continue
            try:
                rows = json.loads(p.read_text(encoding='utf-8'))
                self.maps[asset_type] = {normalize(r['source_name']): AssetRecord(**r) for r in rows}
                self.logger(f'Кэш: {asset_type}: {len(rows)} файлов')
            except Exception as exc:
                self.logger(f'Кэш {asset_type} повреждён: {exc}')

    def find(self, asset_type: str, requested: str) -> AssetRecord | None:
        mp = self.maps.get(asset_type, {})
        key = normalize(requested)
        rec = mp.get(key)
        if rec:
            return AssetRecord(requested, rec.source_name, rec.url, rec.source)
        # Controlled alias matching, only when unique.
        candidates = []
        for k, value in mp.items():
            if k == key.replace(' the ', ' '):
                candidates.append(value)
            elif k.startswith(key + ' ') or key.startswith(k + ' '):
                candidates.append(value)
        return AssetRecord(requested, candidates[0].source_name, candidates[0].url, candidates[0].source) if len(candidates) == 1 else None

    def _api_json(self, url: str):
        resp = self.http.get_bytes(url)
        return json.loads(resp.data.decode('utf-8'))

    def _parse(self, data: dict) -> list[AssetRecord]:
        rows = []
        for page in data.get('query', {}).get('pages', {}).values():
            title = page.get('title', '')
            if not title.startswith('File:'):
                continue
            info = (page.get('imageinfo') or [{}])[0]
            url = info.get('url')
            if not url:
                continue
            filename = title[5:]
            source_name = filename
            suffixes = [
                ' icon dota2 gameasset.png',
                ' itemicon dota2 gameasset.png',
            ]
            for suffix in suffixes:
                if source_name.lower().endswith(suffix.lower()):
                    source_name = source_name[:-len(suffix)]
                    break
            rows.append(AssetRecord('', source_name, url, 'Liquipedia Commons'))
        return rows
