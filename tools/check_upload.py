"""Check the upload list before anyone uploads. Mac side, no board needed.

Reads every `| n | `repo/path` | `/board/path` |` row in UPLOAD.md and checks that the repo file
exists, compiles, and that its board path is sensible (folder matches, same base name). Also lists
board modules that are not in UPLOAD.md and runs the test suite unless --no-tests is given.

The "On the board now" table in UPLOAD.md records which version (git blob) of each file the board
holds. Against that record this checks (the step-1g lesson: slots.py called Assets.open_sprite,
which the art.py on the board did not have):
  - every project module imported by a board file is on the board;
  - every method a board file calls on the shared objects (assets, lcd, font, buttons, store,
    bankroll) is defined in the RECORDED version of that library;
  - a repo file whose content differs from its recorded version is listed as not yet uploaded.
After an upload:  python3 tools/check_upload.py --record 1h lib/art.py games/slots.py
Exit code 0 means clean. Run from the repo root:  python3 tools/check_upload.py
"""
import os
import re
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
ROW = re.compile(r'^\|\s*\d+\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`', re.M)
BOARD_FOLDERS = {'lib': '/lib', 'games': '/games', 'assets/out': '/assets', 'archive/slots': '/games'}
RECORD_ROW = re.compile(r'^\|\s*`(/[^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*(\S+)\s*\|\s*([0-9a-f]{7,40})\s*\|', re.M)
IMPORT = re.compile(r'^\s*(?:from\s+(\w+)\s+import|import\s+(\w+))', re.M)
ATTR_CALL = re.compile(r'\b(assets|lcd|font|buttons|store|bankroll)\.(\w+)\(')
# which library each shared object is, and methods that come from framebuf rather than our code
OBJECT_LIB = {'assets': 'lib/art.py', 'lcd': 'lib/lcd.py', 'font': 'lib/font.py',
              'buttons': 'lib/buttons.py', 'store': 'lib/save.py', 'bankroll': 'lib/bankroll.py'}
FRAMEBUF_METHODS = {'fill', 'fill_rect', 'rect', 'hline', 'vline', 'line', 'pixel', 'text', 'blit',
                    'ellipse', 'scroll', 'poly'}
STDLIB = {'machine', 'utime', 'time', 'framebuf', 'os', 'sys', 'gc', 'json', 'random', 'math',
          'struct', 'itertools', 're'}


def git(*args):
    return subprocess.run(['git'] + list(args), cwd=ROOT, capture_output=True, text=True)


def record(text):
    """{repo path: (board path, step, blob)} from the On-the-board table."""
    return {r: (b, step, blob) for b, r, step, blob in RECORD_ROW.findall(text)}


def blob_of(path):
    r = git('hash-object', os.path.join(ROOT, path))
    return r.stdout.strip() if r.returncode == 0 else ''


def recorded_source(blob):
    r = git('cat-file', '-p', blob)
    return r.stdout if r.returncode == 0 else None


def check_record(text):
    """Problems and warnings from the on-board record."""
    problems = []
    warnings = []
    rec = record(text)
    if not rec:
        return ['UPLOAD.md has no "On the board now" table'], warnings
    sources = {}
    for repo_path, (board_path, step, blob) in rec.items():
        src = recorded_source(blob)
        if src is None and blob_of(repo_path).startswith(blob):
            with open(os.path.join(ROOT, repo_path)) as f:     # recorded but not committed yet
                src = f.read()
        if src is None:
            problems.append('%s: recorded version %s is not in this git repo' % (repo_path, blob))
            continue
        sources[repo_path] = src
        if not blob_of(repo_path).startswith(blob):
            warnings.append('%s differs from the version on the board (recorded at step %s): add it to a step' % (repo_path, step))
    on_board_modules = {os.path.basename(p)[:-3] for p in rec if p.endswith('.py')}
    for repo_path, src in sources.items():
        for m in IMPORT.finditer(src):
            mod = m.group(1) or m.group(2)
            if mod in STDLIB or mod in on_board_modules:
                continue
            problems.append('%s (on the board) imports %r, which is not on the board' % (repo_path, mod))
        for obj, attr in set(ATTR_CALL.findall(src)):
            lib = OBJECT_LIB[obj]
            if obj == 'lcd' and attr in FRAMEBUF_METHODS:
                continue
            lib_src = sources.get(lib)
            if lib_src is None:
                problems.append('%s calls %s.%s() but %s is not on the board' % (repo_path, obj, attr, lib))
            elif not re.search(r'^\s*def %s\(' % re.escape(attr), lib_src, re.M):
                problems.append('%s calls %s.%s(), which the %s on the board (step %s) does not define'
                                % (repo_path, obj, attr, lib, rec[lib][1]))
    return problems, warnings


def update_record(text, step, paths):
    """Return UPLOAD.md text with the rows for `paths` set to the current blobs at `step`."""
    for p in paths:
        p = p.replace('\\', '/')
        blob = blob_of(p)[:12]
        if not blob:
            raise SystemExit('%s: not a file' % p)
        folder = os.path.dirname(p)
        board = (BOARD_FOLDERS.get(folder, '') + '/' + os.path.basename(p))
        row = '| `%s` | `%s` | %s | %s |' % (board, p, step, blob)
        pat = re.compile(r'^\|\s*`%s`\s*\|.*$' % re.escape(board), re.M)
        if pat.search(text):
            text = pat.sub(row, text)
        else:
            anchor = '| Board path | Repo file | Step | Version (git blob) |\n|---|---|---|---|\n'
            text = text.replace(anchor, anchor + row + '\n')
    return text


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
            with open(full) as f:
                compile(f.read(), repo_path, 'exec')
        except SyntaxError as e:
            problems.append('%s: does not compile: line %s: %s' % (repo_path, e.lineno, e.msg))
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
    if argv and argv[0] == '--record':
        if len(argv) < 3:
            print('usage: check_upload.py --record <step> <repo paths...>')
            return 2
        text = update_record(text, argv[1], argv[2:])
        with open(os.path.join(ROOT, 'UPLOAD.md'), 'w') as f:
            f.write(text)
        print('recorded %d file(s) at step %s' % (len(argv) - 2, argv[1]))
        argv = ['--no-tests']
    listed = rows(text)
    problems = []
    for repo_path, board_path in listed:
        problems += check_row(repo_path, board_path)
    listed_files = {r for r, _ in listed}
    mentioned = set(re.findall(r'`((?:lib|games)/\w+\.py|pocket\.py)`', text))   # incl. "Not on the board yet"
    for m in sorted(board_modules() - listed_files - mentioned):
        problems.append('%s is a board module but is not in UPLOAD.md' % m)
    total = 0
    for repo_path, _ in listed:
        full = os.path.join(ROOT, repo_path)
        if '*' not in repo_path and os.path.isfile(full):
            total += os.path.getsize(full)
    print('%d upload rows, %d bytes of code' % (len(listed), total))
    rec_problems, rec_warnings = check_record(text)
    problems += rec_problems
    for w in rec_warnings:
        print('  not yet on the board: ' + w)
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
