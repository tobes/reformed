class ObjectWrapper(object):

    def __init__(self, obj, _session, workflow = None):

        self._obj = obj
        self._workflow= workflow
        self._table = obj._table
        self._session = _session
        self._database = self._table.database
        self._make_other_objs()
        

    def __getattr__(self, name):
        
        if name.startswith("_"):
            return getattr(self,name)
        if self._workflow is None:
            return getattr(self._obj, name)
        if self._workflow == "onetoone":
            return self.get_onetoone(name)
        return getattr(self,name)

    def __setattr__(self, name, value):

        if name.startswith("_"):
            self.__dict__[name]= value
        elif self._workflow is None:
            setattr(self._obj, name, value)
        elif self._workflow == "onetoone":
            self.set_onetoone(name, value)
        else:
            self.__dict__[name]= value

    def _make_other_objs(self):

        self._other_objs = []
        for t,v in self._table.tables_with_relations.items():
            if v.type == "onetoone":
                self._other_objs.append(self._database.tables[t].sa_class())

    def get_onetoone(self,name):

        if hasattr(self._obj,name):
            return getattr(self._obj,name)
        for obj in self._other_objs:
            if hasattr(obj, name):
                return getattr(obj, name)

    def set_onetoone(self, name, value):

        if hasattr(self._obj,name):
            setattr(self._obj, name, value)
        for obj in self._other_objs:
            if hasattr(obj, name):
                setattr(obj, name, value)

    def save(self):
        
        self._session.add(self._obj)
        if self._other_objs:
            for obj in self._other_objs:
                self._session.add(obj)