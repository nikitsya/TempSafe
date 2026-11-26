"""Seal or open a small TempSafe SQL dump using an owner-only recovery key."""

import argparse
import os
import stat
import sys
from pathlib import Path

from cryptography.fernet import Fernet


def load_cipher(key: Path) -> Fernet:
    info = key.stat()
    if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
        sys.exit("Recovery key must be accessible only to its owner")
    return Fernet(key.read_bytes())


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("action", choices=("seal", "open"))
parser.add_argument("key", type=Path)
parser.add_argument("archive", type=Path)
args = parser.parse_args()
os.umask(0o077)

if args.action == "seal":
    dump = sys.stdin.buffer.read()
    if not any(line.startswith(b"-- Dump completed on ") for line in dump.splitlines()[-2:]):
        sys.exit("Incomplete MySQL dump")
    args.key.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    args.archive.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if not args.key.exists():
        with args.key.open("xb") as key_file:
            key_file.write(Fernet.generate_key())
    encrypted = load_cipher(args.key).encrypt(dump)
    with args.archive.open("xb") as backup:
        backup.write(encrypted)
else:
    sys.stdout.buffer.write(load_cipher(args.key).decrypt(args.archive.read_bytes()))
