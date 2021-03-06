import donkey_test
from database.data_loader import *
from nose.tools import assert_raises,raises
from custom_exceptions import *
import formencode as fe
import yaml

class test_record_loader(donkey_test.test_donkey):

    @classmethod
    def set_up_inserts(cls):

        super(cls, test_record_loader).set_up_inserts()

        david ="""
        id : 1
        address_line_1 : 16 blooey
        postcode : sewjfd
        email :
            -
                email : poo@poo.com
            -
                email : poo2@poo.com
        donkey_sponsership:
            id : 1
            amount : 10
            _donkey :
                name : fred
                age : 10
        """

        david = yaml.load(david)

        peter ="""
        name : peter
        address_line_1 : 16 blooey
        postcode : sewjfd
        email :
            -
                email : poo@poo.com
            -
                email : poo2@poo.com
        donkey_sponsership:
            amount : 10
            _donkey :
                name : fred
                age : 10
        """

        peter = yaml.load(peter)



        cls.session = cls.Donkey.Session()

        cls.existing_record = SingleRecord(cls.Donkey, "people", david)
        cls.new_record = SingleRecord(cls.Donkey, "people", peter)

        cls.new_record.get_all_obj(cls.session)
        cls.existing_record.get_all_obj(cls.session)

        #cls.new_record.load()


    def test_single_record_process(self):

        assert ("donkey_sponsership", 0, "_donkey", 0) in self.new_record.all_rows.keys()
        assert self.new_record.all_rows[("donkey_sponsership", 0, "_donkey", 0)] == dict(name = "fred", age =10)
        assert self.new_record.all_rows[("email" , 1)] == dict(email = "poo2@poo.com")

    def test_get_key_data(self):

        assert get_key_data(("donkey_sponsership", 0, "_donkey", 0), self.Donkey , "people").node == "donkey"
        assert get_key_data(("donkey_sponsership", 0, "_donkey", 0), self.Donkey , "people").join == "manytoone"

        assert_raises(InvalidKey, get_key_data,
                     ("donkey_sponsership", 0, "donkey", 0), self.Donkey , "people")

    def test_get_parent_key(self):

        assert_raises(InvalidKey,
                      get_parent_key,
                      ("donkey_sponsership", 1, "donkey", 5),
                      self.new_record.all_rows)

        assert get_parent_key(("donkey_sponsership", 0, "donkey", 0),
                                             self.new_record.all_rows) == ("donkey_sponsership", 0)

        assert get_parent_key(("donkey", 0),
                                             self.new_record.all_rows) == "root"

    def test_check_correct_fields(self):

        assert_raises(InvalidField, check_correct_fields, {"name":  "peter", "name2": "bob"}, self.Donkey, "people")

        assert check_correct_fields( {"name":  "peter", "postcode" : "bob"}, self.Donkey, "people") is None

        assert check_correct_fields( {"name":  "peter", "__options" : "bob"}, self.Donkey, "people") is None

        assert check_correct_fields( {"name":  "peter", "id" : "bob"}, self.Donkey, "people") is None

    def test_get_root_obj(self):

        assert self.new_record.all_obj["root"].id is None

        assert self.existing_record.all_obj["root"].name == u"david"

    def test_get_obj_with_id(self):

        obj = self.existing_record.get_obj_with_id( ("donkey_sponsership", 0) , dict(id = 1, amount = 20))

        assert obj.amount == 50   #originally 50

        assert_raises(InvalidData, self.existing_record.get_obj_with_id, ("donkey_sponsership", 0) , dict(id = 2, amount = 20))

        assert_raises(InvalidData, self.existing_record.get_obj_with_id, ("email", 0) , dict(id = 1))

    def test_get_obj_existing_one_to_many(self):

        assert self.existing_record.all_obj[("donkey_sponsership" , 0)].amount == 50

    def test_get_obj_new_one_to_many(self):

        assert self.existing_record.all_obj[("email" , 0)].email is None

    def test_get_obj_new_many_to_one(self):

        assert self.new_record.all_obj[("donkey_sponsership" , 0, "_donkey", 0)].age is None

    def test_get_obj_existing_many_to_one(self):

        assert self.existing_record.all_obj[("donkey_sponsership" , 0, "_donkey", 0)].age == 13


    def test_key_parser(self):

        assert string_key_parser("poo") == ["poo"]
        assert string_key_parser("poo__24__weeee__2__plop") == ["poo", 24, "weeee", 2, "plop"]
        assert string_key_parser("___field__0__field_name") == ["___field", 0, "field_name"]

    def test_get_keys_and_items_from_list(self):

        assert get_keys_and_items_from_list(["poo__24__weeee__2__plop", "poo", "___field__0__field_name"]) ==\
                [[("poo", 24, "weeee", 2), "plop"],["root","poo"],[("___field", 0),"field_name"]]

    def test_get_keys_from_list(self):

        assert get_keys_from_list([[["poo", 24, "weeee", 2], "plop"],["root","poo"],[["___field", 0],"field_name"]])==\
                {"root":{}, ("poo", 24, "weeee", 2):{}, ("___field", 0):{}}


    def test_invalid(self):

        peter_invalid ="""
        name : peter
        email :
            -
                email : poopoo.com
            -
                email : poo2@poo.com
        donkey_sponsership:
            amount : a
            _donkey :
                name : fred
                age : 90
        """

        peter_invalid = yaml.load(peter_invalid)

        invalid_record = SingleRecord(self.Donkey, "people", peter_invalid)

        assert_raises(fe.Invalid, invalid_record.load)

        try:
            invalid_record.load()
        except fe.Invalid, e:
            assert str(e) == """invalid object(s) are {'root': 'address_line_1: Please enter a value, postcode: Please enter a value', ('donkey_sponsership', 0): 'amount: Please enter a number', ('email', 0): 'email: An email address must contain a single @'}"""



    def test_z_add_values_to_obj(self):

        self.existing_record.add_all_values_to_obj()
        self.new_record.add_all_values_to_obj()

        assert self.existing_record.all_obj[u"root"].address_line_1 == u"16 blooey"
        assert self.existing_record.all_obj[(u"donkey_sponsership" , 0)].amount == 10
        assert self.existing_record.all_obj[(u"email" , 0)].email == "poo@poo.com"

        assert self.new_record.all_obj[(u"root")].name == "peter"
        assert self.new_record.all_obj[(u"email" , 0)].email == "poo@poo.com"
        assert self.new_record.all_obj[(u"donkey_sponsership", 0,)].amount == 10
        assert self.new_record.all_obj[(u"donkey_sponsership", 0, "_donkey", 0)].age == 10


    def test_zz_load_record(self):

        self.new_record.load()

        people = self.session.query(self.Donkey.get_class(u"people")).all()
        email = self.session.query(self.Donkey.get_class(u"email")).all()
        donkey = self.session.query(self.Donkey.get_class(u"donkey")).all()
        donkey_spon = self.session.query(self.Donkey.get_class(u"donkey_sponsership")).all()


        assert (u"peter", u"sewjfd") in [( a.name, a.postcode) for a in
                                         people]
        assert (u"fred", 10 ) in [( a.name, a.age) for a in
                                         donkey]
        assert u"poo@poo.com" in [ a.email for a in
                                         email]
        assert  10  in [ a.amount for a in
                                         donkey_spon]


