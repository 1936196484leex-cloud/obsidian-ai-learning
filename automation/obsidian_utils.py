"""Conservative Markdown handling and backup-first note writes."""
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path

HEADINGS = ["🎯 Today's Top 3", '🔁 Review', '💻 Deep Work', '📚 What I Learned',
            '🧪 What I Practiced', '❓ Problems & Questions', '📖 Reading',
            '🌙 Daily Review', "➡️ Tomorrow's First Step"]


def canonical(value):
    return re.sub(r'^[^A-Za-z]+', '', value).strip().casefold()


def sections(text):
    """Recognize headings outside fenced code; stop at any H1/H2."""
    result = []
    offset = 0
    fence = None
    for line in text.splitlines(keepends=True):
        match = re.match(r'^\s{0,3}(`{3,}|~{3,})', line)
        if match:
            token = match[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
        elif fence is None:
            match = re.match(r'^(#{1,2})\s+(.+?)\s*#*\s*$', line)
            if match:
                result.append((canonical(match[2]) if len(match[1]) == 2 else None,
                               offset, offset + len(line)))
        offset += len(line)
    return [(key, start, body, result[i+1][1] if i+1 < len(result) else len(text))
            for i, (key, start, body) in enumerate(result)]


def empty(body):
    return all(not line.strip() or re.fullmatch(r'\s*[-*] \[ \]\s*', line)
               for line in body.splitlines())


def fill_sections(text, content):
    """Fill blank sections only. Nonempty or duplicated headings are untouched."""
    for heading, value in content.items():
        matches = [s for s in sections(text) if s[0] == canonical(heading)]
        if not matches:
            text = text.rstrip() + '\n\n## ' + heading + '\n' + value.strip() + '\n'
        elif len(matches) == 1:
            _, _, start, end = matches[0]
            if empty(text[start:end]):
                prefix = text[:start]
                if not prefix.endswith('\n'):
                    prefix += '\n'
                text = prefix + value.strip() + '\n\n' + text[end:]
    return text


def template(day):
    return '# ' + day + '\n\n' + '\n\n'.join(
        '## ' + h + ('\n- [ ]\n- [ ]\n- [ ]' if i == 0 else '')
        for i, h in enumerate(HEADINGS)) + '\n'


def read_note(path, vault, files):
    if path.is_symlink() or not path.resolve().is_relative_to(vault):
        raise ValueError('Refusing note symlink or path outside vault')
    if path.stat().st_size > 200_000:
        raise ValueError('Note exceeds 200 KB safety limit')
    data = path.read_bytes().decode('utf-8')
    files.append(str(path.relative_to(vault)))
    return data


def unfinished(text):
    return re.findall(r'^\s*[-*] \[ \] (\S[^\n]*)', text, re.M)[:30]


def active_context(vault, files):
    summaries = []
    # Only inspect these folders, at most 40 note files per folder, no recursion.
    for folder in ('03 Projects', '04 Courses', '06 Career'):
        candidates = sorted((vault / folder).glob('*.md'))[:40]
        active = []
        for path in candidates:
            body = read_note(path, vault, files)
            if re.search(r'^\s*Status:\s*[\"\x27]?Active[\"\x27]?\s*$', body, re.M | re.I):
                high = bool(re.search(r'^\s*Priority:\s*High\s*$', body, re.M | re.I))
                fragments = [body[a:b].strip()[:500] for key, _, a, b in sections(body)
                             if key in ('current goal', 'next actions', 'blockers')]
                active.append((not high, path.name, '\n'.join(fragments)[:1200]))
        for _, name, body in sorted(active)[:3]:
            summaries.append(f'{folder}/{name}\n{body}')
    return summaries


def save_note(path, old, new, backup_dir):
    """Caller serializes runs. Recheck after backup; preserve exact source bytes."""
    if old is None:
        # Exclusive creation cannot overwrite a note created during the API request.
        with path.open('x', encoding='utf-8', newline='') as handle:
            handle.write(new)
        return
    if path.is_symlink() or path.read_bytes().decode('utf-8') != old:
        raise RuntimeError('Note changed during generation; rerun after sync settles')
    backup_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    backup = backup_dir / (path.stem + '-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.md')
    with backup.open('x', encoding='utf-8', newline='') as handle:
        handle.write(old)
    os.chmod(backup, 0o600)
    fd, temp = tempfile.mkstemp(prefix='.ai-note-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as handle:
            handle.write(new)
            handle.flush()
            os.fsync(handle.fileno())
        if path.is_symlink() or path.read_bytes().decode('utf-8') != old:
            raise RuntimeError('Note changed before save; backup kept, write cancelled')
        os.replace(temp, path)
    finally:
        Path(temp).unlink(missing_ok=True)
