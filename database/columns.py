##   This file is part of Reformed.
##
##   Reformed is free software: you can redistribute it and/or modify
##   it under the terms of the GNU General Public License version 2 as
##   published by the Free Software Foundation.
##
##   Reformed is distributed in the hope that it will be useful,
##   but WITHOUT ANY WARRANTY; without even the implied warranty of
##   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##   GNU General Public License for more details.
##
##   You should have received a copy of the GNU General Public License
##   along with Reformed.  If not, see <http://www.gnu.org/licenses/>.
##
##   -----------------------------------------------------------------
##	
##   Reformed
##   Copyright (c) 2008-2009 Toby Dacre & David Raznick
##	
##	columns.py
##	======
##	
##	This file contains the classes that hold information about database
##  fields such as name,type, indexes and constraints.

import util
import custom_exceptions

class BaseSchema(object):
    """Base class of everthing that turn into a database field or
    constraint or index. Its only use is to gather the type and name
    of the field, constraint or index.

    :param type: This is either a sqlalchemy type or a string
            with onetomany, manytoone or onetoone to define join types.

    :param use_parent:  if True will use its parents (Field) column parameters
                  and name.
    :param use_parent_options:  if True will use its parents parameters only.
    """

    sa_allowed_options = []

    def __init__(self, rtype, *args, **kw):

        self.type = rtype
        self.name = kw.pop("name", None)
        self.use_parent = kw.pop("use_parent", False)
        self.use_parent_options = kw.pop("use_parent_options", False)
        self.defined_relation = kw.pop("defined_relation", None)
        self.sa_options = {}

    def _set_name(self, field, name):
        if self.use_parent:
            self.name = field.name
        else:
            self.name = name

    def _set_sa_options(self, field):

        if self.use_parent or self.use_parent_options:
            for key, value in field.sa_options.iteritems():
                if key in self.sa_allowed_options:
                    self.sa_options[key] = value



    def __repr__(self):
        return "<class = %s, name = %s, type = %s>" % \
                (self.__class__.__name__, self.name, self.type)

    @property
    def table(self):
        """The table object accociated with this object"""
        if self.defined_relation:
            return self.defined_relation.table
        if not hasattr(self, "parent"):
            raise custom_exceptions.NoFieldError("no field defined for column")
        return self.parent.table

class Column(BaseSchema):
    """Contains information to make a database field.
    :param default: default value for the column
    :param onupdate: value whenever the accosiated row is updated
    :param mandatory: boolean saying if the column will be not nullable and not empty string
    :param nullable: boolean saying if column in nullable
    """

    sa_allowed_options = ["default", "nullable", "on_update"]

    def __init__(self, type, *args, **kw):

        super(Column, self).__init__(type , *args, **kw)
        ##original column should be made private.
        self.original_column = kw.pop("original_column", None)
        default = kw.get("default", None)
        if default is not None:
            self.sa_options["default"] = default
        onupdate = kw.pop("onupdate", None)
        if onupdate:
            self.sa_options["onupdate"] = onupdate

        try:
            self.length = self.type.length
        except AttributeError:
            self.length = None

        self.nullable = kw.pop("nullable", True)
        self.mandatory = kw.pop("mandatory", False)
        if self.mandatory:
            self.nullable = False
        self.sa_options["nullable"] = self.nullable

        self.validation = kw.pop("validation", None)
        self.validate = kw.pop("validate", True)
        self.parent = None

    def _set_parent(self, parent, name):

        self._set_name(parent, name)
        self._set_sa_options(parent)

        if self.use_parent:
            if parent.length:
                self.type.length = parent.length
            else:
                parent.length = self.length
            if parent.field_validation:
                self.validation = parent.field_validation
            if parent.mandatory:
                self.mandatory = parent.mandatory

        if self.name in parent.items.iterkeys():
            raise AttributeError("column already in field definition")
        else:
            parent.add_column(self.name, self)
            self.parent = parent

class Index(BaseSchema):

    def __init__(self, type, fields, *args, **kw):
        self.fields = fields
        self.type = type
        super(Index, self).__init__(type , *args, **kw)

    def _set_parent(self, parent, name):

        self._set_name(parent, name)

        if self.name in parent.items.iterkeys():
            raise AttributeError("index name already in field definition")
        else:
            parent.add_index(self.name, self)
            self.parent = parent

