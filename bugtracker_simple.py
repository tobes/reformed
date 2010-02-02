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

import reformed.reformed as r
from reformed.database import table, entity, relation
from reformed.fields import *

d =  r.reformed

entity('ticket', d,

       Text("title", mandatory = True),
       Text("summary", length = 4000),
       DateTime("complete_by"), 
       Boolean("accepted"), 

       Created("created_date"), 
       CreatedBy("created_by"),

       title_field = "title"
)

d.persist()




