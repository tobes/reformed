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
##   Copyright (c) 2008-2010 Toby Dacre & David Raznick
##

from formencode import validators
from formencode.validators import UnicodeString

import database.search
from node.node import TableNode, Node
from node.form import form
from node.page_item import *
import node.authenticate as authenticate
from database.saveset import SaveItem
from web.global_session import global_session

r = global_session.database

def initialise():
    predefine = global_session.application.predefine
    # permission
    predefine.permission("Login", u'User login', u'Login to system.')
    predefine.permission("UserAdmin", u'User Administration', u'Administer user accounts.', 2)
    # user group
    predefine.user_group(u'UserAdmins', u'User Administrators', u'Administer user accounts', permissions = ['UserAdmin', 'Login'])
    predefine.user_group(u'Users', u'User', u'General user accounts', permissions = ['Login'])



class User(TableNode):


    main = form(
        layout('column_start'),
        input('name'),
        input('login_name', label = 'login name:', validation = UnicodeString),
        checkbox('active'),
        input('email'),
        layout('column_next'),
        layout('box_start'),
        password('password', validation = UnicodeString),
        password('password2', validation = UnicodeString),
        layout('box_end'),
        layout('column_end'),
        layout('hr'),
        textarea('notes', css = "large"),
        layout('spacer'),
        layout('box_start'),
        codegroup('user_groups', code_table = 'user_group', code_desc_field = 'description', label = 'User Groups', filter = 'access_level = 0'),
        codegroup('restricted_user_group', code_table = 'user_group', code_desc_field = 'description', label = 'Restricted User Groups', filter = 'access_level > 0', permissions = ['SysAdmin']),
        layout('box_end'),
        layout('spacer'),

        table = "user",
        form_type = 'input',
        title_field = 'name'
    )

    user = form(
        layout('column_start'),
        input('name'),
        input('login_name', label = 'login name:'),
        checkbox('active'),
        input('email'),
        layout('column_next'),

        layout('column_end'),
        layout('hr'),
        textarea('notes', css = "large"),
        layout('spacer'),
        layout('box_start'),
        codegroup('user_groups', code_table = 'user_group', code_desc_field = 'description', label = 'User Groups', filter = 'access_level = 0'),
        codegroup('restricted_user_group', code_table = 'user_group', code_desc_field = 'description', label = 'Restricted User Groups', filter = 'access_level > 0', permissions = ['SysAdmin']),
        layout('box_end'),
        layout('spacer'),

        table = "user",
        params =  {"form_type": "input"},
        title_field = 'name'
    )
    change_my_password = form(
        layout('box_start'),
        password('oldpassword', validation = UnicodeString),
        password('newpassword', validation = UnicodeString),
        password('newpassword2', validation = UnicodeString),
        buttons('about_me',
               [['Save Changes', 'user.User:_save_password_change'],
               ['cancel', 'BACK']]),
        layout('box_end'),
        params = {"form_type": "action"}
    )

    change_other_password_form = form(
        layout('box_start'),
        password('newpassword', validation = UnicodeString),
        password('newpassword2', validation = UnicodeString),
        layout('box_end'),
        params = {"form_type": "action"}
    )

    login_form = form(
        layout('box_start'),
        input('login_name', label = 'username:', validation = UnicodeString),
        password('password', validation = UnicodeString),
        checkbox('remember_me', label = 'remember me'),
        button('f@user.User:login', label = 'Log in'),
        layout('box_end'),

        form_type = "action",
        layout_title = "Login",
        params = {"form_type": "action"}
    )

    about_me_form = form(
        layout('box_start'),
        input('login_name', label = 'username:', validation = UnicodeString),
        textarea('about_me', css = "large"),
        layout('box_end'),

        buttons('about_me',
               [['Save Changes', 'user.User:_save_about_me'],
               ['cancel', 'BACK']]),

        message('about_me', 'About Me'),

        table = "user",
        params = {"form_type": "action"}
    )

    listing = form(
        result_link('title'),
        info('summary', data_type = 'info'),
        result_link_list([['Edit', 'user.User:edit'],
                            ['Delete', 'user.User:_delete'],
                            ['Change Password', 'd@user.User:change_other_password'],
                            ['Impersonate', '@user.Impersonate:_impersonate']]),
        form_type = "results",
        layout_title = "results",
    )

    table = "user"

    def setup_extra_commands(self):
        commands = {}
        commands['login'] = dict(command = 'check_login')
        commands['logout'] = dict(command = 'logout')
        commands['list'] = dict(command = 'list')
        commands['_save'] = dict(command = 'save')
        commands['new'] = dict(command = 'new')
        commands['edit'] = dict(command = 'edit')
        commands['view'] = dict(command = 'view')
        commands['about_me'] = dict(command = 'about_me', permissions = ['LoggedIn'])
        commands['_save_about_me'] = dict(command = 'save_about_me', permissions = ['LoggedIn'])
        commands['change_password'] = dict(command = 'change_password', permissions = ['LoggedIn'])
        commands['_save_change_password'] = dict(command = 'save_change_password', permissions = ['LoggedIn'])
        commands['change_other_password'] = dict(command = 'change_other_password', permissions = ['UserAdmin'])
        commands['_save_change_other_password'] = dict(command = 'save_change_other_password', permissions = ['UserAdmin'])
        self.__class__.commands = commands



    def edit(self, node_token):
        print 'User'
        self["user"].view(node_token, read_only = False)

    def view(self, node_token, read_only=True):
        self.layout_main_form = 'user'
        self["user"].view(node_token, read_only = read_only)

    def new(self, node_token):
        self["main"].new(node_token)


    def check_login(self, node_token):
        message = node_token['login'].pop('message')
        fail_message = '# Login failed\n\nuser name or password incorrect, try again.'
        vdata = node_token['login_form']


        if not node_token.get_validation_errors() and vdata.get('login_name') and vdata.get('password'):
            (message, data) = authenticate.check_login(vdata['login_name'], vdata['password'])
            # if data is returned then the login was a success
            if data:
                self.login(node_token, data)
                return
        if not message:
            message = 'Welcome to %s<br /> enter your login details to continue' % global_session.sys_info['name']
        print message
        self.show_login_form(node_token, message)

    def show_login_form(self, node_token, message = None):
        if message:
            data = dict(__message = message)
        else:
            data = {}
        node_token.force_dialog()
        self["login_form"].show(node_token, data)

    def about_me(self, node_token):
        where = 'id = %s' % global_session.session['user_id']
        self["about_me_form"].view(node_token, read_only = False, where = where)

    def save_about_me(self, node_token):
        self["about_me_form"].save(node_token)

    def change_password(self, node_token, message = None):
        if not message:
            message = "Change your password"
        data = dict(__buttons = [['change password', 'f@user.User:_save_change_password'],
                                 ['cancel', 'BACK']],
                    __message = message)

        self["change_my_password"].show(node_token, data)

    def save_change_password(self, node_token):
        #vdata = node_token.data
        #errors = self["change_my_password"].validate(vdata)
        if node_token.errors:
            return
        ##FIXME check for legth or stregth of password
        if vdata.get('newpassword') != vdata.get('newpassword2'):
            # new password not confirmed
            self.change_password(node_token, 'new password does not match')
        else:
            where = 'id=%s' % global_session.session['user_id']
            current_password = r.search_single_data("user", where = where, fields = ['password'])['password']

            if not database.fshp.check(vdata['oldpassword'], current_password):
                # old password incorrect
                self.change_password(node_token, 'old password does not match')
            else:
                # all good update password
                # FIXME actually update the database
                node_token.action = 'html'
                data = "<p>Your password has been updated (this is a lie)</p>"
                node_token.out = {'html': data}


    def change_other_password(self, node_token, message = None):
        __id = node_token[''].get_data_int('__id')
        where = '_core_id=%s' % __id #FIXME insecure
        user = r.search_single_data("user", where = where, fields = ['name'])['name']
        if not message:
            message = "Change password for user %s" % user
        data = dict(__buttons = [['change password', 'f@user.User:_save_change_other_password'],
                                 ['cancel', 'CLOSE']],
                    __message = message,
                    __id = __id)
        node_token.force_dialog()
        self["change_other_password_form"].show(node_token, data)

    def save_change_other_password(self, node_token):
        vdata = node_token['change_other_password_form']
        if node_token.get_validation_errors():
            return
        if vdata.get('newpassword') != vdata.get('newpassword2'):
            # new password not confirmed
            self.change_other_password(node_token, 'new password does not match')
        else:
            core_id = vdata.get_data_int('__id')
            where = '_core_id=%s' % core_id #FIXME insecure
            user = r.search_single_data("user", where = where, fields = ['name'])['name']

            self._set_password(core_id, vdata.get('newpassword'))
            data = "Password for user %s has been updated." % user
            node_token.message(data)



    def _set_password(self, core_id, password):
        session = r.Session()
        result = r.search_single('user', "_core_id = ?",
                              values = [core_id],
                              session = session)
        save_set = SaveItem(result.results[0], session)
        save_set.set_value('password', password)
        errors = save_set.save()




    def login(self, node_token, data):

        user_name = data.get('name')
        user_id = data.get('id')
        auto_login = data.get('auto_login')

        node_token.user = dict(name = user_name, id = user_id)

        # auto login cookie
        if node_token['login_form'].data.get('remember_me') and auto_login:
            node_token.auto_login_cookie = '%s:%s' % (user_id, auto_login)

        node_token.redirect('RELOAD')



    def logout(self, node_token):
        authenticate.clear_user_session()

        node_token.user = dict(name = None, id = 0)
        message = "You are now logged out"
        self.show_login_form(node_token, message)
        # clear bookmarks
        node_token.bookmark = 'CLEAR'

        # auto login cookie
        node_token.auto_login_cookie = 'CLEAR'

    def make_menu(self, node_manager):
        node_manager.add_menu(dict(menu = 'UserAdmin', title = 'List Users', node = '$:list', index = 2))
        node_manager.add_menu(dict(menu = 'UserAdmin', title = 'New User', node = '$:new', flags = 'd', index = 2))

