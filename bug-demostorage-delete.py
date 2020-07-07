#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Program bug-demostorage-delete demonstrates that DemoStorage wrongly handles
load for objects deleted in read-write overlay:

If object is deleted, even though a whiteout is recorded in the overlay,
loadBefore can incorrectly return object data of previous object revision from
read-only base, leading to data corruption.

Example output::

    base:
    @03d9186bbe8b5188  obj<0000000000000001>  ->  int(0)
    @03d9186bbe8ce3ee  obj<0000000000000001>  ->  int(1)

    base+overlay:
    @03d9186bbe8feddd  obj<0000000000000001>  ->  int(2)
    @03d9186bbe9147bb  root['obj'] = ø

    GC:
    @03d9186bbe931b00  del obj<0000000000000001>

    remount base+overlay:
    @03d9186bbe8feddd  obj<0000000000000001>  ->  int(2)    # must be int(2)
    @03d9186bbe9147bb  obj<0000000000000001>  ->  int(2)    # must be int(2)  (garbage, but still in DB)
    @03d9186bbe931b00  obj<0000000000000001>  ->  int(1)    # <- WRONG: must be POSKeyError,  not int(1) from base

The bug could be fixed if we change IStorage.loadBefore(oid) to return

    (None, serial)      # serial = revision where object was deleted

instead of just

    None

for deleted records.

Please see https://lab.nexedi.com/kirr/ZODB/commit/a762e2f8 for details.
"""

from __future__ import print_function

from ZODB.FileStorage import FileStorage
from ZODB.DemoStorage import DemoStorage
from ZODB.Connection import TransactionMetaData
from ZODB import DB
from persistent import Persistent
import transaction
import os, os.path


class PInt(Persistent):
    def __init__(self, i):
        self.i = i
    def __str__(self):
        return "int(%d)" % self.i

def h(tid):
    return tid.encode('hex')

def dump(obj):
    print("@%s  obj<%s>  ->  %s" % (h(obj._p_serial), h(obj._p_oid), obj))

def rmf(path):
    if os.path.exists(path):
        os.unlink(path)

def fs1clear(datafs):
    for suffix in ('', '.index', '.lock', '.tmp'):
        rmf(datafs + suffix)

# mkbase prepares base storage.
def mkbase():
    print("base:")
    fs1clear("base.fs")
    zbase = FileStorage("base.fs")
    db    = DB(zbase)
    conn  = db.open()
    root  = conn.root()

    root['obj'] = obj = PInt(0)
    transaction.commit()
    dump(obj)

    obj.i += 1
    transaction.commit()
    dump(obj)

    conn.close()
    db.close()
    zbase.close()

    zbase = FileStorage("base.fs", read_only=True)
    return zbase


def main():
    # prepare base + overlay
    zbase    = mkbase()
    fs1clear("overlay.fs")
    zoverlay = FileStorage("overlay.fs")
    zdemo    = DemoStorage(base=zbase, changes=zoverlay)

    print("\nbase+overlay:")
    db   = DB(zdemo)
    conn = db.open()
    root = conn.root()
    obj = root['obj']
    oid = obj._p_oid
    obj.i += 1
    # modify root as well so that there is root revision saved in overlay that points to obj
    root['x'] = 1
    transaction.commit()
    dump(obj)

    atLive = obj._p_serial

    # delete obj from root making it a garbage
    del root['obj']
    transaction.commit()
    atUnlink = root._p_serial
    print("@%s  root['obj'] = ø" % h(atUnlink))

    # unmount DemoStorage
    conn.close()
    db.close()
    zdemo.close() # closes zbase and zoverlay as well
    del zbase, zoverlay

    # simulate GC on base+overlay
    print("\nGC:")
    zoverlay = FileStorage("overlay.fs")
    txn = transaction.get()
    txn_meta = TransactionMetaData(txn.user, txn.description, txn.extension)
    zoverlay.tpc_begin(txn_meta)
    zoverlay.deleteObject(oid, atLive, txn_meta)
    zoverlay.tpc_vote(txn_meta)
    atGC = zoverlay.tpc_finish(txn_meta)
    print("@%s  del obj<%s>" % (h(atGC), h(oid)))

    # remount base+overlay
    print("\nremount base+overlay:")
    zbase = FileStorage("base.fs", read_only=True)
    zdemo = DemoStorage(base=zbase, changes=zoverlay)
    db  = DB(zdemo)

    def dumpObjAt(at, comment):
        conn = db.open(at=at)
        obj = conn.get(oid)
        print("@%s  obj<%s>  ->  %s\t# %s" % (h(at), h(oid), obj, comment))
        conn.close()

    dumpObjAt(atLive,   "must be int(2)")
    dumpObjAt(atUnlink, "must be int(2)  (garbage, but still in DB)")
    dumpObjAt(atGC,     "<- WRONG: must be POSKeyError,  not int(1) from base")


if __name__ == '__main__':
    main()
