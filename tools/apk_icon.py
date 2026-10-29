"""Extract a bounded launcher bitmap from a verified APK, without executing it."""
import hashlib
import io
import re
import warnings
import zipfile
from pathlib import PurePosixPath
from PIL import Image


def extract_icon(apk, badging):
    paths = re.findall(r"^application-icon-\d+:'([^']+)'", badging, re.M)
    paths += re.findall(r"^application:.*? icon='([^']+)'", badging, re.M)
    names = {PurePosixPath(path).stem for path in paths}
    if not names:
        return None
    candidates = []
    with zipfile.ZipFile(apk) as archive:
        for info in archive.infolist():
            path = PurePosixPath(info.filename)
            if (not info.filename.startswith('res/') or path.stem not in names
                    or path.suffix.lower() not in ('.png', '.webp', '.jpg', '.jpeg')
                    or not 0 < info.file_size <= 4_000_000):
                continue
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter('error', Image.DecompressionBombWarning)
                    with Image.open(io.BytesIO(archive.read(info))) as source:
                        width, height = source.size
                        if not (1 <= width <= 2048 and 1 <= height <= 2048):
                            continue
                        image = source.convert('RGBA')
                        image.thumbnail((256, 256), Image.Resampling.LANCZOS)
                        output = io.BytesIO()
                        image.save(output, format='PNG', optimize=True)
                        if len(output.getvalue()) <= 256_000:
                            candidates.append((width * height, output.getvalue()))
            except (OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
                continue
    return max(candidates, key=lambda item: item[0])[1] if candidates else None


def icon_path(data):
    return 'icons/' + hashlib.sha256(data).hexdigest() + '.png'
