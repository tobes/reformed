import networkx as nx
import custom_exceptions
import sqlalchemy
import logging
import re

logger = logging.getLogger('reformed.main')

def get_key_data(key, database, table):
    """from a particular key get out what table the key relates to and the last 
    join to that table"""

    relations = key[::2]
    paths = database.tables[table].paths

    try:
        key_data = paths[relations]
    except KeyError:
        raise custom_exceptions.InvalidKey("key %s can not be used with %s table" , key, table)

    return key_data

def get_parent_key(key, all_rows):
    """get the key of the of the table that joins to the keys table"""
    
    if len(key) <= 2:
        return "root"
    try:
        prev_len = len(key)-2
        prev_key = key[0:prev_len]
        all_rows[key[0:prev_len]]
    except KeyError:
        raise custom_exceptions.InvalidKey("key %s does not have a parent key" , key)

    return prev_key

def check_correct_fields(row, database, table):

    for field in row.iterkeys():
        if not field.startswith("__") and\
               field not in database.tables[table].columns.iterkeys() and\
               field not in database.tables[table].relations.iterkeys() and\
               field <> "id":
            raise custom_exceptions.InvalidField("field %s not in table %s",
                                                 field, table)
def convert_unicode(value):
    if isinstance(value, basestring):
        return value.decode("utf8")
    return value

def string_key_parser(key_string):

    numbers = re.finditer("__[0-9]+__", key_string)

    key = []
    current_pos = 0
    for part in numbers:
        key.append(key_string[current_pos: part.start()])
        key.append(int(part.group(0)[2:-2]))
        current_pos = part.end() 
    key.append(key_string[current_pos:])
    return key

def get_keys_and_items_from_list(list):

    key_item_list = []
    for string_key in list:
        string_parsed = string_key_parser(string_key)
        key = tuple(string_parsed[:-1])
        item = string_parsed[-1]
        if key == ():
            key = "root"
        key_item_list.append([key, item])
    return key_item_list

def get_key_item_dict(key_item_list):

    key_item_dict = {}
    for key, item in key_item_list:
        if key == "root":
            key_item_dict.setdefault("root", {})[item] = None 
        else:
            key_item_dict.setdefault(tuple(key), {})[item] = None 
    return key_item_dict

def get_keys_from_list(key_item_list):

    all_rows = {}
    for key, item in key_item_list:
        if key != "root":
            all_rows[tuple(key)] = {}
        else:
            all_rows["root"] = {}

    return all_rows


class FlatFile(object):

    def __init__(self, database, table, headers, data):

        self.data = data
        self.database = database
        self.table = table

        self.parent_key = {}
        self.key_data = {}
        self.key_decendants = {}

        self.key_item_list = get_keys_and_items_from_list(headers)

        self.all_rows_template = get_keys_from_list(self.key_item_list)

        self.key_item_dict = get_key_item_dict(self.key_item_list)

        self.keys = self.all_rows_template.keys()

        self.key_data = self.make_key_data_dict()

        self.check_fields()

        self.get_all_decendants()
        
        self.keys.sort(lambda a, b : len(a) - len(b))


    def make_parent_key_dict(self):
        for key in self.keys:
            if key <> "root":
                self.parent_key[key] = get_parent_key(key, self.all_rows_template)
        return self.parent_key

    def make_key_data_dict(self):
        for key in self.keys:
            if key <> "root":
                self.key_data[key] = get_key_data(key, self.database, self.table)
        return self.key_data

    def check_fields(self):
        for key in self.keys:
            if key == "root":
                table = self.table
            else:
                table, relation = self.key_data[key]
            check_correct_fields(self.key_item_dict[key], self.database, table)

    def get_all_decendants(self):

        for key in self.keys:
            decendants = []
            if key == "root":
                decendants = [other_key for other_key in self.keys if other_key != "root"]
            else:
                key_len = len(key)
                for other_key in self.keys:
                    if other_key[:key_len] == key and other_key <> key:
                        decendants.append(other_key)
            self.key_decendants[key] = decendants

    def create_all_rows(self, row):

        if len(row) != len(self.key_item_list):
            raise custom_exceptions.InvalidRow("length of data is not the same as defined length")
        all_rows = {}
        for key in self.all_rows_template.iterkeys():
            all_rows[key] = {}
        for index, key_item in enumerate(self.key_item_list):
            key, item = key_item
            if row[index]:
                all_rows[key][item] = row[index]
        for key in self.keys:
            if key == "root":
                continue
            if not all_rows[key]:
                if not any([all_rows[other_key] for other_key in self.key_decendants[key]]):
                    all_rows.pop(key)
        return all_rows

    
                    

