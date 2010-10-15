/*

    This file is part of Reformed.

    Reformed is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License version 2 as
    published by the Free Software Foundation.

    Reformed is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Reformed.  If not, see <http://www.gnu.org/licenses/>.

    -----------------------------------------------------------------

    Reformed
    Copyright (c) 2008-2010 Toby Dacre & David Raznick

*/

// JSLint directives
/*global window setTimeout*/
/*global $ REBASE console_log Showdown*/

var CONFIG = {
    DISABLE_FX : true,
    FORM_PAGING_SIZE : 5,
    FORM_FOCUS_SELECT_ALL : true,
    BOOKMARKS_SHOW_MAX : 100,
    BOOKMARK_ARRAY_MAX : 100,
    DIALOG_BORDER_HEIGHT : 150,
    DIALOG_BORDER_WIDTH : 150,
    // FIXME these numbers are magic
    // should be calculated
    DIALOG_CHROME_HEIGHT : 75,
    DIALOG_CHROME_WIDTH : 35
}

var REBASE = {};


/*
 *           ('>
 *           /))@@@@@.
 *          /@"@@@@@()@
 *         .@@()@@()@@@@    FORM
 *         @@@O@@@@()@@@
 *         @()@@\@@@()@@    Useful and shared form functions.
 *          @()@||@@@@@'
 *           '@@||@@@'
 *        jgs   ||
 *       ^^^^^^^^^^^^^^^^^
 */


REBASE.Form = function (){

    function make_paging(paging_data){
        // build and return a paging bar

        var offset = paging_data.offset;
        var limit = paging_data.limit;
        var count = paging_data.row_count;
        var base = paging_data.base_link;
        var use_href = REBASE.Node.is_update_node(base);

        var html = [];

        function make_item(offset, description, active){

            var link;

            function make_href(link){
                if (use_href){
                    return 'href="#' + link + '" ';
                } else {
                    return 'href="#" ';
                }
            }

            if (active){
                link = base + (offset * limit);
                html.push( '<a ' + make_href(link) + 'onclick="node_load(\'' +
                    link +'\');return false;">' + description + '</a> ');
            } else {
                html.push( description + ' ');
            }
        }

        var pages = Math.ceil(count/limit);
        var current = Math.floor(offset/limit);

        var first_page = current - CONFIG.FORM_PAGING_SIZE;
        if (first_page < 0){
            first_page = 0;
        }
        var last_page = first_page + (CONFIG.FORM_PAGING_SIZE * 2);
        if (last_page > pages){
            last_page = pages;
        }


        base = base + '&l=' + limit + '&o=';

        html.push('<div class="PAGING_BAR">');
        html.push('paging: ');

        var active = (current > 0);
        make_item(0, '|&lt;', active);
        var page_offset = (current - 1);
        make_item(page_offset, '&lt;', active);

        for (var i = first_page; i < last_page; i++){
            make_item(i, i + 1, (i != current));
        }

        active = (current < pages - 1);
        page_offset = (current + 1);
        make_item(page_offset, '&gt;', active);
        make_item(pages - 1, '&gt;|', active);

        html.push('page ' + (current + 1) + ' of ' + pages + ' pages');
        html.push(', ' + count + ' records');
        html.push('</div>');
        return html.join('');
    }

    function make_item_class(item, extra_class){
        // Returns a html ' class=".." ' string for
        // an item containing both css and extra class lists.
        if (!item.css && !extra_class){
            return '';
        }
        var class_list = '';
        if (extra_class){
           class_list = extra_class;
        }
        if (item.css){
            class_list += ' ' + item.css;
        }
        return ' class="' + class_list + '" ';
    }

    function HTML_Encode_Clear(arg) {
        // encode html also show null as ''
        // replace & " < > with html entity
        if (arg === null){
            return '';
        }
        if (typeof arg != 'string'){
            return arg;
        }
        return arg.replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    }


    function process_html(text, data, inline){
        var match;
        var out = text;
        var start;
        var end;
        var substitute_data;
        var format;
        // data substitution
        var offset = 0;
        var reg = /\{([^}:]+):?([^}]*)\}/g;
        if (data){
            // JSLint complains but this is intentional.
            while (match = reg.exec(text)){
                if (data[match[1]] === undefined){
                    continue;
                }
                substitute_data = data[match[1]];
                if (match[2] && substitute_data){
                    substitute_data = $.Util.format_data(substitute_data, match[2]);
                }

                start = match.index + offset;
                end = match.index + match[0].length + offset;
                offset += substitute_data.length - match[0].length;
                out = out.substring(0, start) + substitute_data + out.substring(end);
            }
        }

        var mode = Showdown.MODE_FULL;
        if (inline){
            mode = Showdown.MODE_SIMPLE;
        }
        var converter = new Showdown.converter();
        out = converter.makeHtml(out, mode);

        return out;
    }
    function make_selection(input, start, end){
        // select the text in the input
        // between start and end.
        if (input.setSelectionRange){
            // DOM 3
            input.setSelectionRange(start ,end);
        } else if (input.createTextRange){
            // IE
            var range = input.createTextRange();
            range.moveStart("character", start);
            range.moveEnd("character", end);
            range.select();
        }
    }

    function focus($input){
        // focus the element and
        // if select select all.
        var value = $input.val();
        if (value){
            var length = value.length;
            var start
            if (CONFIG.FORM_FOCUS_SELECT_ALL){
                start = 0;
            } else {
                start = length;
            }
            make_selection($input[0], start, length);
        }
        $input.focus();
    }

    function dropdown_click(item_id){
        $('#' + item_id).trigger('dropdown');
    }
    // exported functions
    return {
        'make_paging' : function (paging_data){
            return make_paging(paging_data);
        },
        'make_item_class' : function (item, extra_class){
            return make_item_class(item, extra_class);
        },
        'HTML_Encode_Clear' : function (arg){
            return HTML_Encode_Clear(arg);
        },
        'process_html' : function (arg){
            return process_html(arg);
        },
        'focus' : function ($input){
            return focus($input);
        },
        'dropdown_click' : function (item_id){
            return dropdown_click(item_id);
        }

    };
}();


