from custom_exceptions import DependencyError
from sqlalchemy.orm import attributes
import sqlalchemy as sa
from sqlalchemy.sql import func, select, and_, cast
from operator import add
import datetime
import custom_exceptions
import logging

logger = logging.getLogger('rebase.actions')

class PersistBaseClass(object):

    def __new__(cls, *args, **kw):

        obj = object.__new__(cls)
        obj._args = list(args)
        obj._kw = kw.copy()
        obj._class_name = cls.__name__

        return obj


class Action(PersistBaseClass):

    post_flush = False

    def __call__(self, action_state):
        
        logger.info(self.__class__.__name__)
        logger.info(action_state.__dict__)
        self.run(action_state)
            
class AddRow(Action):

    def __init__(self, related_table, pre_flush = True):

        self.related_table = related_table
        self.pre_flush = pre_flush

    def run(self, action_state):

        object = action_state.object
        table = object._table
        database = table.database
        session = action_state.session

        path = table.get_path(self.related_table)

        if len(path) != 1:
            raise custom_exceptions.InvalidTableReference(
                "table %s not one join away from objects table %s" % 
                (self.related_table, table.name))

        new_obj = database[self.related_table].sa_class()

        setattr(object, path[0], new_obj)
        session.add_no_validate(new_obj)


class DeleteRows(Action):

    def __init__(self, related_table):

        self.related_table = related_table

    def run(self, action_state):

        object = action_state.object

        table = object._table
        database = table.database
        session = action_state.session

        path = table.get_path(self.related_table)
        new_obj = object

        for item in path:
            to_delete = getattr(new_obj, item)
            new_obj = to_delete
            session.delete(to_delete)


class SumEvent(Action):

    def __init__(self, result_field, number_field):

        self.result_field = result_field
        self.number_field = number_field

    def run(self, action_state):

        object = action_state.object
        table = object._table
        database = table.database
        session = action_state.session
        event_type = action_state.event_type

        path = table.get_path_from_field(self.result_field)
        result_field = self.result_field.split(".")[-1]

        new_obj = object

        for relation in path:
            new_obj = getattr(new_obj, relation)
            assert new_obj is not None


        value = getattr(object, self.number_field)

        new_table = new_obj._table

        if event_type == "delete":
            diff = -value
        elif event_type == "new":
            diff = value
        elif event_type == "change":
            a, b, c = attributes.get_history(
                attributes.instance_state(object),
                self.number_field,
                passive = False
            )
            if not c:
                return
            diff = value - c[0]
        else:
            return


        setattr(new_obj, result_field,
                new_table.sa_table.c[result_field] + diff)

        action_state.session.add_no_validate(new_obj)



class CountEvent(Action):

    def __init__(self, result_field, number_field):

        self.result_field = result_field
        self.number_field = number_field

    def run(self, action_state):

        object = action_state.object
        table = object._table
        database = table.database
        session = action_state.session
        event_type = action_state.event_type

        path = table.get_path_from_field(self.result_field)
        result_field = self.result_field.split(".")[-1]

        new_obj = object

        for relation in path:
            new_obj = getattr(new_obj, relation)
            assert new_obj is not None

        new_table = new_obj._table

        if event_type == "delete":
            diff = -1
        elif event_type == "new":
            diff = 1
        else:
            return

        setattr(new_obj, result_field,
                new_table.sa_table.c[result_field] + diff)

        action_state.session.add_no_validate(new_obj)

class MaxDate(Action):

    def __init__(self, target, field, base_level = None, initial_event = False, **kw):

        super(MaxDate, self).__init__(target, field, base_level, initial_event, **kw)

        self.end = kw.get("end", "end_date") 
        self.default_end = kw.get("default_end", datetime.datetime(2199,12,31))

    def update_after(self, object, result, session):

        join = self.get_parent_primary_keys(object)
        end_date_field = object._table.sa_table.c[self.end]
        setattr(result, self.field_name,
                select([func.max(func.coalesce(end_date_field, self.default_end))],
                       and_(*join))
               )
        session.add_no_validate(result)

class AddCommunication(Action):

    def run(self, action_state):

        object = action_state.object
        table = object._table
        database = table.database
        session = action_state.session
        event_type = action_state.event_type

        communication = object._rel_communication

        if not object._core_id:
            raise ValueError("communication has not got a core_id")

        if not communication:
            communication = database.get_instance("communication")
            communication.communication_type = table.name
            object._rel_communication = communication
            core = session.query(database["_core"]).get(object._core_id)
            communication._rel__core = core
        elif event_type == 'delete':
            session.delete(communication)
            return

        if hasattr(object, "defaulted") and object.defaulted:
            communication.defaulted_date = datetime.datetime.now()

        session.add(communication)
        session.add(object)
        session.add(core)


