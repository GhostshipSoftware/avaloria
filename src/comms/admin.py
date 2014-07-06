#
# This sets up how models are displayed
# in the web admin interface.
#

from django.contrib import admin
from src.comms.models import ChannelDB
from src.typeclasses.admin import AttributeInline, TagInline


class ChannelAttributeInline(AttributeInline):
    model = ChannelDB.db_attributes.through


class ChannelTagInline(TagInline):
    model = ChannelDB.db_tags.through


class MsgAdmin(admin.ModelAdmin):
    list_display = ('id', 'db_date_sent', 'db_sender', 'db_receivers',
                    'db_channels', 'db_message', 'db_lock_storage')
    list_display_links = ("id",)
    ordering = ["db_date_sent", 'db_sender', 'db_receivers', 'db_channels']
    #readonly_fields = ['db_message', 'db_sender', 'db_receivers', 'db_channels']
    search_fields = ['id', '^db_date_sent', '^db_message']
    save_as = True
    save_on_top = True
    list_select_related = True
#admin.site.register(Msg, MsgAdmin)


class ChannelAdmin(admin.ModelAdmin):
    inlines = [ChannelTagInline, ChannelAttributeInline]
    list_display = ('id', 'db_key', 'db_lock_storage', "subscriptions")
    list_display_links = ("id", 'db_key')
    ordering = ["db_key"]
    search_fields = ['id', 'db_key', 'db_aliases']
    save_as = True
    save_on_top = True
    list_select_related = True
    fieldsets = (
        (None, {'fields': (('db_key',), 'db_lock_storage', 'db_subscriptions')}),
        )

    def subscriptions(self, obj):
        "Helper method to get subs from a channel"
        return ", ".join([str(sub) for sub in obj.db_subscriptions.all()])

admin.site.register(ChannelDB, ChannelAdmin)