class SingleRecord(object):

    def __init__(self, database, table, data):

        self.data = data
        self.database = database
        self.table = table

        self.all_rows = {}
        self.all_obj = {} 

        self.process()

        self.keys = self.all_rows.keys()

        self.keys.sort(lambda a, b : len(a) - len(b))


    def load(self):

        self.session = self.database.Session()

        self.get_all_obj()

        self.add_all_values_to_obj()

        self.save_all_objs()

        self.session.commit()


    def save_all_objs(self):
        
        for key, obj in self.all_obj.iteritems():
            self.session.add(obj)


    def add_values_to_obj(self, key):

        for name, value in self.all_rows[key].iteritems():
            if not name.startswith("__"):
                setattr(self.all_obj[key], name, value)
    
    def add_all_values_to_obj(self):

        self.add_values_to_obj("root")
        for key in self.keys:
            if key <> "root":
                self.add_values_to_obj(key)


    def get_all_obj(self):

        self.get_root_obj()
        for key in self.keys:
            if key <> "root":
                self.get_obj(key)

    def get_root_obj(self):

        if not hasattr(self, "session"):
            self.session = self.database.Session()


        row = self.all_rows["root"]

        check_correct_fields(row, self.database, self.table)

        pk_list = self.database.tables[self.table].primary_key_columns.keys()

        if "id" in row.keys():
            obj = self.session.query(self.database.get_class(self.table)).filter_by( id = row["id"]).one()
        ##TODO incorrect need to check even if just one key is specified and error otherwise
        elif set(pk_list).intersection(set(row.keys())) == set(pk_list) and pk_list:
            try:
                pk_values = {}
                pk_list = self.database.tables[self.table].primary_key_columns.keys()
                for item in pk_list:
                    pk_values[item] = row[item]
                obj = self.session.query(self.database.get_class(self.table)).filter_by(**pk_values).one()
            except sqlalchemy.orm.exc.NoResultFound:
                obj = self.database.get_instance(self.table)
        else:
            obj = self.database.get_instance(self.table)

        self.all_obj["root"] = obj

        return obj
        

    def get_obj(self, key):

        table, join = get_key_data(key, self.database, self.table)
        parent_key = get_parent_key(key, self.all_rows)
        relation_name = key[-2]

        row = self.all_rows[key]

        check_correct_fields(row, self.database, table)

        if "id" in row.keys():
            obj = self.get_obj_with_id(key, row)
            self.all_obj[key] = obj
            return obj

        pk_list = self.database.tables[table].primary_key_columns.keys()
        ##TODO incorrect need to check even if just one key is specified and error otherwise
        if set(pk_list).intersection(set(row.keys())) == set(pk_list) and pk_list:
            obj = self.get_obj_with_pk(key, row)
            self.all_obj[key] = obj
            return obj

        ##TODO add a possibility to get objects by the order in their parents list

        parents_obj_relation = getattr(self.all_obj[parent_key], relation_name)
        if join in ("onetoone", "manytoone"):
            if parents_obj_relation is not None:
                self.all_obj[key] = parents_obj_relation
                return parents_obj_relation
            obj = self.database.get_instance(table)
            setattr(self.all_obj[parent_key], relation_name, obj)
            self.all_obj[key] = obj
            return obj
        
        obj = self.database.get_instance(table)
        parents_obj_relation.append(obj)
        self.all_obj[key] = obj
        return obj

    def get_obj_with_pk(self, key, row):
        table, join = get_key_data(key, self.database, self.table)
        row_number = key[-1]
        relation_name = key[-2]
        parent_key = get_parent_key(key, self.all_rows)


        pk_values = {}
        pk_list = self.database.tables[table].primary_key_columns.keys()
        for item in pk_list:
            pk_values[item] = row[item]

        parents_obj_relation = getattr(self.all_obj[parent_key], relation_name)

        if join in ("onetoone", "manytoone"):
            pk_current_values = {}
            for item in pk_list:
                pk_current_values[item] = getattr(parents_obj_relation, item)
            if pk_current_values != pk_values:
                raise custom_exceptions.InvalidData("""primary key value(s) %s in table %s
                                        either do(es) not exist or 
                                        is not associted with join"""
                                        % (pk_values, table))
            return parents_obj_relation

        if join in ("onetomany"):
            for obj in parents_obj_relation:
                pk_current_values = {}
                for item in pk_list:
                    pk_current_values[item] = getattr(obj, item)
                if pk_current_values == pk_values:
                    return obj
            raise custom_exceptions.InvalidData("""primary key value(s) %s in table %s
                                    either do(es) not exist or 
                                    is not associted with join"""
                                    % (pk_values, table))

    def get_obj_with_id(self, key, row):

        table, join = get_key_data(key, self.database, self.table)
        row_number = key[-1]
        relation_name = key[-2]
        parent_key = get_parent_key(key, self.all_rows)

        id = row["id"]

        parents_obj_relation = getattr(self.all_obj[parent_key], relation_name)
        if join in ("onetoone", "manytoone"):
            if parents_obj_relation.id <> id:
                raise custom_exceptions.InvalidData("""id %s in table %s
                                        either does not exist or 
                                        is not associted with join"""
                                        % (id, table))
            return parents_obj_relation
        if join in ("onetomany"):
            # may be better doing a query here instead of iterating over object lists"

            for obj in parents_obj_relation:
                if obj.id == id:
                    return obj
            raise custom_exceptions.InvalidData("""id %s in table %s
                                        either does not exist or 
                                        is not associted with join"""
                                        % (id, table))

    def process(self):

        for n, v in self.data.iteritems():
            if not isinstance(v, dict) and not isinstance(v, list):
                self.all_rows.setdefault("root", {})[n] = convert_unicode(v)
            if isinstance(v, list):
                self.process_list([n], v)
            if isinstance(v, dict):
                self.process_dict([n], v)

    def process_list(self, names, list):
        
        for index, value in enumerate(list):
            if isinstance(value, dict):
                self.process_dict(names + [index], value, from_list = True)
    
    def process_dict(self, names, sub_dict, from_list = False):

        for n, v in sub_dict.iteritems():
            if not isinstance(v, dict) and not isinstance(v, list):
                if from_list:
                    self.all_rows.setdefault(tuple(names), {})[n] = convert_unicode(v)
                else:
                    self.all_rows.setdefault(tuple(names + [0]), {})[n] = convert_unicode(v)
            if isinstance(v, list):
                if from_list:
                    self.process_list(names + [n], v)
                else:
                    self.process_list(names + [0,n], v)
            if isinstance(v, dict):
                if from_list:
                    self.process_dict(names + [n], v)
                else:
                    self.process_dict(names + [0,n], v)
            