class UserGroup(TableNode):

    register_node = dict(table = 'user_group', title = 'User Group', cat_node = '$:list')
    main = form(
        info('groupname'),
        input('groupname', description = 'The name of the user group'),
        input('name', description = 'The name of the user group'),
        checkbox('active', description = 'Only active user groups give members permissions'),
        input('description', description = 'A brief description of the user group', css = 'large'),
        textarea('notes', css = "large", description = 'A longer more detailed description'),
        layout("spacer"),
        layout("box_start"),
        codegroup("p1", code_table = 'permission', code_desc_field = 'description', label = 'General Permissions', filter = 'access_level = 0'),
        codegroup("p2", code_table = 'permission', code_desc_field = 'description', label = 'Admin Permissions', filter = 'access_level > 0', permissions = ['SysAdmin']),

        table = "user_group",
        form_type = "input",
        title_field = 'name'
    )

    table = "user_group"

    def make_menu(self, node_manager):
        node_manager.add_menu(dict(menu = 'UserAdmin', title = 'List User Groups', node = '$:list', index = 4))
        node_manager.add_menu(dict(menu = 'UserAdmin', title = 'New User Group', node = '$:new', flags = 'd', index = 4))

class UserAdmin(TableNode):

    permissions = ['UserAdmin']

    form_params =  {"form_type": "action"}
    main = form(
        layout('text', text = 'Users {users}'),
        link('d@user.User:new', label = 'add user'),
        link('user.User:list', label = 'list users'),
        layout('spacer'),
        layout('text', text = 'User Groups {user_groups}'),
        link('d@user.UserGroup:new', label = 'add user group'),
        link('user.UserGroup:list', label = 'list user groups'),
        layout('spacer'),
##        layout('text', text = 'Permissions {permissions}'),
##        button_link('bug.Permission:new', label = 'add permission'),
##        button_link('bug.Permission:list', label = 'list permissions'),
##        layout('spacer'),

        form_type = "action",
    )

    def call(self, node_token):
        session = r.Session()
        users = database.search.Search(r, 'user', session).search().count()
        user_groups = database.search.Search(r, 'user_group', session).search().count()
        permissions = database.search.Search(r, 'permission', session).search().count()
        data = {'users' : users, "user_groups" : user_groups , "permissions" : permissions }