/*
 *           ('>
 *           /))@@@@@.
 *          /@"@@@@@()@
 *         .@@()@@()@@@@    BOOKMARK
 *         @@@O@@@@()@@@
 *         @()@@\@@@()@@    Bookmark functions.
 *          @()@||@@@@@'
 *           '@@||@@@'
 *        jgs   ||
 *       ^^^^^^^^^^^^^^^^^
 */


REBASE.Bookmark = function (){

    var bookmark_array = [];

    function bookmark_add(bookmark){
        // create the bookmark view link
        if (bookmark.entity_id === null){
            alert('null bookmark');
        }
        // stop null bookmarks
        if (!bookmark.title){
            bookmark.title = 'untitled';
        }
        var table_data = REBASE.application_data.bookmarks[bookmark.entity_table];
        if (table_data){
            bookmark.bookmark = 'u:' + table_data.node.replace('&', '&amp;') + ':edit:id=' + bookmark.entity_id;
        } else {
            bookmark.bookmark = 'u:test.Auto:edit:id=' + bookmark.entity_id + '&amp;table=' + bookmark.entity_table;
        }
        // remove the item if already in the list
        for (var i = 0, n = bookmark_array.length; i < n; i++){
            if (bookmark_array[i].bookmark == bookmark.bookmark){
                bookmark_array.splice(i, 1);
                break;
            }
        }
        // trim the array if it's too long
        if (bookmark_array.length >= CONFIG.BOOKMARK_ARRAY_MAX){
            bookmark_array.splice(CONFIG.BOOKMARK_ARRAY_MAX - 1, 1);
        }
        bookmark_array.unshift(bookmark);
    }

    function bookmark_display(){
        var categories = [];
        var category_items = {};
        var category;
        var entity_table;
        var html;
        // create an item for each bookmark and put it in
        // the array for its category
        for(var i = 0; i < bookmark_array.length && i < CONFIG.BOOKMARKS_SHOW_MAX; i++){
            entity_table = bookmark_array[i].entity_table;
            if (category_items[entity_table] === undefined){
                categories.push(entity_table);
                category_items[entity_table] = [];
            }
            html  = '<li>';
            html += '<span onclick="node_load(\'' + bookmark_array[i].bookmark + '\')">';
            html += bookmark_array[i].title + '</span>';
            html += '</li>';

            category_items[entity_table].push(html);
        }
        // create the actual bookmarks list
        html = '<ol class = "bookmark">';
        for(i = 0; i < categories.length; i++){
            category = categories[i];
            html += '<li class ="bookmark-title bookmark-category-' + category + '">';
            html += category;
            html += '<ol class ="bookmark-items">';
            html += category_items[category].join('\n');
            html += '</ol>';
            html += '</li>';
        }
        html += '</ol>';
        $('#bookmarks').html(html);
    }

    function bookmark_process(bookmark){
        if ($.isArray(bookmark)){
            // if we get an array of bookmarks
            // clear any existing bookmarks
            // and replace with the new ones
            bookmark_array = [];
            for (var i = 0, n = bookmark.length; i < n; i++){
                bookmark_add(bookmark[i]);
            }
        } else {
            if (bookmark == 'CLEAR'){
                // reset the bookmarks
                bookmark_array = [];
            } else {
                bookmark_add(bookmark);
            }
        }
        bookmark_display();
    }

    return {
        process : function (arg){
            bookmark_process(arg);
        }
    };
}();


/*
 *           ('>
 *           /))@@@@@.
 *          /@"@@@@@()@
 *         .@@()@@()@@@@    USER
 *         @@@O@@@@()@@@
 *         @()@@\@@@()@@    User management functions.
 *          @()@||@@@@@'
 *           '@@||@@@'
 *        jgs   ||
 *       ^^^^^^^^^^^^^^^^^
 */

REBASE.User = function (){

    function change_user_bar(){
        // update the user bar with the correct user info
        // log in/out options etc.
        var app_data = REBASE.application_data;
        var html;
        if (app_data.__user_id === 0){
            html = '<a href="#" onclick="node_load(\'d:user.User:login\',this);return false;">Log in</a>';
        } else {
            var impersonate = '';
            if (app_data.__real_user_id && app_data.__real_user_id != app_data.__user_id){
                impersonate = ' <a href="#" onclick="node_load(\':user.Impersonate:revert\',this);return false;">revert to ' + app_data.__real_username + '</a>';
            }
            html = app_data.__username + ' <a href="#" onclick="node_load(\':user.User:logout\',this);return false;">Log out</a>' + impersonate;
        }
        $('#user_login').html(html);
    }

    function update_user(user_data){
        // if we have new user data then update the application data
        if (user_data){
            var app_data = REBASE.application_data;
            app_data.__user_id = user_data.id;
            app_data.__username = user_data.name;
            if (user_data.real_user_id){
                app_data.__real_user_id = user_data.real_user_id;
            }
            if (user_data.real_user_name){
                app_data.__real_username = user_data.real_user_name;
            }
        }
        change_user_bar();
    }

    return {
        'update' : function (user_data){
            update_user(user_data);
        }
    };
}();


