#!/usr/bin/env python3
"""
FM Diagnose: Authenticate, find IncomingPOs, and optionally insert a PO from processed JSON with verbose output.
Usage inside container:
  python3 /app/fm_diagnose.py find 4551242018 4551241534 4551241548
  python3 /app/fm_diagnose.py insert 4551242018
"""
import os, sys, json
from typing import List

sys.path.append('/app')
from filemaker_integration import FileMakerIntegration

def do_find(fm: FileMakerIntegration, po_numbers: List[str]):
    if not fm.authenticate():
        print("Auth failed")
        return 1
    for po in po_numbers:
        try:
            exists = fm.check_duplicate_po(po)
            print(f"IncomingPO {po}: {'FOUND' if exists else 'NOT FOUND'}")
        except Exception as e:
            print(f"Find error for {po}: {e}")
    fm.logout()
    return 0

def do_insert(fm: FileMakerIntegration, po: str):
    p = f"/app/processed/{po}/{po}_info.json"
    if not os.path.exists(p):
        print(f"Missing JSON: {p}")
        return 1
    with open(p,'r') as f:
        info = json.load(f)
    ok = fm.insert_po_data(info)
    print(f"Insert {po}: {ok}")
    return 0 if ok else 2

def main():
    if len(sys.argv) < 2:
        print("Usage: fm_diagnose.py [find <PO...>| insert <PO>")
        return 1
    cmd = sys.argv[1]
    fm = FileMakerIntegration()
    if cmd == 'find':
        return do_find(fm, sys.argv[2:])
    if cmd == 'insert' and len(sys.argv) >= 3:
        if not fm.authenticate():
            print("Auth failed")
            return 1
        try:
            rc = do_insert(fm, sys.argv[2])
        finally:
            fm.logout()
        return rc
    print("Invalid args")
    return 1

if __name__ == '__main__':
    raise SystemExit(main())
