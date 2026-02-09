"""Unsplash photo cache: fetch random photos, crop, dither, and cache."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image

from .dither import WIDTH, HEIGHT, dither_image

log = logging.getLogger("pi-eink-dashboard")

UNSPLASH_API = "https://api.unsplash.com/photos/random"
UNSPLASH_TOPIC = "Fzo3zuOHN6w"  # travel
CACHE_DIR = Path.home() / ".cache" / "pi-eink-dashboard" / "photos"
CONFIG_DIR = Path.home() / ".config" / "pi-eink-dashboard"
KEY_FILE = CONFIG_DIR / "unsplash.key"
MAX_CACHED = 10
FETCH_COUNT = 10  # photos per API call (dithering is now ~0.3s/photo)
_USER_AGENT = "pi-eink-dashboard/1.0"


def _load_access_key() -> str:
    """Load Unsplash access key from env var or config file."""
    key = os.environ.get("UNSPLASH_ACCESS_KEY", "").strip()
    if key:
        return key
    if KEY_FILE.exists():
        key = KEY_FILE.read_text().strip()
        if key:
            return key
    raise RuntimeError(
        f"Unsplash API key not found. Set UNSPLASH_ACCESS_KEY env var "
        f"or create {KEY_FILE}"
    )


def _http_get(url: str, headers: dict[str, str] | None = None) -> bytes:
    """Fetch URL content."""
    hdrs = {"User-Agent": _USER_AGENT}
    if headers:
        hdrs.update(headers)
    req = Request(url, headers=hdrs)
    with urlopen(req, timeout=30) as resp:
        return resp.read()


def _cover_crop(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Resize to cover target dimensions, then center-crop."""
    src_w, src_h = img.size
    target_ratio = target_w / target_h
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        new_h = target_h
        new_w = int(src_w * target_h / src_h)
    else:
        new_w = target_w
        new_h = int(src_h * target_w / src_w)

    img = img.resize((new_w, new_h), Image.LANCZOS)

    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


