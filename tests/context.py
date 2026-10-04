# Imported by tests so lib/ and games/ are importable when run from the repo root.
import os
import sys

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _d in ('lib', 'games'):
    _p = os.path.join(_root, _d)
    if _p not in sys.path:
        sys.path.insert(0, _p)