/*
 *           ('>
 *           /))@@@@@.
 *          /@"@@@@@()@
 *         .@@()@@()@@@@    INTERFACE
 *         @@@O@@@@()@@@
 *         @()@@\@@@()@@    Create and manage the user interface.
 *          @()@||@@@@@'
 *           '@@||@@@'
 *        jgs   ||
 *       ^^^^^^^^^^^^^^^^^
 */

REBASE.Interface = function (){

    var $interface_layout;
    var $side;
    var $user_area;
    var $user_bar;
    var $logo;
    var $menu;

    function resize_north_pane(){
        // due to floats we have to measure the user bar items
        var size = $user_bar.outerHeight(true) + $menu.outerHeight(true);
        $interface_layout.sizePane('north', size);
        $logo.height(size - 10);
    }

    function make_menu(menu){
        // Build the menu.
        function build(data){
            var i;
            var item;
            var html = [];
            for(i = 0; i < data.length; i++){
                item = data[i];
                html.push('<li>');
                if (item.node){
                    html.push('<a onclick="node_load(\'' + item.node + '\');$(\'#menu\').hideSuperfishUl();" >');
                } else {
                    if (item['function']) {
                        html.push('<a onclick="REBASE.Functions.call(\'' + item['function'] + '\');$(\'#menu\').hideSuperfishUl();" >');
                    } else {
                        html.push('<a onclick="return false;" >');
                    }
                }
                html.push(item.title);
                html.push('</a>');
                if (item.sub){
                    html.push('<ul>');
                    html.push(build(item.sub));
                    html.push('</ul>');
                }
                html.push('</li>');
            }
            return html.join('');
        }
        $menu.empty();
        $menu.append(build(menu));
        $menu.superfish();
    }

    function add_logo(){
        $logo = $('<img id="logo_image" src="logo.png" />');
        $('#logo').append($logo);
    }

    function add_user_bar(){
        $user_bar = $('<div id="user_bar"></div>');
        // search box
        var html = [];
        html.push('<form action="" onclick="$.Util.Event_Delegator(\'clear\');" onsubmit="return search_box();" style="display:inline">');
        html.push('<input type="text" name="search" id="search" />');
        html.push('<input type="submit" name="search_button" id="search_button" value="search"/>');
        html.push('</form>');
        $user_bar.append(html.join(''));
        // ajax info
        $user_bar.append('<span id="ajax_info"><img src="busy.gif" /> Loading ...</span>');
        // login info
        $user_bar.append('<span id="user_login" style="float:right;">user login</span>');
        $user_area.append($user_bar);
    }

    function add_menu(){
        $menu = $('<ul id="menu" class="sf-menu" ><li><a onclick="return false;" >menu</a></li><ul>');
        $menu.superfish();
        var $menu_bar = $('<div id="menu_bar">');
        $menu_bar.append($menu);
        $user_area.append($menu_bar);
    }

    function make_resizer(){
        var html = [];
        var sizes = [8, 10, 12, 14, 16];
        html.push('<div id="resizer" >');
        for (var i = 0; i < sizes.length; i++){
            html.push('<span onclick="$.Util.selectStyleSheet(\'size\', ' + (i + 1) + ');" >');
            html.push('<span style="font-size:' + sizes[i] + 'px">A</span></span>');
        }
        html.push('</div>');
        return html.join('');
    }

    function add_side(){
        $side.empty();
        $side.append(make_resizer());
        $side.append('<div id="bookmarks"></div>');
    }

    function init(){
        /* initialise the layout */
        var $body = $('body');
        $body.append('<div class="ui-layout-center"><div id="main" /></div>');
        $body.append('<div class="ui-layout-west" id="left"><div id="side" /></div>');
        $body.append('<div class="ui-layout-north"><div id="logo" /><div id="user_area" /></div>');
        $side = $('#side');
        $user_area = $('#user_area');

        add_side();
        add_user_bar();
        add_menu();
        add_logo();

        // set options for the panes
        var layout_defaults = {spacing_open:3, spacing_close:6, padding:0, applyDefaultStyles:true};
        var layout_north = {resizable:true, closable: false, slidable:false, spacing_open:0};

        $interface_layout = $body.layout({defaults: layout_defaults, north : layout_north});
        resize_north_pane();
    }
    return {
        'init' : function (){
            init();
        },
        'resize_north_pane': function (){
            resize_north_pane();
        },
        'make_menu': function (menu_data){
            make_menu(menu_data);
        }
    };
}();


/*
 *           ('>
 *           /))@@@@@.
 *          /@"@@@@@()@
 *         .@@()@@()@@@@    DIALOG BOX
 *         @@@O@@@@()@@@
 *         @()@@\@@@()@@    Pop up dialog box.
 *          @()@||@@@@@'
 *           '@@||@@@'
 *        jgs   ||
 *       ^^^^^^^^^^^^^^^^^
 */