class Counter(Action):

    def __init__(self, target, field, base_level = None, initial_event = False, **kw):

        super(Counter, self).__init__(target, field, base_level, initial_event, **kw)

    def update_after(self, object, result, session):

        relation_attr = self.target_to_base_path[0]

        join_tuples = self.get_join_tuples(relation_attr, object._table, self.base_level)

        target_table = self.database.tables[self.target_table].sa_table.alias()

        join_keys = [key[0] for key in join_tuples]

        key_values = [target_table.c[key] == getattr(object, key) for key in join_keys]

        setattr(object, self.field_name,
                select([select([func.max(func.coalesce(target_table.c[self.field_name], 0)) + 1],
                       and_(*key_values)).alias()])
               )

        session.add_no_validate(object)

    def add(self, result, base_table_obj, object, session):

        session.add_after_flush(self.update_after, (object, result, session))

    def delete(self, result, base_table_obj, object, session):

        session.add_after_flush(self.update_after, (object, result, session))
            
    def update(self, result, base_table_obj, object, session):

        session.add_after_flush(self.update_after, (object, result, session))


class CopyValue(Action):


    def __init__(self, src_field, dest_field, **kw):

        self.dest_field = dest_field
        self.src_field = src_field

    def run(self, action_state):

        object = action_state.object
        table = object._table
        database = table.database

        path = table.get_path_from_field(self.dest_field)
        dest_field = self.dest_field.split(".")[-1]

        new_obj = object

        for relation in path:
            new_obj = getattr(new_obj, relation)
            assert new_obj is not None

        value = getattr(object, self.src_field)

        setattr(new_obj, dest_field, value)
        action_state.session.add_no_validate(new_obj)
 

class CopyTextAfter(Action):

    ##TODO rename class and update_initial method

    def __init__(self, result_field, fields, **kw):

        self.result_field = result_field

        #self.changed_flag = kw.get("changed_flag", None)
        #self.update_when_flag = kw.get("update_when_flag" , None)

        self.field_list = [s.strip() for s in fields.split(",")]

    def run(self, action_state):

        object = action_state.object
        table = object._table
        database = table.database

        path = table.get_path_from_field(self.result_field)
        result_field = self.result_field.split(".")[-1]

        new_obj = object

        for relation in path:
            new_obj = getattr(new_obj, relation)
            assert new_obj is not None
        
        values = [getattr(object, field) for field in self.field_list]

        value = u' '.join([val for val in values if val])

        ## Truncate value if too long for field
        length = new_obj._table.fields[result_field].length
        if value:
            value = value[:length]

        setattr(new_obj, result_field, value)
        action_state.session.add_no_validate(new_obj)

class CopyTextAfterField(CopyTextAfter):

    ## rename class and update_initial method

    def run(self, action_state):

        object = action_state.object
        table = object._table
        database = table.database

        path = table.get_path_from_field(self.result_field)
        result_field = self.result_field.split(".")[-1]

        new_obj = object

        for relation in path:
            new_obj = getattr(new_obj, relation)
            assert new_obj is not None
        
        values = [getattr(object, field) for field in self.field_list]

        values = [u"%s: %s" % (field, getattr(object, field)) for field in self.field_list]

        value = u' -- '.join([val for val in values if val])

        ## Truncate value if too long for field
        length = new_obj._table.fields[result_field].length
        if value:
            value = value[:length]

        setattr(new_obj, result_field, value)
        action_state.session.add_no_validate(new_obj)


class UpdateCommunicationInfo(Action):

    post_flush = True

    def __init__(self, fields, display_name = None,
                 name = None, separator = '\n'):

        self.fields = fields
        self.display_name = display_name
        self.seperator = separator
        self.name = name

    def make_text(self, object):

        values = []

        for field in self.fields:
            value = getattr(object, field)
            if value:
                values.append(value)

        return self.seperator.join(values)

    def set_names(self, table):

        if not self.display_name:
            self.display_name = table.name
        if not self.name:
            if len(self.fields) == 1:
                self.name = self.fields[0]
            else:
                self.name = table.name

    def run(self, action_state):

        object = action_state.object
        table = object._table
        database = table.database
        session = action_state.session
        event_type = action_state.event_type

        self.set_names(table)

        communication = object._rel_communication
        core = communication._rel__core
        core_id = core.id

        result = database.search(
            table.name,
            "communication._core_id = ? and communication.defaulted_date is ?"
            " and communication.active = ?",
            session = session,
            values = [core_id, 'not null', 'true'],
            order_by = 'communication.defaulted_date desc',
            first = True
        )

        default_obj = result.results[0]

        try:
            result = database.search_single(
                "summary_info",
                "_core_id = ? and table_name = ? and name = ?",
                session = session,
                values = [core_id, table.name, self.name]
            )
            info_obj = result.results[0]
        except custom_exceptions.SingleResultError:
            info_obj = None

        if not info_obj:
            if not default_obj:
                return
            info_obj = database.get_instance("summary_info")
            info_obj.table_name = table.name
            info_obj.name = self.name
            info_obj.display_name = self.display_name
            info_obj._rel__core = core
        elif not default_obj:
            session.delete(info_obj)
            return

        text = self.make_text(default_obj)
        info_obj.original_id = default_obj.id
        info_obj.value = text
        session.save(info_obj)
        session.save(core)
