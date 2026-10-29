"""Inspect Windows ZIP metadata without extracting or executing any contents."""
import stat
import zipfile
from pathlib import PurePosixPath


def validate_windows_archive(source):
    with zipfile.ZipFile(source) as archive:
        entries=archive.infolist()
        if not entries or len(entries)>20000:
            raise ValueError('ZIP enthält zu viele oder keine Dateien.')
        total=0; executable=False
        for entry in entries:
            path=PurePosixPath(entry.filename.replace('\\','/'))
            if path.is_absolute() or '..' in path.parts or any(':' in p for p in path.parts):
                raise ValueError('ZIP enthält einen unsicheren Dateipfad.')
            if stat.S_ISLNK(entry.external_attr >> 16) or entry.flag_bits & 1:
                raise ValueError('Verknüpfte oder verschlüsselte ZIP-Dateien sind nicht unterstützt.')
            total+=entry.file_size
            if entry.file_size>512*1024*1024 or total>2*1024*1024*1024:
                raise ValueError('Entpackte ZIP ist zu groß.')
            executable |= not entry.is_dir() and path.suffix.lower() in ('.exe','.msi') and entry.file_size>0
        if not executable:
            raise ValueError('Die ZIP enthält kein Windows-Programm (.exe oder .msi).')