REBASE.Dialog = function (){


    var dialog_decode;
    var $dialog_box;
    var $system_dialog_box;
    var is_setup = false;
    var is_open = false;
    var process_html = REBASE.Form.process_html;

    function setup(){
        var options = {autoOpen: false, width: 'auto', modal: true};
        // dialog box
        $dialog_box = $('<div id="dialog_box"></div>');
        $('body').append($dialog_box);
        // system dialog box
        $system_dialog_box = $('<div id="system_dialog_box"></div>');
        $('body').append($system_dialog_box);

        is_setup = true;
    }

    function show_dialog($dialog, title){
        // Show the dialog.  Unfortunatly the dialog appears to
        // lack some functionality so we have to manually shrink
        // it if it is too big.  We also need to centre it.

        var height = $(window).height() - CONFIG.DIALOG_BORDER_HEIGHT;
        var width = $(window).width() - CONFIG.DIALOG_BORDER_WIDTH;
        // Destroy the dialog and recreate so smaller
        // content is sized correctly.
        $dialog.dialog('destroy');
        var options = {width: 'auto', height: 'auto', modal: true, title: title};
        $dialog.dialog(options);
        var $container = $dialog.parent();
        var c_height = $container.height();
        var c_width = $container.width();
        // Shrink if needed.
        if (c_height > height){
            $container.height(height);
            $dialog.height(height - CONFIG.DIALOG_CHROME_HEIGHT);
            c_height = height;
        }
        if (c_width > width){
            $container.width(width);
            $dialog.width(width - CONFIG.DIALOG_CHROME_WIDTH);
            c_width = width;
        }
        // Centre the dialog on the page.
        $container.css({'top':Math.floor((height - c_height + CONFIG.DIALOG_BORDER_HEIGHT) / 2),
                     'left':Math.floor((width - c_width + CONFIG.DIALOG_BORDER_WIDTH) / 2)});
    }

    function open(title, data, no_processing){
        if (!is_setup){
            setup();
        }
        // If we have sent a string as data then we just want
        // to process it for any markdown and display it.
        // If it is form data then we want to process it as a form.
        if (typeof(data) == 'string'){
            if (!no_processing){
                data = process_html(data);
            }
            $dialog_box.html(data);
        } else {
            // assuming it is form_data
            var form = data.form;
            var form_data = data.data;

            $dialog_box.input_form(form, form_data);
        }
        show_dialog($dialog_box, title);
        // focus first enabled input
        REBASE.Form.focus($dialog_box.find(':input:enabled').first());
        is_open = true;
    }

    function close(){
        if (is_open){
            $dialog_box.dialog('close');
            is_open = false;
        }
    }

    function confirm_action(decode, title, message){
        if (!is_setup){
            setup();
        }
        dialog_decode = decode;
        var $form = $('<div class="INPUT_FORM"></div>');
        // clear any form data
        REBASE.FormControls.set_data({});
        $form.append(REBASE.FormControls.build(true, {control:'message_area'}, message));
        $form.append('<div class="f_control_holder"><div class="f_sub"><button onclick="REBASE.Dialog.confirm_action_return(false);return false" class="button">No</button><button onclick="REBASE.Dialog.confirm_action_return(true);return false" class="button">Yes</button></div></div>');
        $system_dialog_box.empty();
        $system_dialog_box.append($form);

        show_dialog($system_dialog_box, title);
    }

    function confirm_action_return(result){
        $system_dialog_box.dialog('close');
        if (result){
            dialog_decode.flags.confirm_action = false;
            REBASE.Node._get_node(dialog_decode);
        }
    }

    // exported functions
    return {
        'dialog' : function (title, data, no_processing){
            open(title, data, no_processing);
        },
        'close' : function(){
            close();
        },
        'confirm_action' : function (decode, title, message){
            confirm_action(decode, title, message);
        },
        'confirm_action_return' : function(result){
            confirm_action_return(result);
        }
    };
}();


/*
 *           ('>
 *           /))@@@@@.
 *          /@"@@@@@()@
 *         .@@()@@()@@@@    FUNCTIONS
 *         @@@O@@@@()@@@
 *         @()@@\@@@()@@    Remote functions called by the backend.
 *          @()@||@@@@@'
 *           '@@||@@@'
 *        jgs   ||
 *       ^^^^^^^^^^^^^^^^^
 */


REBASE.Functions = function (){

    // hash of functions available
    var functions = {};

    function call(fn, data){
        /* calls function if it exists */
        var f = functions[fn];
        if (f){
            f(data);
        } else {
            REBASE.Dialog.dialog('Error', '<pre>Function `' + fn + '` is not available.</pre>');
            console_log('ERROR: function `' + fn + '` not available');
        }
    }

    function debug_form_info(){
        /* Output the current form cache information */
        var info = REBASE.Layout.debug_form_info();
        $('#main').empty();
        $('#main').append('<p><b>Cached form info</b><div id="treeview_control">		<a title="Collapse the entire tree below" href="#"><img src="jquery/images/minus.gif" /> Collapse All</a> | <a title="Expand the entire tree below" href="#"><img src="jquery/images/plus.gif" /> Expand All</a> | <a title="Toggle the tree below, opening closed branches, closing open branches" href="#">Toggle All</a></div></p>');
        var $treeview = $(REBASE.Utils.treeview_hash(info)).treeview({collapsed: true, control : '#treeview_control'});
        $('#main').append($treeview);
    }

    function debug_html(){
        /* Output the current form cache information */
        var info = $('html').html();
        info = info.replace(/<textarea/g, '<_textarea');
        info = info.replace(/<\/textarea/g, '</_textarea');
        REBASE.Dialog.dialog('HTML', '<textarea class="debug"><html xmlns="http://www.w3.org/1999/xhtml">' + info + '</html></textarea>', true);
    }

    // FUNCTIONS

    functions.debug_form_info = debug_form_info;
    functions.debug_html = debug_html;

    // application data
    functions.application_data = function (data){
        REBASE.application_data = data;
        REBASE.User.update();
    };

    // bookmarks
    functions.load_bookmarks = function (data){
        REBASE.Bookmark.process(data);
    };

    // Clear form cache.
    functions.clear_form_cache = function (){
        REBASE.Layout.clear_form_cache();
    };

    // Make menu.
    functions.make_menu = function (data){
        REBASE.Interface.make_menu(data);
    };

    // exported functions
    return {
        'call' : function (fn, data){
            call(fn, data);
        }
    };
}();


