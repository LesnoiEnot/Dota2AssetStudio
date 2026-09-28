from pathlib import Path
from .http_client import HttpClient
from .image_processing import decode_image, process_image, save_png
from .liquipedia_api import LiquipediaCatalog
from .models import ResultStats
from .text_io import read_names

class DownloadEngine:
    def __init__(self, base_dir: Path, logger, progress, status):
        self.base_dir = base_dir
        self.logger = logger
        self.progress = progress
        self.status = status
        self.http = HttpClient('Dota2AssetStudio/2.0 (Windows asset downloader; see README for contact)')
        self.catalog = LiquipediaCatalog(base_dir / 'cache', logger)
        self.catalog.load_cache()
        self.stats = ResultStats()

    def refresh(self):
        self.catalog.refresh_all()

    def download(self, asset_type: str, list_file: Path, size_mode: str, custom_px: int, force_refresh: bool = True):
        names = read_names(list_file)
        self.stats = ResultStats(total=len(names))
        out_dir = self.base_dir / 'output' / asset_type
        out_dir.mkdir(parents=True, exist_ok=True)
        manual = []
        for i, requested in enumerate(names, 1):
            self.status(f'{asset_type}: {requested}')
            dest = out_dir / f'{requested}.png'
            if dest.exists() and not force_refresh:
                self.stats.skipped += 1
                self.logger(f'[{i}/{len(names)}] SKIP {requested}')
                self.progress(i, len(names), self.stats)
                continue
            rec = self.catalog.find(asset_type, requested)
            if not rec:
                manual.append(requested)
                self.stats.manual += 1
                self.logger(f'[{i}/{len(names)}] MANUAL {requested}: не найден в Liquipedia catalog')
                self.progress(i, len(names), self.stats)
                continue
            try:
                data = self.http.get_bytes(rec.url).data
                img = decode_image(data)
                processed = process_image(img, 'Contain', size_mode, custom_px)
                save_png(processed, dest)
                self.stats.downloaded += 1
                self.logger(f'[{i}/{len(names)}] OK {requested} <- {rec.source} ({processed.width}x{processed.height})')
            except Exception as exc:
                self.stats.failed += 1
                manual.append(requested)
                self.logger(f'[{i}/{len(names)}] FAILED {requested}: {exc}')
            self.progress(i, len(names), self.stats)
        manual_path = self.base_dir / f'manual_check_{asset_type}.txt'
        manual_path.write_text('\n'.join(manual) + ('\n' if manual else ''), encoding='utf-8')
        return self.stats