class Constraint(BaseSchema):

    def __init__(self, type, fields, *args, **kw):
        self.fields = fields
        self.type = type
        super(Constraint, self).__init__(type , *args, **kw)

    def _set_parent(self, parent, name):

        self._set_name(parent, name)

        if self.name in parent.items.iterkeys():
            raise AttributeError("constraint name already in field definition")
        else:
            parent.add_constraint(self.name, self)
            self.parent = parent

class Relation(BaseSchema):
    """Specifies a relationship between the table where this relation
    is defined and another table.  You cannot specify more that one relation
    going from one table to another.
    i.e you can not have more that one relation defined on table "a" that
    joins to table "b". You can however also have a relation on table "b" that joins
    to table "a". There for there is a maximum of two relations bewtween any
    two tables.

    type and other are mandatory for relations

    :param type: specifies join type. Accepts onetoone, onetomany and
        manytoone.

    :param other: The name of the table where this reltaion will
        join to.

    :param eager: Boolean stating if the other table is automatically
        eager loaded.

    :param cascade: Default cascade options see sqlalchemy docs for details

    :param backref: Name the attribute that will occur on the instance of the
        other tables sqlalchemy objects. By default this will be _thistable
        where this table is the name of the table where this relation is
        defined.

    :param one_way: This is to be put at the last edge of where the tables
        join paths comes back in a cycle. If the one_way parmeter is not set
        for tables whos joins loop back to a table search fuctionality wont
        work.
        ie.  table "a" has a relation to "b" and "b" has a relation back to "a"
        In this case you would put the one_way flag on the secone relation
        defined on "b".
    """

    sa_allowed_options = ["uselist", "lazy", "cascade", "backref"]

    def __init__(self, type, other, *args, **kw):

        super(Relation, self).__init__(type , *args, **kw)
        self.other = other
        self.original_type = type
        assert self.type in ("onetoone", "onetooneother",
                             "manytoone", "onetomany")
        if self.type == "onetooneother":
            self.type = "onetoone"

        if self.type == "onetoone":
            self.sa_options["uselist"] = False

        eager = kw.pop("eager", None)
        if eager:
            self.sa_options["lazy"] = not eager
        cascade = kw.pop("cascade", None)
        if cascade:
            self.sa_options["cascade"] = cascade

        self.foreign_key_name = kw.pop("foreign_key_name", None)

        self.many_side_not_null = kw.pop("many_side_not_null", True)
        self.many_side_mandatory = kw.pop("many_side_mandatory", False)
        self.many_side_default = kw.get("many_side_default", None)
        self.many_side_onupdate = kw.get("many_side_onupdate", None)

        backref = kw.pop("backref", None)
        if backref is not None:
            self.sa_options["backref"] = backref
        self.one_way = kw.pop("one_way", None)
        self.no_auto_path = kw.get("no_auto_path", False)
        self.parent = None

    def _set_parent(self, parent, name):
        """adds this relation to a field object"""
        self._set_name(parent, name)
        self._set_sa_options(parent)

        if self.use_parent:
            if parent.many_side_not_null is False:
                self.many_side_not_null = parent.many_side_not_null
            if parent.many_side_mandatory is True:
                self.many_side_mandatory = parent.many_side_mandatory
            if parent.many_side_default is not None:
                self.many_side_default = parent.many_side_default
            if parent.many_side_onupdate is not None:
                self.many_side_onupdate = parent.many_side_onupdate
            if parent.one_way:
                self.one_way = True
            if parent.no_auto_path:
                self.no_auto_path = True
            if parent.foreign_key_name:
                self.foreign_key_name = parent.foreign_key_name

        if self.name in parent.items.iterkeys():
            raise AttributeError("column already in field definition")
        else:
            parent.add_relation(self.name, self)
            self.parent = parent

    def join_type_from_table(self, table_name):

         if self.table.name == table_name:
             return self.type
         if self.other == table_name:
             return util.swap_relations(self.type)


    def _set_name(self, field, name):
        if self.use_parent:
            self.name = "_rel_" + field.relation_name
        else:
            self.name = "_rel_" + name

    @property
    def foreign_key_table(self):

        if self.original_type in ("manytoone", "onetoone"):
            return self.table.name
        else:
            return self.other

    @property
    def primary_key_table(self):

        if self.original_type in ("manytoone", "onetoone"):
            return self.other
        else:
            return self.table.name

    @property
    def foriegn_key_id_name(self):

        return self.join_keys_from_table(self.foreign_key_table)[0][0]

    @property
    def foreign_key_constraint_name(self):

        return self.table.name + "__" + self.name

    def join_keys_from_table(self, table_name):

         table = self.table.database.tables[table_name]

         if self.parent.table.name == table_name:
             return self.this_table_join_keys
         if self.other == table_name:
             return self.this_table_join_keys[::-1]


    @property
    def other_table(self):
        """Table object of related table"""

        try:
            return self.parent.table.database.tables[self.other]
        except AttributeError:
            return None

    @property
    def this_table_join_keys(self):
        keys_this_table = []
        keys_other_table = []
        if self.original_type in ("manytoone", "onetoone"):
            for name, column in self.table.foriegn_key_columns.iteritems():
                if column.defined_relation == self and column.original_column == "id":
                    keys_this_table.append(name)
                    keys_other_table.append(column.original_column)
        if self.original_type in ("onetooneother", "onetomany"):
            for name, column in self.other_table.foriegn_key_columns.iteritems():
                if column.defined_relation == self and column.original_column == "id":
                    keys_this_table.append(column.original_column)
                    keys_other_table.append(name)

        return [keys_this_table, keys_other_table]




