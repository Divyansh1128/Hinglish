"""Read untrusted ZIP archives into memory without extracting or executing anything.

Every member name is checked for absolute paths, drive letters, backslashes and
``..`` traversal; symlinks, encrypted members, duplicates and oversized content
are rejected. Results ZIPs must carry a ``checksums.sha256`` that lists every
other member, and every listed SHA-256 must match.
"""

import hashlib
import io
import re
import stat
import zipfile

CHECKSUMS = "checksums.sha256"
MAX_MEMBERS = 5000
MAX_MEMBER_BYTES = 256 * 1024 * 1024
MAX_TOTAL_BYTES = 1024 * 1024 * 1024
_LINE = re.compile(r"([0-9a-f]{64})  (.+)")


class UnsafeArchive(ValueError):
    """The archive is malformed, unsafe or fails integrity verification."""


def _require(condition, message):
    if not condition:
        raise UnsafeArchive(message)


def check_name(name):
    """Reject absolute, drive-qualified, backslashed or traversing member names."""
    _require(isinstance(name, str) and name, "Empty archive member name")
    _require("\x00" not in name and "\\" not in name, f"Unsafe archive member name: {name!r}")
    _require(not name.startswith("/") and not re.match(r"[A-Za-z]:", name),
             f"Absolute archive member path rejected: {name!r}")
    parts = name[:-1].split("/") if name.endswith("/") else name.split("/")
    _require(all(part not in ("", ".", "..") for part in parts),
             f"Path traversal or empty component rejected: {name!r}")
    _require(not any(ord(ch) < 32 for ch in name), f"Control character in member name: {name!r}")
    return name


def read_zip(source, label="archive"):
    """Return {member_name: bytes} for regular-file members of a ZIP path or bytes."""
    stream = io.BytesIO(source) if isinstance(source, (bytes, bytearray)) else source
    try:
        archive = zipfile.ZipFile(stream)
    except (zipfile.BadZipFile, OSError) as error:
        raise UnsafeArchive(f"{label}: not a readable ZIP ({type(error).__name__})") from None
    members, folded, total = {}, set(), 0
    with archive:
        infos = archive.infolist()
        _require(len(infos) <= MAX_MEMBERS, f"{label}: too many members")
        for info in infos:
            name = check_name(info.filename)
            _require(not info.flag_bits & 0x1, f"{label}: encrypted member {name!r}")
            mode = info.external_attr >> 16
            _require(not stat.S_ISLNK(mode), f"{label}: symlink member {name!r}")
            if info.is_dir():
                continue
            _require(name not in members, f"{label}: duplicate member {name!r}")
            _require(name.casefold() not in folded, f"{label}: case-colliding member {name!r}")
            folded.add(name.casefold())
            _require(info.file_size <= MAX_MEMBER_BYTES, f"{label}: member too large {name!r}")
            try:
                with archive.open(info) as handle:
                    data = handle.read(MAX_MEMBER_BYTES + 1)
            except (zipfile.BadZipFile, OSError, NotImplementedError, RuntimeError) as error:
                raise UnsafeArchive(f"{label}: cannot read {name!r} ({type(error).__name__})") from None
            _require(len(data) <= MAX_MEMBER_BYTES, f"{label}: member too large {name!r}")
            total += len(data)
            _require(total <= MAX_TOTAL_BYTES, f"{label}: uncompressed content too large")
            members[name] = data
    return members


def verify_checksums(members, label="archive"):
    """Verify every checksums.sha256 entry; every other member must be listed.

    Returns {name: sha256} for the verified members.
    """
    _require(CHECKSUMS in members, f"{label}: missing {CHECKSUMS}")
    try:
        text = members[CHECKSUMS].decode("utf-8")
    except UnicodeDecodeError:
        raise UnsafeArchive(f"{label}: {CHECKSUMS} is not UTF-8") from None
    listed = {}
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        match = _LINE.fullmatch(line)
        _require(match is not None, f"{label}: malformed {CHECKSUMS} line {number}")
        expected, name = match.groups()
        check_name(name)
        _require(name != CHECKSUMS and name not in listed, f"{label}: duplicate or self entry {name!r}")
        listed[name] = expected
    _require(listed, f"{label}: {CHECKSUMS} is empty")
    for name, expected in listed.items():
        _require(name in members, f"{label}: listed file missing from archive: {name!r}")
        actual = hashlib.sha256(members[name]).hexdigest()
        _require(actual == expected, f"{label}: checksum mismatch for {name!r}")
    unlisted = sorted(set(members) - set(listed) - {CHECKSUMS})
    _require(not unlisted, f"{label}: members not covered by {CHECKSUMS}: {unlisted}")
    return listed
