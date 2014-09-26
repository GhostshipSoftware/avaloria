#
# This sets up how models are displayed
# in the web admin interface.
#

from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from src.players.models import PlayerDB
from src.typeclasses.admin import AttributeInline, TagInline
from src.utils import create


# handle the custom User editor
class PlayerDBChangeForm(UserChangeForm):

    class Meta:
        model = PlayerDB
        fields = '__all__'

    username = forms.RegexField(
        label="Username",
        max_length=30,
        regex=r'^[\w. @+-]+$',
        widget=forms.TextInput(
            attrs={'size': '30'}),
        error_messages={
            'invalid': "This value may contain only letters, spaces, numbers "
                       "and @/./+/-/_ characters."},
        help_text="30 characters or fewer. Letters, spaces, digits and "
                  "@/./+/-/_ only.")

    def clean_username(self):
        username = self.cleaned_data['username']
        if username.upper() == self.instance.username.upper():
            return username
        elif PlayerDB.objects.filter(username__iexact=username):
            raise forms.ValidationError('A player with that name '
                                        'already exists.')
        return self.cleaned_data['username']


class PlayerDBCreationForm(UserCreationForm):

    class Meta:
        model = PlayerDB
        fields = '__all__'

    username = forms.RegexField(
        label="Username",
        max_length=30,
        regex=r'^[\w. @+-]+$',
        widget=forms.TextInput(
            attrs={'size': '30'}),
        error_messages={
            'invalid': "This value may contain only letters, spaces, numbers "
                       "and @/./+/-/_ characters."},
        help_text="30 characters or fewer. Letters, spaces, digits and "
                  "@/./+/-/_ only.")

    def clean_username(self):
        username = self.cleaned_data['username']
        if PlayerDB.objects.filter(username__iexact=username):
            raise forms.ValidationError('A player with that name already '
                                        'exists.')
        return username


class PlayerForm(forms.ModelForm):
    """
    Defines how to display Players
    """
    class Meta:
        model = PlayerDB
        fields = '__all__'

    db_key = forms.RegexField(
        label="Username",
        initial="PlayerDummy",
        max_length=30,
        regex=r'^[\w. @+-]+$',
        required=False,
        widget=forms.TextInput(attrs={'size': '30'}),
        error_messages={
            'invalid': "This value may contain only letters, spaces, numbers"
                       " and @/./+/-/_ characters."},
        help_text="This should be the same as the connected Player's key "
                  "name. 30 characters or fewer. Letters, spaces, digits and "
                  "@/./+/-/_ only.")

    db_typeclass_path = forms.CharField(
        label="Typeclass",
        initial=settings.BASE_PLAYER_TYPECLASS,
        widget=forms.TextInput(
            attrs={'size': '78'}),
        help_text="Required. Defines what 'type' of entity this is. This "
                  "variable holds a Python path to a module with a valid "
                  "Evennia Typeclass. Defaults to "
                  "settings.BASE_PLAYER_TYPECLASS.")

    db_permissions = forms.CharField(
        label="Permissions",
        initial=settings.PERMISSION_PLAYER_DEFAULT,
        required=False,
        widget=forms.TextInput(
            attrs={'size': '78'}),
        help_text="In-game permissions. A comma-separated list of text "
                  "strings checked by certain locks. They are often used for "
                  "hierarchies, such as letting a Player have permission "
                  "'Wizards', 'Builders' etc. A Player permission can be "
                  "overloaded by the permissions of a controlled Character. "
                  "Normal players use 'Players' by default.")

    db_lock_storage = forms.CharField(
        label="Locks",
        widget=forms.Textarea(attrs={'cols': '100', 'rows': '2'}),
        required=False,
        help_text="In-game lock definition string. If not given, defaults "
                  "will be used. This string should be on the form "
                  "<i>type:lockfunction(args);type2:lockfunction2(args);...")
    db_cmdset_storage = forms.CharField(
        label="cmdset",
        initial=settings.CMDSET_PLAYER,
        widget=forms.TextInput(attrs={'size': '78'}),
        required=False,
        help_text="python path to player cmdset class (set in "
                  "settings.CMDSET_PLAYER by default)")


class PlayerInline(admin.StackedInline):
    """
    Inline creation of Player
    """
    model = PlayerDB
    template = "admin/players/stacked.html"
    form = PlayerForm
    fieldsets = (
        ("In-game Permissions and Locks",
         {'fields': ('db_lock_storage',),
         #{'fields': ('db_permissions', 'db_lock_storage'),
          'description': "<i>These are permissions/locks for in-game use. "
                         "They are unrelated to website access rights.</i>"}),
        ("In-game Player data",
         {'fields': ('db_typeclass_path', 'db_cmdset_storage'),
          'description': "<i>These fields define in-game-specific properties "
                         "for the Player object in-game.</i>"}))

    extra = 1
    max_num = 1


class PlayerTagInline(TagInline):
    model = PlayerDB.db_tags.through


class PlayerAttributeInline(AttributeInline):
    model = PlayerDB.db_attributes.through


class PlayerDBAdmin(BaseUserAdmin):
    """
    This is the main creation screen for Users/players
    """

    list_display = ('username', 'email', 'is_staff', 'is_superuser')
    form = PlayerDBChangeForm
    add_form = PlayerDBCreationForm
    inlines = [PlayerTagInline, PlayerAttributeInline]
    fieldsets = (
        (None, {'fields': ('username', 'password', 'email')}),
        ('Website profile', {
            'fields': ('first_name', 'last_name'),
            'description': "<i>These are not used "
                           "in the default system.</i>"}),
        ('Website dates', {
            'fields': ('last_login', 'date_joined'),
            'description': '<i>Relevant only to the website.</i>'}),
        ('Website Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser',
                       'user_permissions', 'groups'),
            'description': "<i>These are permissions/permission groups for "
                           "accessing the admin site. They are unrelated to "
                           "in-game access rights.</i>"}),
        ('Game Options', {
            'fields': ('db_typeclass_path', 'db_cmdset_storage',
                       'db_lock_storage'),
            'description': '<i>These are attributes that are more relevant '
                           'to gameplay.</i>'}))
        # ('Game Options', {'fields': (
        #     'db_typeclass_path', 'db_cmdset_storage',
        #     'db_permissions', 'db_lock_storage'),
        #     'description': '<i>These are attributes that are '
        #                    'more relevant to gameplay.</i>'}))

    add_fieldsets = (
        (None,
         {'fields': ('username', 'password1', 'password2', 'email'),
          'description': "<i>These account details are shared by the admin "
                         "system and the game.</i>"},),)

    def save_model(self, request, obj, form, change):
        obj.save()
        if not change:
            #calling hooks for new player
            ply = obj.typeclass
            ply.basetype_setup()
            ply.at_player_creation()

    ## TODO! Remove User reference!
    #def save_formset(self, request, form, formset, change):
    #    """
    #    Run all hooks on the player object
    #    """
    #    super(PlayerDBAdmin, self).save_formset(request, form, formset, change)
    #    userobj = form.instance
    #    userobj.name = userobj.username
    #    if not change:
    #        # uname, passwd, email = str(request.POST.get(u"username")), \
    #        #     str(request.POST.get(u"password1")), \
    #        #     str(request.POST.get(u"email"))
    #        typeclass = str(request.POST.get(
    #            u"playerdb_set-0-db_typeclass_path"))
    #        create.create_player("", "", "",
    #                             user=userobj,
    #                             typeclass=typeclass,
    #                             player_dbobj=userobj)

admin.site.register(PlayerDB, PlayerDBAdmin)
