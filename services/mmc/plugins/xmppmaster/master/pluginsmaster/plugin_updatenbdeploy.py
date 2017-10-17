# -*- coding: utf-8 -*-
#
# (c) 2016-2017 siveo, http://www.siveo.net
#
# This file is part of Pulse 2, http://www.siveo.net
#
# Pulse 2 is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Pulse 2 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pulse 2; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.

import base64
import json
import os
import utils
import pprint
from pulse2.database.xmppmaster import XmppMasterDatabase

import logging

plugin = { "VERSION" : "1.0", "NAME" : "updatenbdeploy", "TYPE" : "master" }

#=====================================================
#DEBUG   {'VERSION': '1.0', 'TYPE': 'master', 'NAME': 'updatenbdeploy'} : 
#DEBUG   data plugin {
    #"idcmd": 39, 
    #"countnb": 0, 
    #"grp": 14, 
    #"exec": true, 
    #"consignnb": "", 
    #"nbtotal": 1, 
    #"login": "root"
#}
#=====================================================

def action( xmppobject, action, sessionid, data, message, ret, dataobj):
    try:
        print "====================================================="
        print "====================================================="
        print "====================================================="
        print "====================================================="
        print "====================================================="
        print "====================================================="
        print "====================================================="
        print "====================================================="
        logging.getLogger().debug("%s : "%plugin)
        logging.getLogger().debug("data plugin %s "%(json.dumps(data, indent = 4)))
        XmppMasterDatabase().updatedeployinfo(data['idcmd'])
        print "====================================================="
        print "====================================================="
        print "====================================================="
        print "====================================================="
        print "====================================================="
        print "====================================================="
        print "====================================================="
        print "====================================================="
    except Exception as e:
        print "Error in plugin %s"%str(e)