/*
 *           ('>
 *           /))@@@@@.
 *          /@"@@@@@()@
 *         .@@()@@()@@@@    UTILS
 *         @@@O@@@@()@@@
 *         @()@@\@@@()@@    Useful and shared functions.
 *          @()@||@@@@@'
 *           '@@||@@@'
 *        jgs   ||
 *       ^^^^^^^^^^^^^^^^^
 */

REBASE.Utils = function (){


    function treeview_hash(data, css_class){
        /* takes a hash of data and converts it into
         * a jQuery treeview ready unordered list
         */
        if (css_class === undefined){
            css_class = 'treeview-gray';
        }
        var output = [];
        if (css_class !== ''){
            output.push('<ul class="' + css_class + '" >');
        } else {
            output.push('<ul>');
        }
        for (var key in data){
            if (data[key] === null){
                output.push('<li>' + key + ' : null</li>');
            } else if (typeof(data[key]) == 'object'){
                if (data[key].length){
                    output.push('<li><span>' + key + ' : [\n</span>' + treeview_hash(data[key], '') + '<span>\n]</span></li>');
                } else {
                    output.push('<li><span>' + key + ' : {\n</span>' + treeview_hash(data[key], '') + '<span>\n}</span></li>');
                }
            } else {
                output.push('<li>' + key + ' : ' + data[key] + '</li>');
            }
        }
        output.push('</ul>');
        return output.join('\n');
    }

    // exported functions
    return {
        'treeview_hash' : function (data, css_class){
            return treeview_hash(data, css_class);
        }
    };
}();



/*
 *           ('>
 *           /))@@@@@.
 *          /@"@@@@@()@
 *         .@@()@@()@@@@    NODE
 *         @@@O@@@@()@@@
 *         @()@@\@@@()@@    Processing node calls and
 *          @()@||@@@@@'    deal with backend responses.
 *           '@@||@@@'
 *        jgs   ||
 *       ^^^^^^^^^^^^^^^^^
 */

