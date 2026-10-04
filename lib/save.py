# Bankroll save file. Pure logic: no `machine`, uses only open/os so it is tested under CPython.
# Ruling DR-007: /save.json = {"v": 1, "bank": N, "chk": C}, written to /save.tmp then renamed.
# Ruling DR-008: the previous good file is kept as /save.bak; on damage fall back to it with a
# message, else start fresh with a message, and rename the damaged file to /save.bad.
# load() never raises. Save once per finished round, not per button press (BUDGET: up to ~120 ms).

import json
import os

VERSION = 1


def checksum(bank):
    """Small integrity check; catches truncation and random corruption, not tampering."""
    return (bank * 31 + 7919) % 65521


def encode(bank):
    return json.dumps({'v': VERSION, 'bank': bank, 'chk': checksum(bank)})


def decode(text):
    """Return the bankroll in `text`, or None if it is not a valid save."""
    try:
        d = json.loads(text)
        if d.get('v') != VERSION:
            return None
        bank = d['bank']
        if not isinstance(bank, int) or isinstance(bank, bool) or bank < 0:
            return None
        if d['chk'] != checksum(bank):
            return None
        return bank
    except (ValueError, KeyError, TypeError, AttributeError):
        return None


def _exists(path):
    try:
        os.stat(path)
        return True
    except OSError:
        return False


def _remove(path):
    try:
        os.remove(path)
    except OSError:
        pass


def _read(path):
    try:
        with open(path, 'r') as f:
            return decode(f.read())
    except OSError:
        return None


MSG_RESTORED = 'Save restored from backup'
MSG_FRESH = 'Save damaged. Starting fresh.'


class Store:
    def __init__(self, path='/save.json'):
        base = path[:-5] if path.endswith('.json') else path
        self.path = path
        self.tmp = base + '.tmp'
        self.bak = base + '.bak'
        self.bad = base + '.bad'

    def load(self):
        """Return (bank, message). bank is None for a fresh start; message is None when all is well."""
        main_exists = _exists(self.path)
        bank = _read(self.path) if main_exists else None
        if bank is not None:
            return bank, None
        if main_exists:
            _remove(self.bad)
            try:
                os.rename(self.path, self.bad)
            except OSError:
                _remove(self.path)
        if _exists(self.bak):
            bank = _read(self.bak)
            if bank is not None:
                return bank, MSG_RESTORED
            return None, MSG_FRESH
        if main_exists:
            return None, MSG_FRESH
        return None, None       # first run

    def save(self, bank):
        """Atomic: write tmp, keep the old file as .bak, rename tmp into place."""
        with open(self.tmp, 'w') as f:
            f.write(encode(bank))
        if _exists(self.path):
            _remove(self.bak)
            try:
                os.rename(self.path, self.bak)
            except OSError:
                pass
        os.rename(self.tmp, self.path)
