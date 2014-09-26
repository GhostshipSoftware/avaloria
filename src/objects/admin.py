#
# This sets up how models are displayed
# in the web admin interface.
#

from django import forms
from django.conf import settings
from django.contrib import admin
from src.typeclasses.admin import AttributeInline, TagInline
from src.objects.models import ObjectDB


class ObjectAttributeInline(AttributeInline):
    model = ObjectDB.db_attributes.through


class ObjectTagInline(TagInline):
    model = ObjectDB.db_tags.through


class ObjectCreateForm(forms.ModelForm):
    "This form details the look of the fields"
    class Meta:
        model = ObjectDB
        fields = '__all__'
    db_key = forms.CharField(label="Name/Key",
                             widget=forms.TextInput(attrs={'size': '78'}),
                             help_text="Main identifier, like 'apple', 'strong guy', 'Elizabeth' etc. If creating a Character, check so the name is unique among characters!",)
    db_typeclass_path = forms.CharField(label="Typeclass",
                                        initial=settings.BASE_OBJECT_TYPECLASS,
                                        widget=forms.TextInput(attrs={'size': '78'}),
                                        help_text="This defines what 'type' of entity this is. This variable holds a Python path to a module with a valid Evennia Typeclass. If you are creating a Character you should use the typeclass defined by settings.BASE_CHARACTER_TYPECLASS or one derived from that.")
    db_cmdset_storage = forms.CharField(label="CmdSet",
                                        initial="",
                                        required=False,
                                        widget=forms.TextInput(attrs={'size': '78'}),
                                        help_text="Most non-character objects don't need a cmdset and can leave this field blank.")
    raw_id_fields = ('db_destination', 'db_location', 'db_home')


class ObjectEditForm(ObjectCreateForm):
    "Form used for editing. Extends the create one with more fields"

    class Meta:
        fields = '__all__'
    db_lock_storage = forms.CharField(label="Locks",
                                      required=False,
                                      widget=forms.Textarea(attrs={'cols':'100', 'rows':'2'}),
                                      help_text="In-game lock definition string. If not given, defaults will be used. This string should be on the form <i>type:lockfunction(args);type2:lockfunction2(args);...")


class ObjectDBAdmin(admin.ModelAdmin):

    inlines = [ObjectTagInline, ObjectAttributeInline]
    list_display = ('id', 'db_key', 'db_player', 'db_typeclass_path')
    list_display_links = ('id', 'db_key')
    ordering = ['db_player', 'db_typeclass_path', 'id']
    search_fields = ['^db_key', 'db_typeclass_path']
    raw_id_fields = ('db_destination', 'db_location', 'db_home')

    save_as = True
    save_on_top = True
    list_select_related = True
    list_filter = ('db_typeclass_path',)
    #list_filter = ('db_permissions', 'db_typeclass_path')

    # editing fields setup

    form = ObjectEditForm
    fieldsets = (
        (None, {
                'fields': (('db_key','db_typeclass_path'), ('db_lock_storage', ),
                           ('db_location', 'db_home'), 'db_destination','db_cmdset_storage'
                           )}),
        )
    #fieldsets = (
    #    (None, {
    #            'fields': (('db_key','db_typeclass_path'), ('db_permissions', 'db_lock_storage'),
    #                       ('db_location', 'db_home'), 'db_destination','db_cmdset_storage'
    #                       )}),
    #    )

    #deactivated temporarily, they cause empty objects to be created in admin

    # Custom modification to give two different forms wether adding or not.
    add_form = ObjectCreateForm
    add_fieldsets = (
        (None, {
                'fields': (('db_key','db_typeclass_path'),
                           ('db_location', 'db_home'), 'db_destination', 'db_cmdset_storage'
                           )}),
        )

    #add_fieldsets = (
    #    (None, {
    #            'fields': (('db_key','db_typeclass_path'), 'db_permissions',
    #                       ('db_location', 'db_home'), 'db_destination', 'db_cmdset_storage'
    #                       )}),
    #    )
    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return super(ObjectDBAdmin, self).get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        """
        Use special form during creation
        """
        defaults = {}
        if obj is None:
            defaults.update({
                    'form': self.add_form,
                    'fields': admin.util.flatten_fieldsets(self.add_fieldsets),
                    })
            defaults.update(kwargs)
        return super(ObjectDBAdmin, self).get_form(request, obj, **defaults)

    def save_model(self, request, obj, form, change):
        obj.save()
        if not change:
            # adding a new object
            obj = obj.typeclass
            obj.basetype_setup()
            obj.basetype_posthook_setup()
            obj.at_object_creation()
        obj.at_init()


admin.site.register(ObjectDB, ObjectDBAdmin)