REBASE.Node = function (){

    var global_node_data = {};
    var global_current_node_name;


    /* Private functions. */

    function convert_url_string_to_hash(arg){
        /*
         *  convert string to a hash
         *  input:  "a=1&b=2"
         *  output  {a:1, b:2}
         */
        var out = {};
        var args = arg.split('&');
        var x;
        var s;
        for (var i=0; i<args.length; i++){
            x = args[i];
            s = x.split('=');
            if (s.length == 2){
                out[s[0]] = s[1];
            }
        }
        return out;
    }

    function decode_node_string(node_string, item, target_form){
        /*
         *  Decodes a node string and returns an object.
         *  { node, type, command, url_data, node_data, layout_id, form_data, secure }
         *  or false if an error occurs
         */
        console_log(node_string);
        var error_msg = '';
        var decode = {};
        var split = node_string.split(':');
        var key;

        // node
        decode.node = split[1];
        // $ is shorthand for current node.
        if (decode.node == '$'){
            decode.node = split[1] = global_current_node_name;
        }

        // check enough info
        if (split.length < 2){
            error_msg = 'Invalid node data.\n\nNot enough arguments.';
            REBASE.Dialog.dialog('Application Error', error_msg);
            return false;
        }

        //command
        if (split.length > 2){
            decode.command = split[2];
            // if the command starts with a underscore we don't want
            // to trigger the command from a url change as this can
            // let dangerous commands be sent via urls
            decode.secure = (decode.command.substring(0,1) == '_');
        } else {
            decode.command = null;
            decode.secure = false;
        }
        decode.form_data = [];
        // url data converted to a hash
        if (split.length>3){
            var url_data = convert_url_string_to_hash(split[3]);
            if (target_form){
                decode.form_data.push({form : target_form, data : url_data});
            } else if (url_data.form){
                decode.form_data.push({form : url_data.form, data : url_data});
            } else {
                decode.url_data = url_data;
            }
        } else{
            decode.url_data = {};
        }

        decode.node_data = global_node_data;

        // if we have any extra node data we add it but
        // don't overwrite anything in the url.
        // I'm not sure if this is the best thing to do
        // but it is currently needed for the bookmarks to work correctly.
        for (key in decode.url_data){
            decode.node_data[key] = decode.url_data[key];
        }

        // FLAGS
        // The flags are used to indicate
        // the actions that the node call should perform.
        var flag_data = split[0];
        var flags = {};
        for (var i = 0; i < flag_data.length; i++){
            switch (flag_data.charAt(i)){
                case '/':
                    // ignore this
                    break;
                case 'a':
                    // authenticate
                    flags.authenticate = true;
                    break;
                case 'c':
                    // confirm
                    flags.confirm_action = true;
                    break;
                case 'd':
                    // open as dialog
                    flags.dialog = true;
                    break;
                case 'f':
                    // send form data
                    flags.form_data = true;
                    // get any form data
                    var $obj = $(item);
                    $obj = $obj.parents('div.INPUT_FORM');
                    var form_data = $obj.data('command')('get_form_data');
                    // set the form data
                    if (form_data){
                        decode.form_data.push(form_data);
                    } else {
                        // an error occurred on the form so we don't want to continue.
                        return false;
                    }
                    break;
                case 'u':
                    // update address bar
                    if (decode.secure){
                        error_msg = 'Invalid node data.\n\nCannot update on a secure command.';
                        REBASE.Dialog.dialog('Application Error', error_msg);
                        return false;
                    }
                    flags.update = true;
                    break;
                default:
                    error_msg = 'Invalid node flag ' + flag_data.charAt(i);
                    REBASE.Dialog.dialog('Application Error', error_msg);
                    return false;
            }
        }
        // if we are doing an update we cannot pass form data
        // as we loose the refering item.  Throw an error
        if (flags.update && (flags.form_data || flags.confirm_action)){
            error_msg = 'Cannot process request.\n\nTrying to update address to a node with form data or that needs confirmation.';
            REBASE.Dialog.dialog('Application Error', error_msg);
            return false;
        }
        decode.flags = flags;
        decode.node_string = split.join(':');

        return decode;
    }


    /* Public functions. */

    function get_node(decode){
        /*
         *  Takes a decoded node request does any processing needed
         *  and passes it to be the job processor to request
         */
        if (decode.flags.confirm_action){
            REBASE.Dialog.confirm_action(decode, 'Confirmation needed', 'are you sure?', decode);
            return false;
        }
        var info = decode;
        // application data
        if (!REBASE.application_data){
            info.request_application_data = true;
        }
        REBASE.Job.add(info);
    }

    function load_page(){
        /*
         *  function called on page load by address jquery plug-in
         *  used for back/forward buttons, bookmarking etc
         *  gets correct 'address' string and passes to calling function
         */
        var link = $.address.value();
        var decode = decode_node_string(link);
        if (!decode.secure){
            get_node(decode);
        }
    }

    function load_node(node_string, item, target_form){
        /*
         * Called from form buttons etc.
         * Get any form data needed and request node from backend.
         */

        // Deal with any special commands.
        switch (node_string){
            case 'BACK':
                // browser history back
                window.history.back();
                return false;
            case 'CLOSE':
                // close any open dialog
                REBASE.Dialog.close();
                return false;
            case 'RELOAD':
                // reload the current page
                REBASE.Dialog.close();
                // get the current page
                node_string = $.address.value();
        }

        var decode = decode_node_string(node_string, item, target_form);
        if (!decode){
            return false;
        }

        if (decode.flags.update &&
            $.address.value() != '/' + decode.node_string &&
            $.address.value() != decode.node_string){

            // Sets the address which then forces a page load.
            $.address.value(decode.node_string);
            return;
        }
        get_node(decode);
    }

    function set_node_data(node_name, node_data){
        global_current_node_name = node_name;
        global_node_data = node_data;
        console_log('node data:', node_data);
    }

    function is_update_node(node_string){
        // check if this is an update node_string
        // This is a fairly poor check at the moment.
        if (node_string.substring(0,1) == 'u' || node_string.substring(1,2) == 'u'){
            return true;
        } else {
            return false;
        }
    }

    // exported functions

    return {
        'load_page' : function (){
            /* Called by $.address.change() */
            load_page();
        },
        'load_node' : function (node_string, item, target_form){
            /* Called from form buttons etc sends the form
             * data and can call a target form. */
            load_node(node_string, item, target_form);
        },
        'set_node_data' : function (node_name, node_data){
            /* Used to set the node name and data */
            set_node_data(node_name, node_data);
        },
        'is_update_node' : function (node_string){
            /* is this an update node? */
            return is_update_node(node_string);
        },
        '_get_node' : function (decode){
            // Called to automatically load a node decode
            // needed by confirm dialog.
            // DO NOT USE THIS FUNCTION
            // Use load_node() instead
            get_node(decode);
        }
    };
}();


/*
 *           ('>
 *           /))@@@@@.
 *          /@"@@@@@()@
 *         .@@()@@()@@@@    JOB
 *         @@@O@@@@()@@@
 *         @()@@\@@@()@@    Send/receive ajax data calls.
 *          @()@||@@@@@'
 *           '@@||@@@'
 *        jgs   ||
 *       ^^^^^^^^^^^^^^^^^
 */