#        data['__message'] = "User Admin"
#        data['__buttons'] = [['cancel', 'BACK']]
        self["main"].create_form_data(node_token, data)
        node_token.form(self.name, title = "main")
        node_token.set_layout_title('User Admin')
#        r.set_option('user_group', 'default_node', 'user.UserGroup')
#        r.set_option('user', 'default_node', 'user.User')

      #  node_token.action = 'form'
      #  node_token.title = 'listing'

    def make_menu(self, node_manager):
        node_manager.add_menu(dict(name = 'UserAdmin', menu = 'Admin', title = 'User Admin', node = 'user.UserAdmin', permissions = 'UserAdmin'))
        node_manager.add_menu(dict(name = 'Admin', title = 'Admin', node = None, index = 10))

class Impersonate(Node):

    def call(self, node_token):
        # check we are allowed to do this.
        if not global_session.session['real_user_id']:
            node_token.forbidden()
            return

        if node_token.command == '_impersonate':
            core_id = node_token[''].get_data_int('__id')
            self.impersonate(node_token, core_id = core_id)
        elif node_token.command == 'revert':
            self.impersonate(node_token, id = global_session.session['real_user_id'])

    def impersonate(self, node_token, core_id = None, id = None):

        if authenticate.impersonate(core_id, id):
            # Get the user info to pass to front end.
            user_id = global_session.session['user_id']
            username = global_session.session['username']
            real_user_name = global_session.session['real_username']
            real_user_id = global_session.session['real_user_id']
            node_token.user = dict(name = username,
                                   id = user_id,
                                   real_user_name = real_user_name,
                                   real_user_id = real_user_id)
            node_token.message('you are now logged in as user %s' % username)
        else:
            node_token.forbidden()


