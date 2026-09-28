import time
from dataclasses import dataclass
from typing import Optional
import requests

@dataclass
class Downloaded:
    data: bytes
    content_type: str
    url: str

class HttpClient:
    def __init__(self, user_agent: str, timeout: float = 25):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept-Encoding': 'gzip, deflate',
            'Accept': '*/*',
        })
        self.timeout = timeout

    def get_bytes(self, url: str, retries: int = 3) -> Downloaded:
        last = None
        for attempt in range(retries):
            try:
                r = self.session.get(url, timeout=self.timeout, allow_redirects=True)
                if r.status_code == 200 and r.content:
                    return Downloaded(r.content, r.headers.get('Content-Type',''), r.url)
                last = RuntimeError(f'HTTP {r.status_code}')
                if r.status_code in (429, 500, 502, 503, 504):
                    time.sleep(2 ** attempt)
                else:
                    break
            except requests.RequestException as exc:
                last = exc
                time.sleep(2 ** attempt)
        raise RuntimeError(str(last) if last else 'request failed')
