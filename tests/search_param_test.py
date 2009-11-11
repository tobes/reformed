from reformed.search import  QueryFromStringParam, Search
from donkey_test import test_donkey
import datetime


class TestParserParams(test_donkey):

    def test_parser_params(self):

        ast = QueryFromStringParam(None, "name = {poo}", test = True).ast

        assert ast[0].params == ["poo"]

        ast = QueryFromStringParam(None, "name = {}", test = True).ast

        assert ast[0].params == ["name"]

        ast = QueryFromStringParam(None, "donkey.name = {}", test = True).ast

        assert ast[0].params == ["donkey.name"]

        ast = QueryFromStringParam(None, "donkey.name = ?", test = True).ast

        assert ast[0].params == ["?"]

        ast = QueryFromStringParam(None, "name between {poo} and {moo}", test = True).ast

        assert ast[0].params == ["poo", "moo"]
        
        ast = QueryFromStringParam(None, "name between ? and {moo}", test = True).ast

        assert ast[0].params == ["?", "moo"]

        ast = QueryFromStringParam(None, "name in  ({moo}, ?, {poo})", test = True).ast

        assert ast[0].params == ["moo", "?", "poo"]

        ast = QueryFromStringParam(None, "donkey.name = ? and name in ({moo}, ?, {poo})", test = True).ast

        assert ast[0][0].params == ["?"]

        assert ast[0][2].pos == 20 

        query = QueryFromStringParam(None, "donkey.name = ? and name in ({moo}, ?, {poo})",
                                   pos_args = ["pop", "pooop"],
                                   named_args = {"moo": "cow", "poo": "man"})


        assert len(query.expressions) == 2
        assert query.expressions[0].pos == 0 
        assert query.expressions[1].pos == 20


        assert query.expressions[0].param_values == ["pop"]
        assert query.expressions[1].param_values == ['cow', 'pooop', 'man']

        query = QueryFromStringParam(None, 
                                   "(donkey.name between {} and ?)"
                                   "or (email.email <= {} "
                                   "and name in ({moo}, ?, {poo}))"
                                   "and donkey_sponsership.id is ?",
                                   pos_args = ["pop", "pooop", "not null"],
                                   named_args =  {"donkey.name": "yes",
                                                  "email.email": "got",
                                                  "moo": "cow",
                                                  "poo": "man"} 
                                    )


        assert query.expressions[0].param_values == ["yes", "pop"]
        assert query.expressions[1].param_values == ["got"]
        assert query.expressions[2].param_values == ["cow", "pooop", "man"]
        assert query.expressions[3].param_values == ["not null"]

        expression = query.expressions[0].make_sa_expression(self.Donkey, "people")
        expression = query.expressions[3].make_sa_expression(self.Donkey, "people")

        assert query.expressions[0].parsed_values == [u'yes', u'pop']
        assert query.expressions[3].parsed_values == [False]


        query = QueryFromStringParam(None, 
                                   "(donkey.name between {} and ?)"
                                   "or (email.email <= {} "
                                   "and name in ({moo}, ?, {poo}))"
                                   "and donkey_sponsership.id is ?",
                                   pos_args = ["pop", "pooop", "not null"],
                                   named_args =  {"donkey.name": "yes",
                                                  "email.email": "got",
                                                  "moo": "cow",
                                                  "poo": "man"} 
                                    )


        assert query.expressions[0].param_values == ["yes", "pop"]
        assert query.expressions[1].param_values == ["got"]
        assert query.expressions[2].param_values == ["cow", "pooop", "man"]
        assert query.expressions[3].param_values == ["not null"]

        expression = query.expressions[0].make_sa_expression(self.Donkey, "people")
        expression = query.expressions[3].make_sa_expression(self.Donkey, "people")

        assert query.expressions[0].parsed_values == [u'yes', u'pop']
        assert query.expressions[3].parsed_values == [False]

        query = QueryFromStringParam(None, 
                                   "(donkey.modified_date between {} and ?)"
                                   "or (email.active_email = {}"
                                   "and name in ({moo}, ?, {poo}))"
                                   "and donkey_sponsership.id is ?",
                                   pos_args = ["2009-01-01", "pooop", "not null"],
                                   named_args =  {"donkey.modified_date": "2019-01-01",
                                                  "email.active_email": "True",
                                                  "moo": "cow",
                                                  "poo": "man"} 
                                    )
        expression = query.expressions[0].make_sa_expression(self.Donkey, "people")

        assert query.expressions[0].parsed_values == [datetime.datetime(2019, 1, 1),
                                                      datetime.datetime(2009, 1, 1)] 

        expression = query.expressions[1].make_sa_expression(self.Donkey, "people")

        assert query.expressions[1].parsed_values == [True] 

    def test_where(self):

        s = Search(self.Donkey, "people", self.session)

        query = QueryFromStringParam(s, """ name = ? or email.email = {} """, pos_args = ["david"], named_args = {"email.email": "poo@poo.com"})

        where = query.convert_where(query.ast[0])

        assert str(where.compile()) == "people.name = ? AND people.id IS NOT NULL OR email.email = ? AND email.id IS NOT NULL"
        assert where.compile().params == {u'email_1': 'poo@poo.com', u'name_1': 'david'}


        query = QueryFromStringParam(s, """ name = ? or not (email.email < {} and donkey.name = ?)  """, pos_args = ["david", "fred"], named_args = {"email.email" : "poo@poo.com"})
        where = query.convert_where(query.ast[0])
        assert str(where.compile()) == "people.name = ? AND people.id IS NOT NULL OR NOT ((email.email < ? OR email.id IS NULL) AND donkey.name = ? AND donkey.id IS NOT NULL)"
        assert where.compile().params == {u'name_2': 'fred', u'email_1': 'poo@poo.com', u'name_1': 'david'}


        assert query.covering_ors == set(["email","donkey"])
        assert query.inner_joins == set(["email"])
        assert query.outer_joins == set(["donkey"])



