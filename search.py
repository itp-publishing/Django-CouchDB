# -*- coding: utf-8 -

#  ITP - abar - CouchDB lucene search integration
#
#
#  Author: Martin Alcala Rubi - Tryolabs
#  e-mail: martin@tryolabs.com
#                                   Feb 2011
#

__author__="draix"

# For couchdb-lucene installation instructions please refer to lucene-installation file

from urllib import urlencode, urlopen, quote
import pprint as pp
from django.utils import simplejson


class SearchLucene(object):
    '''Manager for CouchDB Lucene search
    '''
    def __init__(self, host, db, design_doc):
        self._host = host
        self._db = db
        self._design_doc = design_doc

    def search(self, index, query, fuzzy=False, **kwargs):
        '''Query an index view

        The index will be implented in an design view ( like _design/title) for example
        in the abar_article DB and will look like this:

{
   "_id": "_design/fields",
   "_rev": "21-fa6d85e4f03b9d074f18b242c9073c2e",
   "fulltext": {
       "by_title_sectionid": {
           "index": "function(doc) { var ret=new Document(); ret.add(doc.section['id'], {'field':'section_id'}); ret.add(doc.title); return ret }"
       },
       "by_title": {
           "index": "function(doc) { var ret=new Document(); ret.add(doc.title); return ret }"
       },
       "by_intro_text": {
           "index": "function(doc) { var ret=new Document(); ret.add(doc.intro_text); return ret }"
       },
       "by_body": {
           "index": "function(doc) { var ret=new Document(); ret.add(doc.body); return ret }"
       },
       "by_title_intro_body": {
           "index": "function(doc) { var ret=new Document(); ret.add(doc.title); ret.add(doc.body); ret.add(doc.intro_text); return ret }"
       },
       "by_title_intro_body_section": {
           "index": "function(doc) { var ret=new Document(); ret.add(doc.title); ret.add(doc.body); ret.add(doc.intro_text); ret.add(doc.section['id'], {'field':'section_id', 'store':'yes'}); ret.add(doc.section['name'], {'field':'section_name', 'store':'yes'}); ret.add( doc.created , {'field': 'date', 'type' : 'date', 'store':'yes'}); return ret }"
       }
   }
}

        And could be queried by an http GET like this:

        curl -X GET http://localhost:5984/abar_article/_fti/_design/title/by_title?q=إماراتي

        The total index will look like this:

{
   "_id": "_design/total",
   "fulltext": {
       "by_every": {
           "index": "function(doc) { var ret = new Document(); function idx(obj) { for (var key in obj) { switch (typeof obj[key]) { case 'object': idx(obj[key]); break; case 'function': break; default: ret.add(obj[key]); break; } } }; idx(doc); return ret; }"
       }
   }
}

        :param index: indexing function
        :param fuzzy: fuzzy searches based on the Levenshtein Distance, or Edit Distance algorithm
        :param **kwargs: optional parameters for que query.
        '''

        #import pdb;pdb.set_trace()
        query = query.lstrip()
        query = query.rstrip()
        query = query.replace(" ", " OR ")
        if fuzzy:
            edit_distance = int(len(query)/3) # 30% of the lenght of the word
            query = "\"%s\"~%s" % (query, edit_distance)

        query_dic = {'q': query }
        if kwargs.has_key("options"):
            query_dic.update( kwargs['options'] )
        else:
            query_dic.update( { 'limit' : 10 } )

        query_string = urlencode( query_dic )
        url = ("%s/%s/_fti/%s/%s?%s") % (self._host, self._db, self._design_doc, index, query_string)
        print url
        search_results = urlopen(url)
        json_dict = simplejson.loads(search_results.read())
        #pp(json)
        return json_dict

