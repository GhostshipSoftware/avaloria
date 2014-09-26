"""
This module handles serialization of arbitrary python structural data,
intended primarily to be stored in the database. It also supports
storing Django model instances (which plain pickle cannot do).

This serialization is used internally by the server, notably for
storing data in Attributes and for piping data to process pools.

The purpose of dbserialize is to handle all forms of data. For
well-structured non-arbitrary exchange, such as communicating with a
rich web client, a simpler JSON serialization makes more sense.

This module also implements the SaverList, SaverDict and SaverSet
classes. These are iterables that track their position in a nested
structure and makes sure to send updates up to their root. This is
used by Attributes - without it, one would not be able to update mutables
in-situ, e.g obj.db.mynestedlist[3][5] = 3 would never be saved and
be out of sync with the database.

"""

from functools import update_wrapper
from collections import defaultdict, MutableSequence, MutableSet, MutableMapping
try:
    from cPickle import dumps, loads
except ImportError:
    from pickle import dumps, loads
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
from src.server.models import ServerConfig
from src.utils.utils import to_str, uses_database
from src.utils import logger

__all__ = ("to_pickle", "from_pickle", "do_pickle", "do_unpickle")

PICKLE_PROTOCOL = 2

# initialization and helpers

_GA = object.__getattribute__
_SA = object.__setattr__
_FROM_MODEL_MAP = None
_TO_MODEL_MAP = None
_TO_TYPECLASS = lambda o: hasattr(o, 'typeclass') and o.typeclass or o
_IS_PACKED_DBOBJ = lambda o: type(o) == tuple and len(o) == 4 and o[0] == '__packed_dbobj__'
if uses_database("mysql") and ServerConfig.objects.get_mysql_db_version() < '5.6.4':
    # mysql <5.6.4 don't support millisecond precision
    _DATESTRING = "%Y:%m:%d-%H:%M:%S:000000"
else:
    _DATESTRING = "%Y:%m:%d-%H:%M:%S:%f"


def _TO_DATESTRING(obj):
    """
    this will only be called with valid database objects. Returns datestring
    on correct form.
    """
    try:
        return _GA(obj, "db_date_created").strftime(_DATESTRING)
    except AttributeError:
        # this can happen if object is not yet saved - no datestring is then set
        obj.save()
        return _GA(obj, "db_date_created").strftime(_DATESTRING)


def _init_globals():
    "Lazy importing to avoid circular import issues"
    global _FROM_MODEL_MAP, _TO_MODEL_MAP
    if not _FROM_MODEL_MAP:
        _FROM_MODEL_MAP = defaultdict(str)
        _FROM_MODEL_MAP.update(dict((c.model, c.natural_key()) for c in ContentType.objects.all()))
    if not _TO_MODEL_MAP:
        _TO_MODEL_MAP = defaultdict(str)
        _TO_MODEL_MAP.update(dict((c.natural_key(), c.model_class()) for c in ContentType.objects.all()))

#
# SaverList, SaverDict, SaverSet - Attribute-specific helper classes and functions
#


def _save(method):
    "method decorator that saves data to Attribute"
    def save_wrapper(self, *args, **kwargs):
        self.__doc__ = method.__doc__
        ret = method(self, *args, **kwargs)
        self._save_tree()
        return ret
    return update_wrapper(save_wrapper, method)


class _SaverMutable(object):
    """
    Parent class for properly handling  of nested mutables in
    an Attribute. If not used something like
     obj.db.mylist[1][2] = "test" (allocation to a nested list)
    will not save the updated value to the database.
    """
    def __init__(self, *args, **kwargs):
        "store all properties for tracking the tree"
        self._parent = kwargs.pop("parent", None)
        self._db_obj = kwargs.pop("db_obj", None)
        self._data = None

    def _save_tree(self):
        "recursively traverse back up the tree, save when we reach the root"
        if self._parent:
            self._parent._save_tree()
        elif self._db_obj:
            self._db_obj.value = self
        else:
            logger.log_errmsg("_SaverMutable %s has no root Attribute to save to." % self)

    def _convert_mutables(self, data):
        "converts mutables to Saver* variants and assigns .parent property"
        def process_tree(item, parent):
            "recursively populate the tree, storing parents"
            dtype = type(item)
            if dtype in (basestring, int, long, float, bool, tuple):
                return item
            elif dtype == list:
                dat = _SaverList(parent=parent)
                dat._data.extend(process_tree(val, dat) for val in item)
                return dat
            elif dtype == dict:
                dat = _SaverDict(parent=parent)
                dat._data.update((key, process_tree(val, dat)) for key, val in item.items())
                return dat
            elif dtype == set:
                dat = _SaverSet(parent=parent)
                dat._data.update(process_tree(val, dat) for val in item)
                return dat
            return item
        return process_tree(data, self)

    def __repr__(self):
        return self._data.__repr__()

    def __len__(self):
        return self._data.__len__()

    def __iter__(self):
        return self._data.__iter__()

    def __getitem__(self, key):
        return self._data.__getitem__(key)

    @_save
    def __setitem__(self, key, value):
        self._data.__setitem__(key, self._convert_mutables(value))

    @_save
    def __delitem__(self, key):
        self._data.__delitem__(key)


