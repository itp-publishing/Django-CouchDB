# -*- coding: utf-8 -
from uuid import uuid4
from couchdb import client
from couchdb.design import ViewDefinition
from django.conf import settings
from django.core import serializers

from itpcouch.search import *
#import httplib


class CouchDBImproperlyConfigured(Exception):
    pass

try:
    HOST = settings.COUCHDB_HOST
except AttributeError:
    raise CouchDBImproperlyConfigured("Please ensure that COUCHDB_HOST is set in your settings file.")


server = client.Server( HOST )
if settings.COUCHDB_USER not in ("", None) and settings.COUCHDB_PASSWORD not in ("", None):
    server.resource.credentials = ( settings.COUCHDB_USER  ,  settings.COUCHDB_PASSWORD )

CONFIG_DB = getattr(settings, 'COUCHDB_SITECONFIG', 'site_settings')
from django.core import serializers

try:
    config_db = server.create(CONFIG_DB)
except:
    config_db = server[CONFIG_DB]



class ConfigDB():

    def __init__(self, site):

        try:
            data = config_db.query("""function(d){ if (d.site == '%s'){ emit(d, null); }  }""" % ( site ))
        except IndexError:
            raise Exception("What are you thinking yourself doing? There is no such site really ! or this site has no DB defined.")

        #set all the values
        for key,value in data.rows[0].key.iteritems():
            setattr(self, key, value  )

    def add(self, key, value):
        '''Insert new attribute into configDB

        :param attr: attribute to add
        :param value: value for the attribute
        '''
        setattr(self, key, value)
        config_db[self._id] = self


class ITP_CouchDB():

    site       = ""
    db         = ""
    design_doc = ""

    def __init__(self,site_name, db, generic=False):
        self.site = ConfigDB( site_name )
        self.select_db(db)

    def select_db(self, db):
        db_name = getattr(self.site, "db_%s"%db )
        if db_name in ("", None):
            raise Exception("DB Does not exist.")
        self.db_name = db_name
        self.db = server[db_name]
        self.design_doc = "%s_design"%self.db

    def query(self, query, **kwargs):
        '''Query the view
        '''
        #malcala: added the option to include kwargs for que query. For more info
        # check 'Query Options' in http://wiki.apache.org/couchdb/HTTP_view_API
        # For example you can use this options lo limit your query with the
        # kwarg: limit='3'
        return self.db.query(query, **kwargs)

    def get_one(self,query):
        res = self.query(query)
        try:
            return res.rows[0]['value'] 
        except IndexError:
            return None


    def query_view(self,view_name, options={}):
        res = self.db.view(view_name,None, options=options)
        #Fix for a bug in couchdb-python library. TODO write a custom lib!
        res = client.ViewResults(res.view, options)
        return res

    def create_view(self,design, name, map_fun, reduce_fun=None, language='javascript', wrapper=None, **defaults):
        """Just uses ViewDefinition but makes sure it uses it"""
        view = ViewDefinition( design, name, map_fun, reduce_fun=None, language='javascript', wrapper=None, **defaults )
        view.sync(self.db)


    def store(self, key, value):
        self.db[key] = value



    def update_dict(self, key, value, rev):
        """value must be a dict not encoded with json"""
        try:
            self.db[key] = value
        except:
            if isinstance(value, dict ):
                value.update({'rev' : rev})
                jsn = serializers.serialize("json", value)
                self.db[key] = jsn
            else:
                return None
    
    def delete(self, _id, _rev):
        self.db.resource.delete(_id,rev= _rev)

    def update(self, key, value):
        """value must be a json dict including the REV"""
        self.db[key] = value

    def search(self, index_design_doc, index, query, fuzzy=False, options={}):
        '''Query the couchDB using lucene integration

        :param index_design_doc: design document
        :param index: index to be queried
        :param query: query made using lucene query syntax
        '''
        lucene_search = SearchLucene(HOST, self.db.name, index_design_doc)
        return lucene_search.search(index, query, fuzzy=fuzzy, options=options )

    def new(self, value):
        '''Creates a new document into the couchDB

        Notes on not using couchdb.client.Database.create(data): http://packages.python.org/CouchDB/client.html#server

        "Note that it is generally better to avoid the create() method and instead generate document IDs on the client side.
        This is due to the fact that the underlying HTTP POST method is not idempotent, and an automatic retry due to a problem
        somewhere on the networking stack may cause multiple documents being created in the database.

        To avoid such problems you can generate a UUID on the client side."

        :param value: json value to be stored
        '''
        doc_id = uuid4().hex           
        self.db[doc_id] = value 
        #value['UUID'] = doc_id
        #self.db.create(value)


def view_interface(site_name, db, options, GET={}):
    """Handler query view interface for limited ability to use objects ---- such as designer widget framework"""

    from news.couch_model import Article
    db = ITP_CouchDB(site_name, db)
    try:
        options = dict((k.encode('ascii'), v) for (k, v) in options.items())
    except :
        pass

    view = options['view']
    design = options['design_name']

    design_view = str(design+"/"+view)
    res = db.query_view(design_view, options)

    return res