class test_flat_file(donkey_test.test_donkey):

    @classmethod
    def set_up_inserts(cls):

        super(cls, test_flat_file).set_up_inserts()

        cls.flatfile = FlatFile(cls.Donkey,
                            "people",
                            "tests/new_people.csv",
                            ["id",
                            "name",
                            "address_line_1",
                            "postcode",
                            "email__0__email",
                            "email__1__email",
                            "donkey_sponsership__0__amount",
                            "donkey_sponsership__0__id",
                            "donkey_sponsership__0___donkey__0__name"]
                            )



    def test_parent_key(self):

        assert self.flatfile.make_parent_key_dict() == {('donkey_sponsership', 0, '_donkey', 0): ('donkey_sponsership', 0),
                                                   ('email', 1): 'root',
                                                   ('email', 0): 'root',
                                                   ('donkey_sponsership', 0): 'root'}

        assert_raises(custom_exceptions.InvalidKey, FlatFile, self.Donkey,
                                            "people",
                                            None,
                                            ["id",
                                            "name",
                                            "address_line_1",
                                            "postcode",
                                            "email__0__email",
                                            "email__1__email",
                                            "donkey_sponsership__0__amount",
                                            "donkey_sponsership__0__id",
                                            "donkey_sponsership__1___donkey__0__name"]
                                            )

    def test_get_key_info(self):

        print self.flatfile.key_data.keys()

        assert self.flatfile.key_data.keys() == [('donkey_sponsership', 0, '_donkey', 0), ('email', 1), ('email', 0), ('donkey_sponsership', 0)]



        assert_raises(custom_exceptions.InvalidKey, FlatFile, self.Donkey,
                            "people",
                            None,
                            ["id",
                            "name",
                            "address_line_1",
                            "postcode",
                            "email__0__email",
                            "email__1__email",
                            "donkey_sponsership__0__amount",
                            "donkey_sponsership__0__id",
                            "donkey_sponsership__0___donkeyy__0__name"]
                            )

    def test_key_item_dict(self):

        assert self.flatfile.key_item_dict == {('donkey_sponsership', 0, '_donkey', 0): {'name': None},
                                               ('email', 1): {'email': None},
                                               'root': {'address_line_1': None, 'postcode': None, 'id': None, 'name': None},
                                               ('donkey_sponsership', 0): {'amount': None, 'id': None},
                                               ('email', 0): {'email': None}}

    def test_check_fields(self):

        assert self.flatfile.check_fields() == None

        assert_raises(custom_exceptions.InvalidField, FlatFile, self.Donkey,
                            "people",
                            None,
                            ["id",
                            "name",
                            "address_line_1",
                            "postcode",
                            "email__0__email",
                            "email__1__email",
                            "donkey_sponsership__0__amount",
                            "donkey_sponsership__0__id",
                            "donkey_sponsership__0___donkey__0__namee"]
                            )

    def test_get_descendants(self):

        assert self.flatfile.key_decendants == {('donkey_sponsership', 0, '_donkey', 0): [],
                                                ('email', 1): [],
                                                'root': [('donkey_sponsership', 0, '_donkey', 0), ('email', 1), ('donkey_sponsership', 0), ('email', 0)],
                                                ('email', 0): [],
                                                ('donkey_sponsership', 0): [('donkey_sponsership', 0, '_donkey', 0)]}

    def test_create_all_rows(self):

        assert self.flatfile.create_all_rows(["", "peter", "16 blooey", "sewjfd", "poo@poo.com", "poo2@poo.com", 10, None, "fred"]) ==\
                {('donkey_sponsership', 0, '_donkey', 0): {'name': 'fred'},
                 ('email', 1): {'email': 'poo2@poo.com'},
                 'root': {'postcode': 'sewjfd', 'name': 'peter', 'address_line_1': '16 blooey'},
                 ('email', 0): {'email': 'poo@poo.com'},
                 ('donkey_sponsership', 0): {'amount': 10}}

        assert self.flatfile.create_all_rows(["", "peter", "16 blooey", "sewjfd", "poo@poo.com", "poo2@poo.com", None, None, None]) ==\
                {('email', 1): {'email': 'poo2@poo.com'},
                 'root': {'postcode': 'sewjfd', 'name': 'peter', 'address_line_1': '16 blooey'},
                 ('email', 0): {'email': 'poo@poo.com'}}

        assert self.flatfile.create_all_rows(["", "peter", "16 blooey", "sewjfd", "poo@poo.com", "poo2@poo.com", None, None, "fred"]) ==\
                {('donkey_sponsership', 0, '_donkey', 0): {'name': 'fred'},
                 ('email', 1): {'email': 'poo2@poo.com'},
                 'root': {'postcode': 'sewjfd', 'name': 'peter', 'address_line_1': '16 blooey'},
                 ('email', 0): {'email': 'poo@poo.com'},
                 ('donkey_sponsership', 0): {}}

    def test_data_load(self):

        self.flatfile.load()

        result = self.session.query(self.Donkey.get_class("people")).filter_by(name = u"popp102").one()

        assert 102 in [a.amount for a in result.donkey_sponsership]

    def test_data_load_with_header(self):

        flatfile = FlatFile(self.Donkey,
                            "people",
                            "tests/new_people_with_header.csv")

        print flatfile.count_lines()
        assert flatfile.count_lines() == 28
        flatfile.load()


        result = self.session.query(self.Donkey.get_class("people")).filter_by(name = u"popph15").one()

        assert 1500 in [a.amount for a in result.donkey_sponsership]

    def test_data_load_with_header_error(self):

        flatfile = FlatFile(self.Donkey,
                            "people",
                            "tests/new_people_with_header_errors.csv")


        flatfile.load()
        print flatfile.status[0].error_count
        assert flatfile.status[0].error_count == 5


    def test_make_chunks(self):

        flatfile = FlatFile(self.Donkey,
                            "people",
                            "tests/data.csv")

        assert flatfile.make_chunks(250) == [[0, 250], [250, 500], [500, 750], [750, 1000], [1000, 1250], [1250, 1500], [1500, 1750], [1750, 2000], [2000, 2250], [2250, 2500], [2500, 2750], [2750, 3000], [3000, 3250], [3250, 3500], [3500, 3750], [3750, 4000], [4000, 4250], [4250, 4500], [4500, 4750], [4750, 5000]]

        flatfile.total_lines = 450

        assert flatfile.make_chunks(250) == [[0, 250], [250, 450]]

    def test_load_chunk(self):

        session = self.Donkey.Session()

        count_before = session.query(self.Donkey.aliases["people"]).count()

        flatfile = FlatFile(self.Donkey,
                            "people",
                            "tests/data.csv")

        chunk_status = flatfile.load_chunk([0,250])

        count_after = session.query(self.Donkey.aliases["people"]).count()

        assert count_before + 250 == count_after

        assert chunk_status.status == "committed"

        chunk_status = flatfile.load_chunk([250,500])


        assert chunk_status.error_count == 2
#        assert repr(chunk_status.error_lines) == """[line_number: 301, errors: {('email', 0): Invalid('email: The domain portion of the email address is invalid (the portion after the @: .com)',)}, line_number: 428, errors: {('email', 0): Invalid('email: The domain portion of the email address is invalid (the portion after the @: .org)',)}]"""

        print chunk_status.error_lines[0].error_dict
        assert str(chunk_status.error_lines[0].error_dict) == """{('email', 0, 'email'): [Invalid(u'The domain portion of the email address is invalid (the portion after the @: .com)',)]}"""




