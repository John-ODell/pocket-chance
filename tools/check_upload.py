"""Check the upload list before anyone uploads. Mac side, no board needed.

Reads every `| n | `repo/path` | `/board/path` |` row in UPLOAD.md and checks that the repo file
exists, compiles, and that its board path is sensible (folder matches, same base name). Also lists
board modules that are not in UPLOAD.md and runs the test suite unless --no-tests is given.
Exit code 0 means clean. Run from the repo root:  python3 tools/check_upload.py
"""
import os
import py_compile
import re
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
ROW = re.compile(r'^\|\s*\d+\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`', re.M)
BOARD_FOLDERS = {'lib': '/lib', 'games': '/games', 'assets/out': '/assets'}


def rows(text):
    return ROW.findall(text)


def check_row(repo_path, board_path):
    """Return a list of problems for one upload row (empty = fine)."""
    problems = []
    if '*' in repo_path:
        return problems                         # assets/out/*.565: a pattern, checked separately
    full = os.path.join(ROOT, repo_path)
    if not os.path.isfile(full):
        return ['%s: file does not exist' % repo_path]
    if repo_path.endswith('.py'):
        try:
            py_compile.compile(full, cfile=os.devnull, doraise=True)
        except py_compile.PyCompileError as e:
            problems.append('%s: does not compile: %s' % (repo_path, e.msg.strip().splitlines()[-1]))
    board_path = board_path.split(' ')[0]
    if os.path.basename(board_path) != os.path.basename(repo_path):
        problems.append('%s -> %s: base name differs' % (repo_path, board_path))
    folder = os.path.dirname(repo_path)
    want = BOARD_FOLDERS.get(folder, '')
    if os.path.dirname(board_path).rstrip('/') != want:
        problems.append('%s -> %s: expected it under %s' % (repo_path, board_path, want or '/'))
    return problems


def board_modules():
    mods = set()
    for d in ('lib', 'games'):
        for n in os.listdir(os.path.join(ROOT, d)):
            if n.endswith('.py'):
                mods.add(d + '/' + n)
    mods.add('pocket.py')
    return mods


def main(argv):
    with open(os.path.join(ROOT, 'UPLOAD.md')) as f:
        text = f.read()
    listed = rows(text)
    problems = []
    for repo_path, board_path in listed:
        problems += check_row(repo_path, board_path)
    listed_files = {r for r, _ in listed}
    for m in sorted(board_modules() - listed_files):
        problems.append('%s is a board module but is not in UPLOAD.md' % m)
    total = 0
    for repo_path, _ in listed:
        if '*' not in repo_path:
            total += os.path.getsize(os.path.join(ROOT, repo_path))
    print('%d upload rows, %d bytes of code' % (len(listed), total))
    for p in problems:
        print('  PROBLEM: ' + p)
    if '--no-tests' not in argv:
        r = subprocess.run([sys.executable, '-m', 'unittest'], cwd=ROOT, capture_output=True, text=True)
        tail = (r.stderr.strip().splitlines() or [''])[-1]
        print('  tests: ' + tail)
        if r.returncode != 0:
            problems.append('tests fail')
    print('CLEAN' if not problems else '%d PROBLEM(S)' % len(problems))
    return 0 if not problems else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
