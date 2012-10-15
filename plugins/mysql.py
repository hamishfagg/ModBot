import MySQLdb as mysql
from mysqlconf import *
from constants import *

class Plugin():
    depends = ['logger']

    def connect(self):
        self.db = mysql.connect(host=DBHOST, user=DBUSER, passwd=DBPASS, db=DBNAME)
        
        dbuser = None
        dbpass = None # Dunno if this helps
        self.cur = self.db.cursor()

    def update(self, table, data={}, conditions={}):
        self.db.ping(1)

        query = self.unpack(data, conditions)
        query[0] = 'UPDATE %s SET ' % table + query[0]

        self.cur.execute(query[0], query[1])

    def iupdate(self, table, data={}, conditions={}):
        self.db.ping(1)
        
        if len(self.find(table=table, fields=['id'], conditions=conditions)) > 0:
            self.update(table=table, data=data, conditions=conditions)              # The row already exists
        else:
            self.insert(table=table, data=data)

    def insert(self, table, data={}):
        self.db.ping(1)

        if data == {}:
            self.cur.execute("""INSERT %s (id) VALUES (DEFAULT)""" % table)
        else:
            datalist = []
            query = "INSERT INTO %s (" % table

            # Generate query string and data list
            for key, value in data.items():
                query += key+', '
                datalist.append(value)
            query = query[:-2]
            query += ') VALUES ('
            for i in datalist: query += '%s, '
        
            query = query[:-2]
            query += ')'
            self.cur.execute(query, datalist)

    def find(self, table, fields=[], conditions={}, order=None, limit=None):
        self.db.ping(1)
        if fields == []: fields = '*'

        query = self.unpack(conditions=conditions)
        query[0] = 'SELECT %s FROM %s ' % (", ".join(fields), table) + query[0]

        if order != None: query[0] += " ORDER BY %s" % order
        if limit  != None: query[0] += " LIMIT %s" % limit
        self.cur.execute(query[0], query[1])

        return self.cur.fetchall()

    def execute(self, string, args=None):
        self.cur.execute(string, args)
        return self.cur.fetchall()

    def unpack(self, data={}, conditions={}):
        query = ''
        datalist = []
        for key, value in data.items():
            datalist.append(value)
            query += '`'+key+'` = %s, '
        query = query[:-2]

        if conditions != {}:
            query += ' WHERE '
            for key, value in conditions.items():
                datalist.append(value)
                query += '`'+key+'` = %s AND '
            query = query[:-5]
        return [query, datalist]
