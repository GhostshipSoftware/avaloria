# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'ExternalChannelConnection'
        db.create_table('comms_externalchannelconnection', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('db_channel', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['comms.Channel'])),
            ('db_external_key', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('db_external_path', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('db_external_config', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('db_is_enabled', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('comms', ['ExternalChannelConnection'])

        db.rename_table('comms_channelconnection', 'comms_playerchannelconnection')
        
        # # Adding model 'PlayerChannelConnection'
        # db.create_table('comms_playerchannelconnection', (
        #     ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        #     ('db_player', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['players.PlayerDB'])),
        #     ('db_channel', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['comms.Channel'])),
        # ))
        # db.send_create_signal('comms', ['PlayerChannelConnection'])

        # # move channelconnections to playerchannelconnections        
        # for conn in orm.ChannelConnection.objects.all():
        #     ncon = orm.PlayerChannelConnection(db_player=conn.db_player, db_channel=conn.db_channel)
        #     ncon.save()

        # db
        # # Deleting model 'ChannelConnection'
        # db.delete_table('comms_channelconnection')

        # Adding field 'Msg.db_sender_external'
        db.add_column('comms_msg', 'db_sender_external', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True), keep_default=False)

        # Changing field 'Msg.db_sender'
        db.alter_column('comms_msg', 'db_sender_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['players.PlayerDB']))


    def backwards(self, orm):
        
        # # Adding model 'ChannelConnection'
        # db.create_table('comms_channelconnection', (
        #     ('db_channel', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['comms.Channel'])),
        #     ('db_player', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['players.PlayerDB'])),
        #     ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        # ))
        # db.send_create_signal('comms', ['ChannelConnection'])

        # 
        db.rename_table('comms_playerchannelconnection', 'comms_channelconnection')

        # Deleting model 'ExternalChannelConnection'
        db.delete_table('comms_externalchannelconnection')

        # # Deleting model 'PlayerChannelConnection'
        # db.delete_table('comms_playerchannelconnection')

        # Deleting field 'Msg.db_sender_external'
        db.delete_column('comms_msg', 'db_sender_external')

        # User chose to not deal with backwards NULL issues for 'Msg.db_sender'
        raise RuntimeError("Cannot reverse this migration. 'Msg.db_sender' and its values cannot be restored.")


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
        'auth.user': {
            'Meta': {'object_name': 'User'},
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
        'comms.channel': {
            'Meta': {'object_name': 'Channel'},
            'db_aliases': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'db_desc': ('django.db.models.fields.CharField', [], {'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'db_keep_log': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'db_key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'db_lock_storage': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'comms.externalchannelconnection': {
            'Meta': {'object_name': 'ExternalChannelConnection'},
            'db_channel': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['comms.Channel']"}),
            'db_external_config': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'db_external_key': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'db_external_path': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'db_is_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'comms.msg': {
            'Meta': {'object_name': 'Msg'},
            'db_channels': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'db_date_sent': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'db_hide_from_channels': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'db_hide_from_receivers': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'db_hide_from_sender': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'db_lock_storage': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'db_message': ('django.db.models.fields.TextField', [], {}),
            'db_receivers': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'db_sender': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sender_set'", 'null': 'True', 'to': "orm['players.PlayerDB']"}),
            'db_sender_external': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'comms.playerchannelconnection': {
            'Meta': {'object_name': 'PlayerChannelConnection'},
            'db_channel': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['comms.Channel']"}),
            'db_player': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['players.PlayerDB']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'objects.objectdb': {
            'Meta': {'object_name': 'ObjectDB'},
            'db_cmdset_storage': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'db_date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'db_destination': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'destinations_set'", 'null': 'True', 'to': "orm['objects.ObjectDB']"}),
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
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        }
    }

    complete_apps = ['comms']
