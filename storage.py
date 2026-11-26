"""Local files for catalog, market history and execution reconciliation."""

import json
import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path


def data_root():
    base = os.environ.get("EMA_TRADER_DATA_DIR")
    if base:
        return Path(base)
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA", Path.home())) / "EMATrader"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "EMATrader"
    return Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")) / "ema-trader"


def read(path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False, mode="w", encoding="utf-8") as file:
        temporary = Path(file.name)
        try:
            json.dump(value, file, ensure_ascii=False)
            file.flush()
            os.fsync(file.fileno())
        except BaseException:
            file.close()
            temporary.unlink(missing_ok=True)
            raise
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def account_lock(path):
    with path.open("a+b") as lock:
        lock.seek(0)
        if sys.platform == "win32":
            import msvcrt
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            if sys.platform == "win32":
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock, fcntl.LOCK_UN)