REBASE.Job = function(){

    var outstanding_requests = 0;
    var status_timer;

    function loading_show(){
        $('#ajax_info').show();
    }

    function loading_hide(){
        $('#ajax_info').hide();
    }

    function job_processor_status(data, node, root){
        // display the message form if it exists
        if (data.form){
            $('#' + root).status_form();
        }
        // show info on form
        if (data.data){
            var $status_form = $('div.STATUS_FORM');
            if ($status_form.length){
                $status_form.data('command')('update', data.data);
            }
        }
        // set data refresh if job not finished
        if (!data.data || !data.data.end){
            var node_string = "/:" + node + ":_status:id=" + data.data.id;
            status_timer = setTimeout(function (){
                                          REBASE.Node.load_node(node_string);
                                      }, 1000);
        }
    }

    function process(packet, job){

        var message;

        if (packet.data === null){
            console_log("NULL DATA PACKET");
            return;
        }

        var root = 'main'; //FIXME

        var title = packet.data.title;
        if (title){
            $.address.title(title);
        }

        var sent_node_data = packet.data.node_data;
        if (sent_node_data){
            REBASE.Node.set_node_data(packet.data.node, sent_node_data);
        }

        var user = packet.data.user;
        if (user){
            REBASE.User.update(user);
        }

        var bookmark = packet.data.bookmark;
        if (bookmark){
           REBASE.Bookmark.process(bookmark);
        }

        var data;
        switch (packet.data.action){
            case 'redirect':
                var link = packet.data.link;
                if (link){
                    REBASE.Node.load_node(link);
                }
                break;
            case 'html':
                $('#' + root).html(packet.data.data.html);
                break;
            case 'form':
            case 'dialog':
                 REBASE.Layout.update_layout(packet.data);
                 break;
            case 'function':
                REBASE.Functions.call(packet.data['function'], packet.data.data);
                break;
            case 'save_error':
                // FIXME not implemented
                break;
            case 'save':
                // FIXME not implemented
                break;
            case 'delete':
                // FIXME not implemented
                break;
            case 'general_error':
                message = packet.data.data;
                REBASE.Dialog.dialog('Error', message);
                break;
            case 'message':
                message = packet.data.data;
                REBASE.Dialog.dialog('Message', message);
                break;
            case 'forbidden':
                message = 'You do not have the permissions to perform this action.';
                REBASE.Dialog.dialog('Forbidden', message);
                break;
            case 'status':
                job_processor_status(packet.data.data, packet.data.node, root);
                break;
            default:
                REBASE.Dialog.dialog('Error', 'Action `' + packet.data.action + '` not recognised');
                break;
        }
    }

    function process_return(return_data, sent_data){
        var i;
        var n;
        outstanding_requests--;
        if (outstanding_requests === 0){
            loading_hide();
        }
        if (return_data !== null){
            for (i = 0, n = return_data.length; i < n; i++){
                process(return_data[i], sent_data);
            }
        } else {
            REBASE.Dialog.dialog('Application Error', 'No data was returned.\n\nThe application may not be running.');
        }
    }

	function add(request, sent_data){
		// this is where we make the ajax request
		var body = $.toJSON(request);
		$.post("/ajax", {body: body},
		  function(return_data){
			 process_return(return_data, sent_data);
		  }, "json");
        outstanding_requests++;
        loading_show();
	}

    return {
        'add' : function (request, data){
            add(request, data);
        }
    };
}();


/*
 *           ('>
 *           /))@@@@@.
 *          /@"@@@@@()@
 *         .@@()@@()@@@@    LAYOUT
 *         @@@O@@@@()@@@
 *         @()@@\@@@()@@    Manage forms and layout.
 *          @()@||@@@@@'
 *           '@@||@@@'
 *        jgs   ||
 *       ^^^^^^^^^^^^^^^^^
 */

