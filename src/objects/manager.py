"""
Custom manager for Objects.
"""
from itertools import chain
from django.db.models import Q
from django.conf import settings
from django.db.models.fields import exceptions
from src.typeclasses.managers import TypedObjectManager
from src.typeclasses.managers import returns_typeclass, returns_typeclass_list
from src.utils import utils
from src.utils.utils import to_unicode, is_iter, make_iter, string_partial_matching

__all__ = ("ObjectManager",)
_GA = object.__getattribute__

# delayed import
_ATTR = None


# Try to use a custom way to parse id-tagged multimatches.

_AT_MULTIMATCH_INPUT = utils.variable_from_module(*settings.SEARCH_AT_MULTIMATCH_INPUT.rsplit('.', 1))


class ObjectManager(TypedObjectManager):
    """
    This ObjectManager implementes methods for searching
    and manipulating Objects directly from the database.

    Evennia-specific search methods (will return Typeclasses or
    lists of Typeclasses, whereas Django-general methods will return
    Querysets or database objects).

    dbref (converter)
    get_id (alias: dbref_search)
    get_dbref_range
    object_totals
    typeclass_search
    get_object_with_player
    get_objs_with_key_and_typeclass
    get_objs_with_attr
    get_objs_with_attr_match
    get_objs_with_db_property
    get_objs_with_db_property_match
    get_objs_with_key_or_alias
    get_contents
    object_search (interface to many of the above methods,
                   equivalent to ev.search_object)
    copy_object

    """

    #
    # ObjectManager Get methods
    #

    # player related

    @returns_typeclass
    def get_object_with_player(self, ostring, exact=True, candidates=None):
        """
        Search for an object based on its player's name or dbref.
        This search
        is sometimes initiated by appending a * to the beginning of
        the search criterion (e.g. in local_and_global_search).
        search_string:  (string) The name or dbref to search for.
        """
        ostring = to_unicode(ostring).lstrip('*')
        # simplest case - search by dbref
        dbref = self.dbref(ostring)
        if dbref:
            return dbref
        # not a dbref. Search by name.
        cand_restriction = candidates != None and Q(pk__in=[_GA(obj, "id") for obj in make_iter(candidates) if obj]) or Q()
        if exact:
            return self.filter(cand_restriction & Q(db_player__username__iexact=ostring))
        else: # fuzzy matching
            ply_cands = self.filter(cand_restriction & Q(playerdb__username__istartswith=ostring)).values_list("db_key", flat=True)
            if candidates:
                index_matches = string_partial_matching(ply_cands, ostring, ret_index=True)
                return [obj for ind, obj in enumerate(make_iter(candidates)) if ind in index_matches]
            else:
                return string_partial_matching(ply_cands, ostring, ret_index=False)

    @returns_typeclass_list
    def get_objs_with_key_and_typeclass(self, oname, otypeclass_path, candidates=None):
        """
        Returns objects based on simultaneous key and typeclass match.
        """
        cand_restriction = candidates != None and Q(pk__in=[_GA(obj, "id") for obj in make_iter(candidates) if obj]) or Q()
        return self.filter(cand_restriction & Q(db_key__iexact=oname, db_typeclass_path__exact=otypeclass_path))

    # attr/property related

    @returns_typeclass_list
    def get_objs_with_attr(self, attribute_name, candidates=None):
        """
        Returns all objects having the given attribute_name defined at all.
        Location should be a valid location object.
        """
        cand_restriction = candidates != None and Q(db_attributes__db_obj__pk__in=[_GA(obj, "id") for obj in make_iter(candidates) if obj]) or Q()
        return list(self.filter(cand_restriction & Q(db_attributes__db_key=attribute_name)))

    @returns_typeclass_list
    def get_objs_with_attr_value(self, attribute_name, attribute_value, candidates=None, typeclasses=None):
        """
        Returns all objects having the valid attrname set to the given value.

        candidates - list of candidate objects to search
        typeclasses - list of typeclass-path strings to restrict matches with

        This uses the Attribute's PickledField to transparently search the database by matching
        the internal representation. This is reasonably effective but since Attribute values
        cannot be indexed, searching by Attribute key is to be preferred whenever possible.
        """
        cand_restriction = candidates != None and Q(pk__in=[_GA(obj, "id") for obj in make_iter(candidates) if obj]) or Q()
        type_restriction = typeclasses and Q(db_typeclass_path__in=make_iter(typeclasses)) or Q()

        ## This doesn't work if attribute_value is an object. Workaround below

        if isinstance(attribute_value, (basestring, int, float, bool, long)):
            return self.filter(cand_restriction & type_restriction & Q(db_attributes__db_key=attribute_name, db_attributes__db_value=attribute_value))
        else:
            # We have to loop for safety since the referenced lookup gives deepcopy error if attribute value is an object.
            global _ATTR
            if not _ATTR:
                from src.typeclasses.models import Attribute as _ATTR
            cands = list(self.filter(cand_restriction & type_restriction & Q(db_attributes__db_key=attribute_name)))
            results = [attr.objectdb_set.all() for attr in _ATTR.objects.filter(objectdb__in=cands, db_value=attribute_value)]
            return chain(*results)

    @returns_typeclass_list
    def get_objs_with_db_property(self, property_name, candidates=None):
        """
        Returns all objects having a given db field property.
        property_name = search string
        candidates - list of candidate objects to search
        """
        property_name = "db_%s" % property_name.lstrip('db_')
        cand_restriction = candidates != None and Q(pk__in=[_GA(obj, "id") for obj in make_iter(candidates) if obj]) or Q()
        querykwargs = {property_name:None}
        try:
            return list(self.filter(cand_restriction).exclude(Q(**querykwargs)))
        except exceptions.FieldError:
            return []

    @returns_typeclass_list
    def get_objs_with_db_property_value(self, property_name, property_value, candidates=None, typeclasses=None):
        """
        Returns all objects having a given db field property.
        candidates - list of objects to search
        typeclasses - list of typeclass-path strings to restrict matches with
        """
        if isinstance(property_value, basestring):
            property_value = to_unicode(property_value)
        if isinstance(property_name, basestring):
            if not property_name.startswith('db_'):
                property_name = "db_%s" % property_name
        if hasattr(property_value, 'dbobj'):
            property_value = property_value.dbobj
        querykwargs = {property_name:property_value}
        cand_restriction = candidates != None and Q(pk__in=[_GA(obj, "id") for obj in make_iter(candidates) if obj]) or Q()
        type_restriction = typeclasses and Q(db_typeclass_path__in=make_iter(typeclasses)) or Q()
        try:
            return list(self.filter(cand_restriction & type_restriction & Q(**querykwargs)))
        except exceptions.FieldError:
            return []
        except ValueError:
            from src.utils import logger
            logger.log_errmsg("The property '%s' does not support search criteria of the type %s." % (property_name, type(property_value)))
            return []

    @returns_typeclass_list
    def get_contents(self, location, excludeobj=None):
        """
        Get all objects that has a location
        set to this one.

        excludeobj - one or more object keys to exclude from the match
        """
        exclude_restriction = Q(pk__in=[_GA(obj, "id") for obj in make_iter(excludeobj)]) if excludeobj else Q()
        return self.filter(db_location=location).exclude(exclude_restriction)

    @returns_typeclass_list
    def get_objs_with_key_or_alias(self, ostring, exact=True,
                                         candidates=None, typeclasses=None):
        """
        Returns objects based on key or alias match. Will also do fuzzy
        matching based on the utils.string_partial_matching function.
        candidates - list of candidate objects to restrict on
        typeclasses - list of typeclass path strings to restrict on
        """
        if not isinstance(ostring, basestring):
            if hasattr(ostring, "key"):
                ostring = ostring.key
            else:
                return []
        if is_iter(candidates) and not len(candidates):
            # if candidates is an empty iterable there can be no matches
            # Exit early.
            return []

        # build query objects
        candidates_id = [_GA(obj, "id") for obj in make_iter(candidates) if obj]
        cand_restriction = candidates != None and Q(pk__in=make_iter(candidates_id)) or Q()
        type_restriction = typeclasses and Q(db_typeclass_path__in=make_iter(typeclasses)) or Q()
        if exact:
            # exact match - do direct search
            return self.filter(cand_restriction & type_restriction & (Q(db_key__iexact=ostring) |
                               Q(db_tags__db_key__iexact=ostring) & Q(db_tags__db_tagtype__iexact="alias"))).distinct()
        elif candidates:
            # fuzzy with candidates
            key_candidates = self.filter(cand_restriction & type_restriction)
        else:
            # fuzzy without supplied candidates - we select our own candidates
            key_candidates = self.filter(type_restriction & (Q(db_key__istartswith=ostring) | Q(db_tags__db_key__istartswith=ostring))).distinct()
            candidates_id = [_GA(obj, "id") for obj in key_candidates]
        # fuzzy matching
        key_strings = key_candidates.values_list("db_key", flat=True).order_by("id")

        index_matches = string_partial_matching(key_strings, ostring, ret_index=True)
        if index_matches:
            return [obj for ind, obj in enumerate(key_candidates) if ind in index_matches]
        else:
            alias_candidates = self.filter(id__in=candidates_id, db_tags__db_tagtype__iexact="alias")
            alias_strings = alias_candidates.values_list("db_key", flat=True)
            index_matches = string_partial_matching(alias_strings, ostring, ret_index=True)
            if index_matches:
                return [alias.db_obj for ind, alias in enumerate(alias_candidates) if ind in index_matches]
            return []

    # main search methods and helper functions

    @returns_typeclass_list
    def object_search(self, searchdata,
                      attribute_name=None,
                      typeclass=None,
                      candidates=None,
                      exact=True):
        """
        Search as an object globally or in a list of candidates and return
        results. The result is always an Object. Always returns a list.

        Arguments:
        searchdata: (str or obj) The entity to match for. This is usually a
                  key string but may also be an object itself. By default (if
                  not attribute_name is set), this will search object.key and
                  object.aliases in order. Can also be on the form #dbref,
                  which will, if exact=True be matched against primary key.
        attribute_name: (str): Use this named ObjectAttribute to match
                  searchdata against, instead of the defaults. If this is
                  the name of a database field (with or without the db_ prefix),
                  that will be matched too.
        typeclass (str or TypeClass): restrict matches to objects having this
                  typeclass. This will help speed up global searches.
        candidates (list obj ObjectDBs): If supplied, search will only be
                  performed among the candidates in this list. A common list
                  of candidates is the contents of the current location
                  searched.
        exact (bool): Match names/aliases exactly or partially. Partial
                  matching matches the beginning of words in the names/aliases,
                  using a matching routine to separate multiple matches in
                  names with multiple components (so "bi sw" will match
                  "Big sword"). Since this is more expensive than exact
                  matching, it is recommended to be used together with the
                  objlist keyword to limit the number of possibilities. This
                  value has no meaning if searching for attributes/properties.

        Returns:
        A list of matching objects (or a list with one unique match)
        """
        def _searcher(searchdata, candidates, typeclass, exact=False):
            """
            Helper method for searching objects. typeclass is only used
            for global searching (no candidates)
            """
            if attribute_name:
                # attribute/property search (always exact).
                matches = self.get_objs_with_db_property_value(attribute_name, searchdata, candidates=candidates, typeclasses=typeclass)
                if matches:
                    return matches
                return self.get_objs_with_attr_value(attribute_name, searchdata, candidates=candidates, typeclasses=typeclass)
            else:
                # normal key/alias search
                return self.get_objs_with_key_or_alias(searchdata, exact=exact, candidates=candidates, typeclasses=typeclass)

        if not searchdata and searchdata != 0:
            return []

        if typeclass:
            # typeclass may also be a list
            typeclasses = make_iter(typeclass)
            for i, typeclass in enumerate(make_iter(typeclasses)):
                if callable(typeclass):
                    typeclasses[i] = u"%s.%s" % (typeclass.__module__, typeclass.__name__)
                else:
                    typeclasses[i] = u"%s" % typeclass
            typeclass = typeclasses

        if candidates:
            # Convenience check to make sure candidates are really dbobjs
            candidates = [cand.dbobj for cand in make_iter(candidates) if cand]
            if typeclass:
                candidates = [cand for cand in candidates
                                if _GA(cand, "db_typeclass_path") in typeclass]

        dbref = not attribute_name and exact and self.dbref(searchdata)
        if dbref is not None:
            # Easiest case - dbref matching (always exact)
            dbref_match = self.dbref_search(dbref)
            if dbref_match:
                if not candidates or dbref_match.dbobj in candidates:
                    return [dbref_match]
                else:
                    return []

        # Search through all possibilities.
        match_number = None
        # always run first check exact - we don't want partial matches
        # if on the form of 1-keyword etc.
        matches = _searcher(searchdata, candidates, typeclass, exact=True)
        if not matches:
            # no matches found - check if we are dealing with N-keyword
            # query - if so, strip it.
            match_number, searchdata = _AT_MULTIMATCH_INPUT(searchdata)
            # run search again, with the exactness set by call
            if match_number is not None or not exact:
                matches = _searcher(searchdata, candidates, typeclass, exact=exact)

        # deal with result
        if len(matches) > 1 and match_number is not None:
            # multiple matches, but a number was given to separate them
            try:
                matches = [matches[match_number]]
            except IndexError:
                pass
        # return a list (possibly empty)
        return matches

    #
    # ObjectManager Copy method
    #

    def copy_object(self, original_object, new_key=None,
                    new_location=None, new_home=None,
                    new_permissions=None, new_locks=None,
                    new_aliases=None, new_destination=None):
        """
        Create and return a new object as a copy of the original object. All
        will be identical to the original except for the arguments given
        specifically to this method.

        original_object (obj) - the object to make a copy from
        new_key (str) - name the copy differently from the original.
        new_location (obj) - if not None, change the location
        new_home (obj) - if not None, change the Home
        new_aliases (list of strings) - if not None, change object aliases.
        new_destination (obj) - if not None, change destination
        """

        # get all the object's stats
        typeclass_path = original_object.typeclass_path
        if not new_key:
            new_key = original_object.key
        if not new_location:
            new_location = original_object.location
        if not new_home:
            new_home = original_object.home
        if not new_aliases:
            new_aliases = original_object.aliases.all()
        if not new_locks:
            new_locks = original_object.db_lock_storage
        if not new_permissions:
            new_permissions = original_object.permissions.all()
        if not new_destination:
            new_destination = original_object.destination

        # create new object
        from src.utils import create
        from src.scripts.models import ScriptDB
        new_object = create.create_object(typeclass_path,
                                          key=new_key,
                                          location=new_location,
                                          home=new_home,
                                          permissions=new_permissions,
                                          locks=new_locks,
                                          aliases=new_aliases,
                                          destination=new_destination)
        if not new_object:
            return None

        # copy over all attributes from old to new.
        for attr in original_object.attributes.all():
            new_object.attributes.add(attr.key, attr.value)

        # copy over all cmdsets, if any
        for icmdset, cmdset in enumerate(original_object.cmdset.all()):
            if icmdset == 0:
                new_object.cmdset.add_default(cmdset)
            else:
                new_object.cmdset.add(cmdset)

        # copy over all scripts, if any
        for script in original_object.scripts.all():
            ScriptDB.objects.copy_script(script, new_obj=new_object.dbobj)

        return new_object

    def clear_all_sessids(self):
        """
        Clear the db_sessid field of all objects having also the db_player field
        set.
        """
        self.filter(db_sessid__isnull=False).update(db_sessid=None)