class PhotoCache:
    """Manage downloaded and pre-dithered Unsplash photos."""

    def __init__(self) -> None:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._meta_path = CACHE_DIR / "meta.json"
        self._meta: dict = self._load_meta()
        self._index = 0
        self._lock = threading.Lock()
        self._bg_thread: threading.Thread | None = None
        self._pending: list[dict] = []

    def _load_meta(self) -> dict:
        if self._meta_path.exists():
            try:
                return json.loads(self._meta_path.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return {"photos": []}

    def _save_meta(self) -> None:
        self._meta_path.write_text(json.dumps(self._meta, indent=2))

    @property
    def count(self) -> int:
        with self._lock:
            return len(self._meta["photos"])

    @property
    def index(self) -> int:
        return self._index

    def advance(self) -> None:
        c = self.count
        if c > 0:
            self._index = (self._index + 1) % c

    def retreat(self) -> None:
        c = self.count
        if c > 0:
            self._index = (self._index - 1) % c

    def _hash_url(self, url: str) -> str:
        return hashlib.sha256(url.encode()).hexdigest()[:16]

    def _known_ids(self) -> set[str]:
        return {p["id"] for p in self._meta["photos"]}

    def _evict_oldest(self) -> None:
        """Remove oldest entries beyond MAX_CACHED. Caller must hold _lock."""
        while len(self._meta["photos"]) > MAX_CACHED:
            old = self._meta["photos"].pop(0)
            h = old["hash"]
            for suffix in (".jpg", "_black.png", "_red.png"):
                (CACHE_DIR / f"{h}{suffix}").unlink(missing_ok=True)
            log.info("Evicted cached photo: %s", old.get("id", h))

    def _fetch_photo_list(self) -> list[dict]:
        """Fetch random landscape photos from Unsplash API."""
        access_key = _load_access_key()
        url = (
            f"{UNSPLASH_API}?count={FETCH_COUNT}"
            f"&orientation=landscape&topics={UNSPLASH_TOPIC}"
        )
        log.info("Fetching %d travel photos from Unsplash...", FETCH_COUNT)

        data = _http_get(
            url, headers={"Authorization": f"Client-ID {access_key}"}
        )
        photos = json.loads(data)

        result = []
        for photo in photos:
            photo_id = photo["id"]
            img_url = photo["urls"]["small"]
            desc = photo.get("alt_description") or photo.get("description") or ""
            result.append({"id": photo_id, "url": img_url, "desc": desc})

        log.info("Got %d photos from Unsplash.", len(result))
        return result

    def _process_one(self, photo: dict) -> bool:
        """Download, crop, dither, and cache a single photo. Return True on success."""
        h = self._hash_url(photo["url"])
        jpg_path = CACHE_DIR / f"{h}.jpg"
        black_path = CACHE_DIR / f"{h}_black.png"
        red_path = CACHE_DIR / f"{h}_red.png"

        try:
            log.info("Downloading: %s", photo["desc"][:60] or photo["id"])
            data = _http_get(photo["url"])
            jpg_path.write_bytes(data)

            img = Image.open(jpg_path).convert("RGB")
            img = _cover_crop(img, WIDTH, HEIGHT)

            black_layer, red_layer = dither_image(img)
            black_layer.save(str(black_path))
            red_layer.save(str(red_path))

            with self._lock:
                self._meta["photos"].append(
                    {"id": photo["id"], "url": photo["url"], "hash": h}
                )
                self._evict_oldest()
                self._save_meta()

            log.info("Cached photo: %s (%s)", photo["id"], h)
            return True

        except Exception:
            log.warning(
                "Failed to process photo: %s", photo["id"], exc_info=True
            )
            for p in (jpg_path, black_path, red_path):
                p.unlink(missing_ok=True)
            return False

    def refresh_first(self) -> bool:
        """Fetch photo list, process first new one, queue the rest.

        Return True if a photo was added and is ready to display.
        """
        photo_list = self._fetch_photo_list()

        with self._lock:
            known = self._known_ids()
        new_photos = [p for p in photo_list if p["id"] not in known]

        if not new_photos:
            log.info("No new photos to process.")
            self._pending = []
            return False

        first = new_photos[0]
        self._pending = new_photos[1:]

        ok = self._process_one(first)
        log.info(
            "First photo %s, %d remaining in queue.",
            "ready" if ok else "failed",
            len(self._pending),
        )
        return ok

    def start_background_refresh(self) -> None:
        """Process remaining queued photos in a background thread."""
        if not self._pending:
            return

        remaining = self._pending
        self._pending = []

        def _worker() -> None:
            for photo in remaining:
                self._process_one(photo)
            log.info("Background refresh complete, %d total cached.", self.count)

        self._bg_thread = threading.Thread(target=_worker, daemon=True)
        self._bg_thread.start()
        log.info("Background refresh started for %d photos.", len(remaining))

    def refresh(self) -> int:
        """Fetch and process all photos synchronously (for demo mode)."""
        photo_list = self._fetch_photo_list()
        known = self._known_ids()
        new_count = 0

        for photo in photo_list:
            if photo["id"] in known:
                continue
            if self._process_one(photo):
                new_count += 1

        log.info(
            "Photo cache refresh: %d new, %d total.", new_count, self.count
        )
        return new_count

    def get_dithered(
        self, index: int | None = None
    ) -> tuple[Image.Image, Image.Image] | None:
        """Load cached dithered layers for a photo. Return (black, red) or None."""
        with self._lock:
            if not self._meta["photos"]:
                return None

            idx = index if index is not None else self._index
            idx = idx % len(self._meta["photos"])
            entry = self._meta["photos"][idx]
            h = entry["hash"]

        black_path = CACHE_DIR / f"{h}_black.png"
        red_path = CACHE_DIR / f"{h}_red.png"

        if not black_path.exists() or not red_path.exists():
            log.warning("Missing cached layers for %s — removing entry.", h)
            with self._lock:
                self._meta["photos"] = [
                    p for p in self._meta["photos"] if p["hash"] != h
                ]
                self._save_meta()
            return None

        return Image.open(black_path), Image.open(red_path)