class Field(object):
    """ This is intended to be sublassed and should be the only way
    a database field or relation can be made.  This object can contain
    one or more column object (representing a database field) or one
    relation object (representing a database relataion with a foreign key).
    Examples are in fields.py

    :param name:  field name will be used as column name if use_parent is
           used

    A field can also have any paremeters defined for a column or relation
    as long as the field only has one column or relation and the use parent
    or use_parent_option flag is set for that column or relation.
    """

    extra_kw = []

    modifiable_kw = ["eager", "cascade", "backref", "one_way",
                     "no_auto_path", "description", "generator",
                     "cat", "relation_name", "validation"]

    restricted_kw = ["field_id", "foreign_key_name", "default",
                     "onupdate", "nullable", "mandatory",
                     "length", "many_side_not_null","many_side_mandatory",
                     "many_side_default", "many_side_onupdate", "order_by"]


    def __new__(cls, name, *args, **kw):

        cls.all_kw = set(cls.modifiable_kw + cls.restricted_kw
                         + cls.extra_kw)
        cls.all_updatable_kw = set(cls.modifiable_kw + cls.extra_kw)

        assert set(kw.keys()) - cls.all_kw == set()

        obj = object.__new__(cls)
        obj.name = name.encode("ascii")
        obj.relation_name = kw.get("relation_name", name)
        obj.columns = {}
        obj.relations = {}
        obj.indexes = {}
        obj.constraints = {}
        obj.sa_options = {}
        obj.column_order = []
        obj.args = args
        obj.kw = kw
        obj.field_id = kw.get("field_id", None)

        obj.cat = kw.get("cat", None)

        obj.foreign_key_name = kw.get("foreign_key_name", None)

        obj.default = kw.get("default", None)
        if obj.default is not None:
            obj.sa_options["default"] = obj.default
        obj.onupdate = kw.get("onupdate", None)
        if obj.onupdate:
            obj.sa_options["onupdate"] = obj.onupdate

        obj.nullable = kw.get("nullable", True)
        obj.mandatory = kw.get("mandatory", False)
        if obj.mandatory:
            obj.nullable = False
        if obj.nullable == False:
            obj.sa_options["nullable"] = obj.nullable

        obj.eager = kw.get("eager", None)
        if obj.eager:
            obj.sa_options["lazy"] = not obj.eager
        obj.cascade = kw.get("cascade", None)
        if obj.cascade:
            obj.sa_options["cascade"] = obj.cascade
        obj.backref = kw.get("backref", None)
        if obj.backref is not None:
            obj.sa_options["backref"] = obj.backref
        obj.field_validation = kw.get("validation", None)
        if obj.field_validation:
            obj.field_validation = r"%s" % obj.field_validation.encode("ascii")
        obj.order_by = kw.get("order_by", None)
        obj.length = kw.get("length", None)
        ## ignore length if empty string
        if not obj.length:
            kw.get("length", None)
        else:
            obj.length = int(obj.length)
        obj.many_side_not_null = kw.get("many_side_not_null", True)
        obj.many_side_mandatory = kw.get("many_side_mandatory", False)

        obj.many_side_default = kw.get("many_side_default", None)
        obj.many_side_onupdate = kw.get("many_side_onupdate", None)

        obj.one_way = kw.get("one_way", None)

        obj.no_auto_path = kw.get("no_auto_path", False)

        obj.data_type = None

        obj.description = kw.get("description", None)
        obj.generator = kw.get("generator", None)

        return obj

    def code_repr(self):

        class_name = self.__class__.__name__
        kw_display = ""
        arg_display = ""

        if self.args:
            arg_list = ["%s" % repr(i) for i in self.args]
            arg_display = ", " + ", ".join(arg_list)
        if self.kw:
            kw_list = ["%s = %s" % (i[0], repr(i[1])) for i in self.kw.items()]
            kw_display = ", " + ", ".join(sorted(kw_list))
        
        return "%s('%s'%s%s)" % (class_name, self.name, arg_display, kw_display) 


    def __eq__(self, other):
        if (self.__class__.__name__ == other.__class__.__name__
            and self.name == other.name
            and self.kw == other.kw):
            return True
        else:
            False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "<%s - %s>" % (self.name, self.column_order)

    def __setattr__(self, name, value):

        if isinstance(value, BaseSchema):
            value._set_parent(self, name)
        else:
            object.__setattr__(self, name, value)

    def set_kw(self, key, value):

        if key not in self.all_updatable_kw:
            raise ValueError("%s not allowed to be added or modified" % key)

        database = self.table.database
        with util.SchemaLock(database) as file_lock:
            self.kw[key] = value
            setattr(self, key, value)
            file_lock.export()


    def diff(self, other):

        new = {}
        removed = {}
        difference = {}

        for name, value in self.kw.iteritems():
            if name not in other.kw:
                new[name] = value

        for name, value in other.kw.iteritems():
            if name not in self.kw:
                removed[name] = value

        for name, value in self.kw.iteritems():
            if name in other.kw and value <> other.kw[name]:
                difference[name] = [other.kw[name], value]

        return new, removed, difference

    @property
    def category(self):

        if self.cat:
            return self.cat

        if self.column:
            if self.column.name.startswith("_"):
                return "internal"
            else:
                return "field"
        if self.columns:
            return "multi_field"
        if self.relations:
            return "relation"
        if self.constraints:
            return "constraint"
        if self.indexes:
            return "index"

    @property
    def type(self):
        if self.data_type:
            return self.data_type
        else:
            return self.__class__.__name__

    @property
    def column(self):
        if len(self.columns) == 1:
            return self.columns.copy().popitem()[1]

    @property
    def relation(self):
        if len(self.relations) == 1:
            return self.relations.copy().popitem()[1]

    @property
    def validation_info(self):
        if not self.column:
            raise AttributeError("can only get validation info on "
                                 "fields with one column")

        all_validator = self.table.schema_dict[self.column.name]
        info = []

        for validator in all_validator.validators:
            validator_info = {}

            validator_info["type"] = validator.__class__.__name__

            for name, attrib in validator.__dict__.iteritems():
                if name in ('declarative_count', 'inputEncoding', 'outputEncoding'):
                    continue
                if name.startswith("_"):
                    continue
                validator_info[name] = attrib

            info.append(validator_info)

        return info

    @property
    def items(self):
        """all columns and relation related to this field"""
        items = {}
        items.update(self.columns)
        items.update(self.relations)
        items.update(self.constraints)
        items.update(self.indexes)
        return items

    def add_column(self, name, column):
        self.columns[name] = column
        self.column_order.append(name)

    def add_relation(self, name, relation):
        self.relations[name] = relation

    def add_index(self, name, index):
        self.indexes[name] = index

    def add_constraint(self, name, constraint):
        self.constraints[name] = constraint

    def _set_parent(self, table):

        self.check_table(table)
        max_field_id = table.max_field_id
        if not self.field_id:
            new_id = table.max_field_id + 1
            table.max_field_id = new_id
            self.kw["field_id"] = new_id
            self.field_id = new_id
        else:
            table.max_field_id = max(table.max_field_id, self.field_id)

        table.fields[self.name] = self
        table.field_list.append(self)
        if not table.persisted:
            table.field_order.append(self.name)
        table.add_relations()
        if hasattr(table, "database"):
            table.database.add_relations()
        self.table = table

    def check_table(self, table):
        """check to see if this fields columns or relation name clash with
        any fields or columns in a table.

        :param table:  rtable to check this field against
        """
        for name, item in self.items.iteritems():
            if name in table.items.iterkeys():
                raise AttributeError("already an item named %s in %s" %
                                     (name, table.name))

