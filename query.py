from itpcouch.handler import ITP_CouchDB

class QueryManager():
    #TODO Move query here.
    pass

class ObjectManager():
    #Update Insert Delete an Object
    pass


class CouchQuery():

    def _set_all(self):

        self._filter_dict = {}
        self._exclude_dict = {}
        self._filter_dict__arr = {
            'in' : {},
            'gte' : {},
            'lte' : {},
        }
        self._exclude_dict__arr = {
            'in' : {},
            'gte' : {},
            'lte' : {},
        }

        self._order = "-id"
        self._limit = None
        self._descending = None
        self._skip = None # skip n number of documents
        self._cs = None # country switch for all queries
        self.return_k = "d._id";
        self.return_v = "d";
        self._filter_dict = {}
        self._clean_query = False #if set to true it invalidates any criterias and return all docs
        self.extras = ""

    def __init__(self, site_name, database,  lazy=False):   
        self._set_all()
        self._db = ITP_CouchDB( site_name , database )
        self._lazy = lazy
        self.couch_handler = self._db #mask

    def change_db( self, db ):
        self._db.select_db(db)

    def _query(self):

        """
        It's cleaner to have a set of for loops than a set of conidtions inside a for loop.
        """

        #malcala: added support for query options
        # The list of query parameters can be found at:
        # http://wiki.apache.org/couchdb/HTTP_view_API
        query_options = dict()
        if self._limit:
            query_options['limit'] = self._limit
        if self._descending:
            query_options['descending'] = self._descending
        if self._skip:
            query_options['skip'] = self._skip

        #if return all objects
        if self._clean_query:
            query = """function(d) {
                    emit ( %(return_k)s , %(return_v)s  )
            }"""% { 
                'return_k' : self.return_k,
                'return_v' : self.return_v,
            }

            return self._db.query(query, **query_options)


        filter_str = ""
        filter_str_in = "" 
        filter_str_gte = ""
        filter_str_lte = ""
        exclude_str = ""
        exclude_str_in = "" 
        exclude_str_gte = ""
        exclude_str_lte = ""

        sep = ""
        prev = 0 #used to see if we need to add && to the final query, if there is a previous one to this 

        for counter, flt in enumerate(self._filter_dict.iteritems()):
            prev = 1
            #malcala: country_id compound data support. Workaround
            #flt_cero = flt[0] # tuples do not support modifications
            #if flt_cero == 'country_id':
            #    flt_cero = 'countries.country.id'
            if counter != 0: sep="&&"
            filter_str = "%s%s"% ( filter_str, "%s ( d.%s == '%s' ) "% ( sep, flt[0] ,  flt[1] ) )
            #filter_str = "%s%s"% ( filter_str, "%s ( d.%s == '%s' ) "% ( sep, flt_cero ,  flt[1] ) )

        sep = ""
        for counter, flt in enumerate(self._exclude_dict.iteritems()):
            prev += 1
            if counter != 0: sep="&&"
            exclude_str = "%s%s"% ( exclude_str, "%s ( d.%s != '%s' ) "% ( sep, flt[0] , flt[1] ) )
            if prev > 1: exclude_str = " && %s" % exclude_str  

        sep = ""
        for counter, flt in enumerate(self._filter_dict__arr['gte'].iteritems()):
            prev += 1
            if counter != 0: sep="&&"
            #print filter_str_gte, counter
            filter_str_gte = "%s%s" % ( filter_str_gte, "%s ( d.%s > %s  )  " % ( sep, flt[0] , flt[1]  )  )
            #print filter_str_gte
            if prev > 1: filter_str_gte = " && %s" % filter_str_gte  
            #print filter_str_gte

        sep = ""
        for counter, flt in enumerate(self._exclude_dict__arr['gte'].iteritems()):
            prev += 1
            if counter != 0: sep="&&"
            exclude_str_gte = "%s%s" % ( exclude_str_gte, "%s ( d.%s <= %s  )  " % ( sep, flt[0] , flt[1]  )  )
            if prev > 1: exclude_str_gte = " && %s" % exclude_str_gte  

        sep = ""
        for counter, flt in enumerate(self._filter_dict__arr['lte'].iteritems()):
            prev += 1
            if counter != 0: sep="&&"
            filter_str_lte = "%s%s" % ( filter_str_lte, "%s ( d.%s < %s  )  " % ( sep, flt[0] , flt[1]  )  )
            if prev > 1: filter_str_lte = " && %s" % filter_str_lte  

        sep = ""
        for counter, flt in enumerate(self._exclude_dict__arr['lte'].iteritems()):
            prev += 1
            if counter != 0: sep="&&"
            exclude_str_lte = "%s%s" % ( exclude_str_lte, "%s ( d.%s >= %s  )  " % ( sep, flt[0] , flt[1]  )  )
            if prev > 1: exclude_str_lte = " && %s" % exclude_str_lte  

        sep = ""
        arr_content = ""
        for counter, flt in enumerate(self._filter_dict__arr['in'].iteritems()):
            prev += 1
            if counter != 0: sep="&&"
            flt_val = flt[1]
            try:
                flt_val  = [str(k).encode('ascii') for k in flt[1]]
            except:
                pass
            arr_content = "%s %s" % ( arr_content,  "var arr0%d = %s ; " % ( counter, str(flt_val)  ) )
            filter_str_in = "%s%s" % ( filter_str_in, "%s ( %s.indexOf( d.%s ) != -1 )  " % ( sep, "arr0%d"%counter , flt[0]  )  )
            if prev > 1: filter_str_in = " && %s" % filter_str_in  


        sep = ""
        for counter, flt in enumerate(self._exclude_dict__arr['in'].iteritems()):
            prev += 1
            if counter != 0: sep="&&"
            flt_val = flt[1]
            try:
                flt_val  = [str(k).encode('ascii') for k in flt[1]]
            except:
                pass
            arr_content = "%s %s" % ( arr_content,  "var arr1%d = %s ; " % ( counter, str(flt_val )  ) )
            exclude_str_in = "%s%s" % ( exclude_str_in, "%s ( %s.indexOf( d.%s ) == -1 )  " % ( sep, "arr1%d"%counter , flt[0]  )  )
            if prev > 1: exclude_str_in = " && %s" % exclude_str_in  



        query = """function(d) {
            %(arr_content)s

            %(extras)s            
 
            if (  %(filter_str)s  %(exclude_str)s  %(filter_str_gte)s  %(exclude_str_gte)s  %(filter_str_lte)s  %(exclude_str_lte)s  %(filter_str_in)s  %(exclude_str_in)s  ) {
                emit ( %(return_k)s , %(return_v)s  )
            } 
        }"""% { 
            'arr_content' : arr_content,
            'extras' : self.extras,
            'filter_str' : filter_str,
            'filter_str_lte' : filter_str_lte,
            'filter_str_gte' : filter_str_gte,
            'filter_str_in' : filter_str_in,
            'exclude_str' : exclude_str,
            'exclude_str_lte' : exclude_str_lte,
            'exclude_str_gte' : exclude_str_gte,
            'exclude_str_in' : exclude_str_in,
            'return_k' : self.return_k,
            'return_v' : self.return_v,
        }


        #print query

        #malcala: added support for query options
        # The list of query parameters can be found at:
        # http://wiki.apache.org/couchdb/HTTP_view_API
        query_options = dict()
        if self._limit:
            query_options['limit'] = self._limit
        if self._descending:
            query_options['descending'] = self._descending
        if self._skip:
            query_options['skip'] = self._skip


        res= self._db.query(query, **query_options)

        #import pdb; pdb.set_trace()
        return res

    def _add_filter_or_exclude(self, exclude, key, value):
        if exclude:
            self._exclude_dict.update( { key : value }  )
        else:
            self._filter_dict.update( { key : value }  )

    def _add_filter_or_exclude__(self, exclude, key, __val, param):
        if exclude:
            self._exclude_dict__arr[param].update( { key : __val }  )
        else:
            self._filter_dict__arr[param].update( { key : __val }  )


    def _filter_or_exclude( self, exclude,  dic={} , *args, **kwargs ):
        parse = kwargs if dic=={} else dic
        for key in parse:
            params = key.split("__") 
            if len( params  ) > 1:
                if params[1] not in ( "in" , "gte" , "lte"  ):
                    raise Exception( "Unsupported key word argument %s" %params[1] )
                self._add_filter_or_exclude__( exclude, params[0] , parse[key] , params[1]  )
                continue 
            self._add_filter_or_exclude(exclude, key, parse[key])

        if self._lazy:
            return self
        else:
            return self.fire()

    def dict_filter_or_exclude(self, exclude, dic={}):
        self._filter_or_exclude( exclude, dic)
        return self
    
    def filter(self, *args, **kwargs):
        """News.filter( slug = "", id="" , date__gte="", country_id=""  )"""
        return self._filter_or_exclude(False, *args, **kwargs)

    def exclude(self, *args, **kwargs):
        return self._filter_or_exclude(True, *args, **kwargs)

    def get(self, *args, **kwargs):
        """Returns one object"""
        self._lazy = True
        self.limit(1)
        self.filter( *args, **kwargs )
        res = self.fire()
        try:
            return res.rows[0].value
        except KeyError:
            return None

    def all(self):
        """That's when you don't want to write a criteria"""
        self._clean_query = True
        if not self._lazy: 
            return self._query()
        else:
            return self

    def view(self, view_name, options={}):
        """example: get all countries"""
        return self._db.query_view(view_name,options )


    def delete(self, _id, _rev):
        self._db.db.resource.delete_json(_id,rev= _rev)

    def order_by(self, field_name):
        """News.filter( slug = "", id="" , date__gte=""  ).exclude( id__in="2,4,5"  ).order_by("-id")"""
        self._order = field_name
        return self

    def limit(self, number):
        '''Limit results of a query

        :param number: Number of results to show
        '''
        self._limit = number
        return self

    def descending(self, condition):
        '''Reverse the output of a query

        :param condition: Boolean value. If 'True' the query will be reversed. Default is 'False'.
        '''
        descend = 'false'
        if condition:
            descend = 'true'

        self._descending = descend
        return self

    def skip(self, number):
        '''skip n number of documents

        :param number: number.
        '''
        self._skip = number
        return self

    def fire(self):
        res= self._query()
        self._set_all()
        return res



def query_interface( site_name="abar", db="article",  dic={} , limit=5, order_by="_id", desc=True, return_key="d._id", return_val="d", GET={}, extras="" ):
    """Query interface for limited ability to use objects ---- such as designer widget framework"""
    from news.couch_model import Article

    if dic == {}:
        return 
    db = CouchQuery( site_name, db , True  )
    if dic.has_key('filter'): 
        db.dict_filter_or_exclude(False, dic['filter']  ) 
    if dic.has_key('exclude'): 
        db.dict_filter_or_exclude(True, dic['exclude']  ) 
    db.limit(limit)
    db.descending( desc )
    db.order_by(order_by)
    db.return_k = return_key
    db.return_v = return_val
    db.extras = extras
    res = db.fire()

    return res