REBASE.Layout = function(){


    var root = '#main';

    // The version of the layout to make sure we do not mix
    // data between layouts.  All updates to forms should
    // have a matching layout_id
    var layout_id = 0;

    // Form data set by external set_data function.
    var forms;

    // Layout data set by external set_data function.
    var layout;

    // Array of layout section JQuery objects.
    // for the current layout.
    var $layout_divs;

    var form_count;
    // The hash of JQuery forms on the layout
    // by form name.
    var $forms = {};

    var layout_title;
    var $header;
    var $footer;


    /*
     *      (\  }\   (\  }\   (\  }\
     *     (  \_('> (  \_('> (  \_('>   FORM DATA PROCESSOR
     *     (__(=_)  (__(=_)  (__(=_)
     *   jgs  -"=      -"=      -"=
     */

    var FormProcessor = function(){
        /* FormProcessor processes form data sent by the
         * backend.  Cache form data where possible.
         * Normailises forms etc.
         */

        // form data is kept here key is 'node_name|form_name'
        var form_data_cache = {};
        var form_data_cache_info = {};

        function clear_form_cache(){
            // Clear the form cache.
            form_data_cache = {};
            form_data_cache_info = {};
            console_log('FORM CACHE deleted');
        }

        function form_data_normalise(form_data, node){
            /* generally clean up the form data to
             * make things easier for us later on.
             * creates .items hash for quick reverse lookups etc.
             */

            form_data.node = node;
            // make hash of the fields
            form_data.items = {};
            for (var i = 0, n = form_data.fields.length; i < n; i++){
                var field = form_data.fields[i];
                field.index = i;
                if (field.name){
                    form_data.items[field.name] = field;
                }
                if (!field.control){
                    field.control = 'normal';
                }
                // get out the thumb field if one exists
                // makes life easier later on
                // TODO do we still use this?
                if (field.control == 'thumb'){
                    form_data.thumb = field;
                }
            }
            return form_data;
        }

        function process_form_data(form_data, node){
            /* If we have a suitable version in the form cache
             * then just return that else normalise the form.
             */
            var cache_name;
            if (form_data.cache_form !== undefined){
                cache_name = form_data.cache_node + '|' + form_data.cache_form;
                return form_data_cache[cache_name];
            }
            form_data = form_data_normalise(form_data, node);
            // form caching
            cache_name = node + '|' + form_data.name;
            if (!form_data.version){
                // remove from cache if it exists
                if (form_data_cache_info[node] !== undefined){
                    delete form_data_cache_info[node][form_data.name];
                }
            } else {
                // store form in cache
                form_data_cache[cache_name] = form_data;
                if (!form_data_cache_info[node]){
                    form_data_cache_info[node] = {};
                }
                form_data_cache_info[node][form_data.name] = form_data.version;
            }
            return form_data;
        }

        function process_form_data_all(forms_data, node){
            var full_form_data = {};
            var form_data;
            for (var form in forms_data){
                form_data = {};
                form_data.data = forms_data[form].data;
                form_data.paging = forms_data[form].paging;
                form_data.form = process_form_data(forms_data[form].form, node);
                full_form_data[form] = form_data;
            }
            return full_form_data;
        }

        // exported functions
        return {
            'process' : function (form_data, node_data){
                return process_form_data_all(form_data, node_data);
            },
            'debug_form_info' : function (){
                return form_data_cache;
            },
            'clear_form_cache' : function (node_name){
                clear_form_cache();
            },
            'get_form_cache_data' : function (node_name){
                return form_data_cache_info[node_name];
            }
        };
    }();


    /*
     *      (\  }\   (\  }\   (\  }\
     *     (  \_('> (  \_('> (  \_('>   LAYOUT FUNCTIONS
     *     (__(=_)  (__(=_)  (__(=_)
     *   jgs  -"=      -"=      -"=
     */


    function set_layout_title_and_footer(){
        if (layout_title){
            $header.text(layout_title);
        }
        var footer = 'footer';
        $footer.text(footer);
    }

    function make_form(form_name){
        /* create the form requested and return it as a JQuery object */
        var form = forms[form_name].form;
        var data = forms[form_name].data;
        var paging = forms[form_name].paging;
        var form_type = forms[form_name].form.form_type;

        var $div = $('<div class="FORM_HOLDER" id="form_' + (form_count++) + '"/>');
        if (form_type == 'grid'){
            $div.grid2(form, data, paging);
        } else {
            $div.input_form(form, data, paging);
        }
        return $div;
    }

    function replace_forms(){
        /* Replace a named form in the layout with
         * a newly created form of the same name.
         * Used for updating form(s) whilst keeping
         * the rest of the layout.
         */

        for (var i = 0; i< layout.layout_forms.length; i++){
            var form_name = layout.layout_forms[i];
            if ($forms[form_name]){
                $forms[form_name].empty();
                $forms[form_name].append(make_form(form_name));
            } else {
                console_log('TRIED TO USE UNINITIALISED FORM ' + form_name);
            }
        }
        set_layout_title_and_footer();
    }

    function create_layout(){
        /* Build the layout (including all contained forms)
         * and place it in the 'root' DOM element.
         *
         */
        var $layout;
        var sections;
        var section;
        var form_name;
        var $form;

        function build_layout(){
            /* Create the actual layout HTML.
             * Refreshes data relating to the layout
             * this destroys the 'knowledge' of the previous layout.
             */

            // reset the layout
            $layout_divs = [];
            $forms = {};
            // new layout so change id
            layout_id++;

            // This is the outer holder for the new layout.
            var $layout = $('<div class="LAYOUT_HOLDER">');

            function make_layout_section(layout_class){
                /* Creates a layout section of the requested class.
                 * Attaches it to the layout and stores the innermost div in
                 * $layout_divs for later access.
                 */

                var $section_subdiv = $('<div class="STYLE">');
                var $section = $('<div class="' + layout_class + '">');
                $section.append($section_subdiv);
                $layout_divs.push($section_subdiv);
                $layout.append($section);
            }

            // Create the layout.
            // These are the available layouts.
            $header = $('<div class="LAYOUT_HEADER"></div>');
            $layout.append($header);
            switch (layout.layout_type){
                case 'entity':
                    make_layout_section("LAYOUT_COL_LEFT");
                    make_layout_section("LAYOUT_COL_RIGHT");
                    make_layout_section("LAYOUT_COL_FULL");
                    break;
                case 'listing':
                    make_layout_section("LAYOUT_COL_FULL");
                    break;
                default:
                    console_log('UNKNOWN LAYOUT: ' + layout.layout_type);
                    break;
            }
            $footer = $('<div class="LAYOUT_FOOTER"></div>');
            $layout.append($footer);
            return $layout;
        }

        form_count = 0;
        // Create the base layout with sections
        $layout = build_layout();
        sections = layout.form_layout;
        // Add the required forms to the correct layout section.
        for (var i = 0; i < sections.length; i++){
            section = sections[i];
            for (var j = 0; j < section.length; j++){
                form_name = section[j];
                // ensure that we actually have data for this form
                if (forms[form_name] === undefined){
                    console_log('ERROR: form `' + form_name + '` is in the layout but no data exists.');
                } else {
                    $form = make_form(form_name);
                    $layout_divs[i].append($form);
                    // save it for future lookups
                    $forms[form_name] = $form;
                }
            }
        }
        // set the title
        set_layout_title_and_footer();
        // Replace root DOM elements content with the new layout
        // and scroll to the top.
        var $root = $(root);
        $root.empty();
        $root.scrollTop(0);
        $root.append($layout);
    }

    function add_forms_to_layout(packet){
        /* Create a new layout or update form(s)
         * depending on the data provided.
         * If the layout_type is provided then we
         * build a whole new layout.  If not we just replace the forms
         * This function is EXPORTED.
         */

        // retrieve layout data
        var layout_data = packet.layout;
        // Store the form data.
        forms = FormProcessor.process(packet.data, packet.node);
        layout_title = layout_data.layout_title;

        if (layout_data.layout_dialog){
            REBASE.Dialog.dialog(layout_data.layout_title, forms[layout_data.layout_dialog]);
        } else {
            REBASE.Dialog.close();
            if (layout_data.layout_type){
                // Layout has changed so update our stored data.
                layout = layout_data;
                create_layout();
                // focus first enabled input
                REBASE.Form.focus($(root).find(':input:enabled').first());
            } else {
                // Update the layout forms
                layout.layout_forms = layout_data.layout_forms;
                replace_forms();
            }
        }
    }
    // exported functions
    return {
        'update_layout' : function (packet){
            // Create or update the layout.
            add_forms_to_layout(packet);
        },
        'get_layout_id' : function (){
            return layout_id;
        },
        'debug_form_info' : function (){
            return FormProcessor.debug_form_info();
        },
        'clear_form_cache' : function (node_name){
                FormProcessor.clear_form_cache();
            },
        'get_form_cache_info' : function (node_name){
            return FormProcessor.get_form_cache_data(node_name);
        }
    };
}();