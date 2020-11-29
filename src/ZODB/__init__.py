##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

import sys

from persistent import TimeStamp
from persistent import list
from persistent import mapping

# Backward compat for old imports.
sys.modules['ZODB.TimeStamp'] = sys.modules['persistent.TimeStamp']
sys.modules['ZODB.PersistentMapping'] = sys.modules['persistent.mapping']
sys.modules['ZODB.PersistentList'] = sys.modules['persistent.list']

del mapping, list, sys

from ZODB.DB import DB, connection

# set of changes backported by Nexedi.
nxd_patches = {
    # Rework Connection MVCC implementation to always call
    # storage.loadBefore(zconn._txn_time) to load objects.
    # storage.load() is no longer called at all.
    # https://github.com/zopefoundation/ZODB/issues/50
    # https://github.com/zopefoundation/ZODB/pull/56
    # https://github.com/zopefoundation/ZODB/pull/307
    # ...
    'conn:MVCC-via-loadBefore-only',
}
