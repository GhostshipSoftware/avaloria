#
# This sets up how models are displayed
# in the web admin interface.
#
from src.typeclasses.admin import AttributeInline, TagInline

from src.scripts.models import ScriptDB
from django.contrib import admin


class ScriptTagInline(TagInline):
    model = ScriptDB.db_tags.through


class ScriptAttributeInline(AttributeInline):
    model = ScriptDB.db_attributes.through


class ScriptDBAdmin(admin.ModelAdmin):

    list_display = ('id', 'db_key', 'db_typeclass_path',
                    'db_obj', 'db_interval', 'db_repeats', 'db_persistent')
    list_display_links = ('id', 'db_key')
    ordering = ['db_obj', 'db_typeclass_path']
    search_fields = ['^db_key', 'db_typeclass_path']
    save_as = True
    save_on_top = True
    list_select_related = True
    raw_id_fields = ('db_obj',)

    fieldsets = (
        (None, {
                'fields': (('db_key', 'db_typeclass_path'), 'db_interval',
                            'db_repeats', 'db_start_delay', 'db_persistent',
                            'db_obj')}),
        )
    inlines = [ScriptTagInline, ScriptAttributeInline]


admin.site.register(ScriptDB, ScriptDBAdmin)