class _SaverList(_SaverMutable, MutableSequence):
    """
    A list that saves itself to an Attribute when updated.
    """
    def __init__(self, *args, **kwargs):
        super(_SaverList, self).__init__(*args, **kwargs)
        self._data = list(*args)

    @_save
    def __add__(self, otherlist):
        self._data = self._data.__add__(otherlist)
        return self._data

    @_save
    def insert(self, index, value):
        self._data.insert(index, self._convert_mutables(value))


class _SaverDict(_SaverMutable, MutableMapping):
    """
    A dict that stores changes to an Attribute when updated
    """
    def __init__(self, *args, **kwargs):
        super(_SaverDict, self).__init__(*args, **kwargs)
        self._data = dict(*args)

    def has_key(self, key):
        return key in self._data


class _SaverSet(_SaverMutable, MutableSet):
    """
    A set that saves to an Attribute when updated
    """
    def __init__(self, *args, **kwargs):
        super(_SaverSet, self).__init__(*args, **kwargs)
        self._data = set(*args)

    def __contains__(self, value):
        return self._data.__contains__(value)

    @_save
    def add(self, value):
        self._data.add(self._convert_mutables(value))

    @_save
    def discard(self, value):
        self._data.discard(value)

#
# serialization helpers
#

def pack_dbobj(item):
    """
    Check and convert django database objects to an internal representation.
    This either returns the original input item or a tuple
      ("__packed_dbobj__", key, creation_time, id)
    """
    _init_globals()
    obj = hasattr(item, 'dbobj') and item.dbobj or item
    natural_key = _FROM_MODEL_MAP[hasattr(obj, "id") and hasattr(obj, "db_date_created") and
                                  hasattr(obj, '__class__') and obj.__class__.__name__.lower()]
    # build the internal representation as a tuple
    #  ("__packed_dbobj__", key, creation_time, id)
    return natural_key and ('__packed_dbobj__', natural_key,
                             _TO_DATESTRING(obj), _GA(obj, "id")) or item


def unpack_dbobj(item):
    """
    Check and convert internal representations back to Django database models.
    The fact that item is a packed dbobj should be checked before this call.
    This either returns the original input or converts the internal store back
    to a database representation (its typeclass is returned if applicable).
    """
    _init_globals()
    try:
        obj = item[3] and _TO_TYPECLASS(_TO_MODEL_MAP[item[1]].objects.get(id=item[3]))
    except ObjectDoesNotExist:
        return None
    # even if we got back a match, check the sanity of the date (some
    # databases may 're-use' the id)
    try:
        dbobj = obj.dbobj
    except AttributeError:
        dbobj = obj
    return _TO_DATESTRING(dbobj) == item[2] and obj or None

#
# Access methods
#

def to_pickle(data):
    """
    This prepares data on arbitrary form to be pickled. It handles any nested
    structure and returns data on a form that is safe to pickle (including
    having converted any database models to their internal representation).
    We also convert any Saver*-type objects back to their normal
    representations, they are not pickle-safe.
    """
    def process_item(item):
        "Recursive processor and identification of data"
        dtype = type(item)
        if dtype in (basestring, int, long, float, bool):
            return item
        elif dtype == tuple:
            return tuple(process_item(val) for val in item)
        elif dtype in (list, _SaverList):
            return [process_item(val) for val in item]
        elif dtype in (dict, _SaverDict):
            return dict((process_item(key), process_item(val)) for key, val in item.items())
        elif dtype in (set, _SaverSet):
            return set(process_item(val) for val in item)
        elif hasattr(item, '__item__'):
            # we try to conserve the iterable class, if not convert to list
            try:
                return item.__class__([process_item(val) for val in item])
            except (AttributeError, TypeError):
                return [process_item(val) for val in item]
        return pack_dbobj(item)
    return process_item(data)


