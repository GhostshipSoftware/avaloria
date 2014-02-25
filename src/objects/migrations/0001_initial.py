# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

try:
    from django.contrib.auth import get_user_model
except ImportError: # django < 1.5
    from django.contrib.auth.models import User
else:
    User = get_user_model()

user_orm_label = '%s.%s' % (User._meta.app_label, User._meta.object_name)
user_model_label = '%s.%s' % (User._meta.app_label, User._meta.module_name)
user_ptr_name = '%s_ptr' % User._meta.object_name.lower()

class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding model 'ObjAttribute'
        db.create_table('objects_objattribute', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('db_key', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('db_value', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('db_mode', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('db_lock_storage', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('db_date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('db_obj', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['objects.ObjectDB'])),
        ))
        db.send_create_signal('objects', ['ObjAttribute'])

        # Adding model 'Alias'
        db.create_table('objects_alias', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('db_key', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('db_obj', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['objects.ObjectDB'])),
        ))
        db.send_create_signal('objects', ['Alias'])

        # Adding model 'Nick'
        db.create_table('objects_nick', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('db_nick', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('db_real', self.gf('django.db.models.fields.TextField')()),
            ('db_type', self.gf('django.db.models.fields.CharField')(default='inputline', max_length=16, null=True, blank=True)),
            ('db_obj', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['objects.ObjectDB'])),
        ))
        db.send_create_signal('objects', ['Nick'])

        # Adding unique constraint on 'Nick', fields ['db_nick', 'db_type', 'db_obj']
        db.create_unique('objects_nick', ['db_nick', 'db_type', 'db_obj_id'])

        # Adding model 'ObjectDB'
        db.create_table('objects_objectdb', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('db_key', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('db_typeclass_path', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('db_date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('db_permissions', self.gf('django.db.models.fields.CharField')(max_length=512, blank=True)),
            ('db_lock_storage', self.gf('django.db.models.fields.TextField')(blank=True)),
            # Moved to player migration
            #('db_player', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['players.PlayerDB'], null=True, blank=True)),
            ('db_location', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='locations_set', null=True, to=orm['objects.ObjectDB'])),
            ('db_home', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='homes_set', null=True, to=orm['objects.ObjectDB'])),
            ('db_cmdset_storage', self.gf('django.db.models.fields.TextField')(null=True)),
        ))
        db.send_create_signal('objects', ['ObjectDB'])


    def backwards(self, orm):

        # Removing unique constraint on 'Nick', fields ['db_nick', 'db_type', 'db_obj']
        db.delete_unique('objects_nick', ['db_nick', 'db_type', 'db_obj_id'])

        # Deleting model 'ObjAttribute'
        db.delete_table('objects_objattribute')

        # Deleting model 'Alias'
        db.delete_table('objects_alias')

        # Deleting model 'Nick'
        db.delete_table('objects_nick')

        # Deleting model 'ObjectDB'
        db.delete_table('objects_objectdb')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        user_model_label: {
            'Meta': {'object_name': User.__name__, 'db_table': "'%s'" % User._meta.db_table},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'objects.alias': {
            'Meta': {'object_name': 'Alias'},
            'db_key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'db_obj': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['objects.ObjectDB']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'objects.nick': {
            'Meta': {'unique_together': "(('db_nick', 'db_type', 'db_obj'),)", 'object_name': 'Nick'},
            'db_nick': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'db_obj': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['objects.ObjectDB']"}),
            'db_real': ('django.db.models.fields.TextField', [], {}),
            'db_type': ('django.db.models.fields.CharField', [], {'default': "'inputline'", 'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'objects.objattribute': {
            'Meta': {'object_name': 'ObjAttribute'},
            'db_date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'db_key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'db_lock_storage': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'db_mode': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'db_obj': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['objects.ObjectDB']"}),
            'db_value': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'objects.objectdb': {
            'Meta': {'object_name': 'ObjectDB'},
            'db_cmdset_storage': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'db_date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'db_home': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'homes_set'", 'null': 'True', 'to': "orm['objects.ObjectDB']"}),
            'db_key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'db_location': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'locations_set'", 'null': 'True', 'to': "orm['objects.ObjectDB']"}),
            'db_lock_storage': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'db_permissions': ('django.db.models.fields.CharField', [], {'max_length': '512', 'blank': 'True'}),
            'db_player': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['players.PlayerDB']", 'null': 'True', 'blank': 'True'}),
            'db_typeclass_path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'players.playerdb': {
            'Meta': {'object_name': 'PlayerDB'},
            'db_date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'db_key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'db_lock_storage': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'db_obj': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['objects.ObjectDB']", 'null': 'True'}),
            'db_permissions': ('django.db.models.fields.CharField', [], {'max_length': '512', 'blank': 'True'}),
            'db_typeclass_path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['%s']" % user_orm_label, 'unique': 'True'})
        }
    }

    complete_apps = ['objects']