#@transaction.autocommit
def from_pickle(data, db_obj=None):
    """
    This should be fed a just de-pickled data object. It will be converted back
    to a form that may contain database objects again. Note that if a database
    object was removed (or changed in-place) in the database, None will be
    returned.

    db_obj - this is the model instance (normally an Attribute) that
             _Saver*-type iterables (_SaverList etc) will save to when they
             update. It must have a 'value' property that saves assigned data
             to the database. Skip if not serializing onto a given object.

    If db_obj is given, this function will convert lists, dicts and sets
    to their _SaverList, _SaverDict and _SaverSet counterparts.

    """
    def process_item(item):
        "Recursive processor and identification of data"
        dtype = type(item)
        if dtype in (basestring, int, long, float, bool):
            return item
        elif _IS_PACKED_DBOBJ(item):
            # this must be checked before tuple
            return unpack_dbobj(item)
        elif dtype == tuple:
            return tuple(process_item(val) for val in item)
        elif dtype == dict:
            return dict((process_item(key), process_item(val)) for key, val in item.items())
        elif dtype == set:
            return set(process_item(val) for val in item)
        elif hasattr(item, '__iter__'):
            try:
                # we try to conserve the iterable class if
                # it accepts an iterator
                return item.__class__(process_item(val) for val in item)
            except (AttributeError, TypeError):
                return [process_item(val) for val in item]
        return item

    def process_tree(item, parent):
        "Recursive processor, building a parent-tree from iterable data"
        dtype = type(item)
        if dtype in (basestring, int, long, float, bool):
            return item
        elif _IS_PACKED_DBOBJ(item):
            # this must be checked before tuple
            return unpack_dbobj(item)
        elif dtype == tuple:
            return tuple(process_tree(val, item) for val in item)
        elif dtype == list:
            dat = _SaverList(parent=parent)
            dat._data.extend(process_tree(val, dat) for val in item)
            return dat
        elif dtype == dict:
            dat = _SaverDict(parent=parent)
            dat._data.update(dict((process_item(key), process_tree(val, dat))
                                   for key, val in item.items()))
            return dat
        elif dtype == set:
            dat = _SaverSet(parent=parent)
            dat._data.update(set(process_tree(val, dat) for val in item))
            return dat
        elif hasattr(item, '__iter__'):
            try:
                # we try to conserve the iterable class if it
                # accepts an iterator
                return item.__class__(process_tree(val, parent) for val in item)
            except (AttributeError, TypeError):
                dat = _SaverList(parent=parent)
                dat._data.extend(process_tree(val, dat) for val in item)
                return dat
        return item

    if db_obj:
        # convert lists, dicts and sets to their Saved* counterparts. It
        # is only relevant if the "root" is an iterable of the right type.
        dtype = type(data)
        if dtype == list:
            dat = _SaverList(db_obj=db_obj)
            dat._data.extend(process_tree(val, parent=dat) for val in data)
            return dat
        elif dtype == dict:
            dat = _SaverDict(db_obj=db_obj)
            dat._data.update((process_item(key), process_tree(val, parent=dat))
                              for key, val in data.items())
            return dat
        elif dtype == set:
            dat = _SaverSet(db_obj=db_obj)
            dat._data.update(process_tree(val, parent=dat) for val in data)
            return dat
    return process_item(data)


def do_pickle(data):
    "Perform pickle to string"
    return to_str(dumps(data, protocol=PICKLE_PROTOCOL))


def do_unpickle(data):
    "Retrieve pickle from pickled string"
    return loads(to_str(data))


def dbserialize(data):
    "Serialize to pickled form in one step"
    return do_pickle(to_pickle(data))


def dbunserialize(data, db_obj=None):
    "Un-serialize in one step. See from_pickle for help db_obj."
    return do_unpickle(from_pickle(data, db_obj=db_obj))
