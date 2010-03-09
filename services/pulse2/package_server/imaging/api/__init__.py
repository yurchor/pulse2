# -*- coding: utf-8; -*-
#
# (c) 2007-2010 Mandriva, http://www.mandriva.com/
#
# $Id$
#
# This file is part of Pulse 2, http://pulse2.mandriva.org
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
# along with Pulse 2.  If not, see <http://www.gnu.org/licenses/>.

"""
Pulse 2 Package Server Imaging API
"""

import logging
import os
import shutil

from twisted.internet import defer
from twisted.internet.defer import maybeDeferred

from pulse2.package_server.config import P2PServerCP as PackageServerConfig
from pulse2.package_server.xmlrpc import MyXmlrpc
from pulse2.package_server.imaging.api.client import ImagingXMLRPCClient
from pulse2.package_server.imaging.cache import UUIDCache
from pulse2.package_server.imaging.api.status import Status
from pulse2.package_server.imaging.menu import isMenuStructure, ImagingDefaultMenuBuilder, ImagingComputerMenuBuilder

from pulse2.utils import isMACAddress, splitComputerPath, macToNode, isUUID, rfc3339Time, humanReadable
from pulse2.apis import makeURL
from pulse2.imaging.image import Pulse2Image

from time import gmtime
try:
    import uuid
except ImportError:
    import mmc.support.uuid as uuid


class ImagingApi(MyXmlrpc):

    myType = 'Imaging'
    myUUIDCache = UUIDCache()

    def __init__(self, name, config):
        """
        @param config: Package server config
        @type config: P2PServerCP
        """
        MyXmlrpc.__init__(self)
        self.name = name
        self.logger = logging.getLogger('imaging')
        self.logger.info("Initializing %s" % self.myType)
        # Read and check configuration
        self.config = config
        # FIXME: un-comment me later :)
        # self.check()

    def check(self):
        """
        Validate imaging configuration.

        @raise ValueError: if the configuration is not right
        """
        basefolder = self.config.imaging_api['base_folder']
        for folder in ['base', 'bootloader', 'bootmenus', 'diskless',
                       'computers', 'inventories', 'masters', 'postinst']:
            optname = folder + '_folder'
            dirname = self.config.imaging_api[optname]
            if folder != 'base':
                dirname = os.path.join(basefolder, dirname)
            if not os.path.isdir(dirname):
                raise ValueError, "Directory '%s' does not exists. Please check option '%s' in your configuration file." % (dirname, optname)
        for optname in ['diskless_kernel', 'diskless_initrd',
                      'diskless_memtest']:
            fpath = os.path.join(basefolder,
                                 self.config.imaging_api['diskless_folder'],
                                 self.config.imaging_api[optname])
            if not os.path.isfile(fpath):
                raise ValueError, "File '%s' does not exists. Please check option '%s' in your configuration file." % (fpath, optname)

    def _getXMLRPCClient(self):
        """
        @return: a XML-RPC client allowing to connect to the agent
        @rtype: ImagingXMLRPCClient
        """
        url, _ = makeURL(PackageServerConfig().mmc_agent)
        return ImagingXMLRPCClient(
            '',
            url,
            PackageServerConfig().mmc_agent['verifypeer'],
            PackageServerConfig().mmc_agent['cacert'],
            PackageServerConfig().mmc_agent['localcert'])

    def xmlrpc_getServerDetails(self):
        pass

    def xmlrpc_logClientAction(self, mac, level, phase, message):
        """
        Remote logging.

        Mainly used to send progress info to our mmc-agent.

        @param mac : The mac address of the client
        @param level : the log level
        @param phase : what the client was doing when the info was logged
        @param message : the log message itself
        @raise TypeError: if MACAddress is malformed
        @return: a deferred object resulting to 1 if processing was
                 successful, else 0.
        @rtype: int
        """

        def _getmacCB(result):
            if result and type(result) == dict :
                client = self._getXMLRPCClient()
                func = 'imaging.logClientAction'
                args = (self.config.imaging_api['uuid'], result['uuid'], level, phase, message)
                d = client.callRemote(func, *args)
                d.addCallbacks(lambda x : True, client.onError, errbackArgs = (func, args, 0))
                return d

            self.logger.warn('Imaging: Failed resolving UUID for client %s : %s' % (mac, result))
            return False

        if not isMACAddress(mac):
            raise TypeError

        self.logger.debug('Imaging: Client %s sent a log message while %s (%s) : %s' % (mac, phase, level, message))
        d = self.xmlrpc_getComputerByMac(mac)
        d.addCallback(_getmacCB)
        return d

    def xmlrpc_computerMenuUpdate(self, mac):
        """
        Perform a menu refresh.

        @param mac : The mac address of the client
        @return: a deferred object resulting to 1 if processing was
                 successful, else 0.
        @rtype: int
        """

        def _getmacCB(result):
            if result and type(result) == dict :
                # TODO : call menu refresh here
                return True
            self.logger.warn('Imaging: Failed resolving UUID for client %s : %s' % (mac, result))
            return False

        if not isMACAddress(mac):
            raise TypeError
        self.logger.debug('Imaging: Client %s asked for a menu update' % (mac))
        d = self.xmlrpc_getComputerByMac(mac)
        d.addCallback(_getmacCB)
        return d

    def xmlrpc_imagingServerStatus(self):
        """
        Returns the percentage of remaining size from the part where the images
        are stored.

        @return: a percentage, or -1 if it fails
        @rtype: int
        """
        status = Status(self.config)
        status.deferred = defer.Deferred()
        status.get()
        return status.deferred

    def xmlrpc_computersRegister(self, computers):
        """
        Mass method to perform multiple computerRegister.
        Always called by the MMC agent.

        @param computers: list of triplets (hostname,MAC address,imaging data)
        @type computers: list

        @return: the list of UUID that were successfully registered.
        @rtype: list
        """
        ret = []
        for item in computers:
            try:
                computerName, macAddress, imagingData = item
            except (ValueError, TypeError):
                self.logger.error("Can't register computer, bad input value: %s" % (str(item)))
                continue
            if not imagingData:
                self.logger.error("No imaging data available for %s / %s" % (computerName, macAddress))
                continue
            try:
                if self.xmlrpc_computerRegister(computerName, macAddress, imagingData):
                    # Registration succeeded
                    ret.append(imagingData['uuid'])
            except Exception, e:
                self.logger.error("Can't register computer %s / %s: %s" % (computerName, macAddress, str(e)))
        return ret

    def xmlrpc_computerRegister(self, computerName, macAddress, imagingData = False):
        """
        Method to register a new computer.

        if imagingData is set, we know that the method is called from a MMC
        agent !

        @raise TypeError: if computerName or MACAddress are malformed
        @return: a deferred object resulting to True if registration was
                 successful, else False.
        @rtype: bool
        """

        def onSuccess(result):
            if type(result) != list and len(result) != 2:
                self.logger.warn('Imaging: Couldn\'t register client %s (%s) : %s' % (computerName, macAddress, str(result)))
                ret = False
            elif not result[0]:
                self.logger.warn('Imaging: Couldn\'t register client %s (%s) : %s' % (computerName, macAddress, result[1]))
                ret = False
            else:
                uuid = result[1]
                self.logger.info('Imaging: Register client %s (%s) as %s' % (computerName, macAddress, uuid))
                self.myUUIDCache.set(uuid, macAddress, hostname, domain)
                ret = self.xmlrpc_computerPrepareImagingDirectory(uuid, {'mac': macAddress, 'hostname': hostname})
            return ret

        try:
            # check MAC Addr is conform
            if not isMACAddress(macAddress):
                raise TypeError('Malformed MAC address: %s' % macAddress)
            # check computer name is conform
            if not len(computerName):
                raise TypeError('Malformed computer name: %s' % computerName)
            profile, entities, hostname, domain = splitComputerPath(computerName)
        except TypeError, ex:
            self.logger.error('Imaging: Won\'t register %s as %s : %s' % (macAddress, computerName, ex))
            return maybeDeferred(lambda x: x, False)

        if not imagingData:
            # Registration is coming from the imaging server
            self.logger.info('Imaging: Starting registration for %s as %s' % (macAddress, computerName))
            client = self._getXMLRPCClient()
            func = 'imaging.computerRegister'
            args = (self.config.imaging_api['uuid'], hostname, domain, macAddress, profile, entities)
            d = client.callRemote(func, *args)
            d.addCallbacks(onSuccess, client.onError, errbackArgs = (func, args, False))
            return d
        else:
            # Registration is coming from the MMC agent
            if not 'uuid' in imagingData:
                self.logger.error('UUID missing in imaging data')
                return False
            cuuid = imagingData['uuid']
            self.myUUIDCache.set(cuuid, macAddress, hostname, domain)
            if not self.xmlrpc_computerPrepareImagingDirectory(cuuid, {'mac': macAddress, 'hostname': computerName}):
                return False
            if self.xmlrpc_computersMenuSet(imagingData['menu']) != [cuuid]:
                return False
            return True

    def xmlrpc_computerPrepareImagingDirectory(self, uuid, imagingData = False):
        """
        Prepare a full imaging folder for client <uuid>

        if imagingData is False, ask the mmc agent for additional
        parameters (not yet done).

        @param mac : The mac address of the client
        @type menus: MAC Address
        @param imagingData : The data to use for image creation
        @type imagingData: ????
        """
        target_folder = os.path.join(PackageServerConfig().imaging_api['base_folder'], PackageServerConfig().imaging_api['computers_folder'], uuid)
        if os.path.isdir(target_folder):
            self.logger.warn('Imaging: folder %s for client %s : It already exists !' % (target_folder, uuid))
            return True
        if os.path.exists(target_folder):
            self.logger.warn('Imaging: folder %s for client %s : It already exists, but is not a folder !' % (target_folder, uuid))
            return False
        try:
            os.mkdir(target_folder)
        except Exception, e:
            self.logger.warn('Imaging: I was not able to create folder %s for client %s : %s' % (target_folder, uuid, e))
            return False
        return True

    def xmlrpc_computerUpdate(self, MACAddress):
        """
        Method to update the menu a computer.

        @raise TypeError: if MACAddress is malformed
        @return: a deferred object resulting to 1 if update was
                 successful, else 0.
        @rtype: int
        """

        def onSuccess(result):
            # TODO : add menu re-generation here
            return 1

        if not isMACAddress(MACAddress):
            raise TypeError

        url, credentials = makeURL(PackageServerConfig().mmc_agent)

        self.logger.info('Imaging: Starting menu update for %s' % (MACAddress))
        client = self._getXMLRPCClient()
        func = 'imaging.getMenu'
        args = (MACAddress)
        d = client.callRemote(func, *args)
        d.addCallbacks(onSuccess, client.onError, errbackArgs = (func, args, 0))
        return d

    def xmlrpc_injectInventory(self, MACAddress, Inventory):
        """
        Method to process the inventory of a computer

        @raise TypeError: if MACAddress is malformed
        @return: a deferred object resulting to 1 if processing was
                 successful, else 0.
        @rtype: int
        """

        def _getmacCB(result):
            if result and type(result) == dict:
                client = self._getXMLRPCClient()
                func = 'imaging.injectInventory'
                args = (self.config.imaging_api['uuid'], result['uuid'], Inventory)
                d = client.callRemote(func, *args)
                d.addCallbacks(lambda x: True, client.onError, errbackArgs=(func, args, 0))
                return d
            self.logger.warn('Imaging: Failed resolving UUID for client %s : %s' % (MACAddress, result))
            return False

        if not isMACAddress(MACAddress):
            raise TypeError
        self.logger.debug('Imaging: Starting inventory processing for %s' % (MACAddress))
        d = self.xmlrpc_getComputerByMac(MACAddress)
        d.addCallback(_getmacCB)
        return d

    def xmlrpc_getComputerByMac(self, MACAddress):
        """
        Method to obtain informations about a computer using its MAC address.

        We are using a cache system :
        pulse2.package_server.imaging.cache.UUIDCache()

        @raise TypeError: if MACAddress is malformed
        @return: a deferred object resulting to 1 if processing was
                 successful, else 0.
        @rtype: int
        """

        def onSuccess(result):
            if type(result) == dict and "faultCode" in result:
                self.logger.warning('Imaging: While processing result for %s : %s' % (MACAddress, result['faultTraceback']))
                return False
            try:
                if result[0]:
                    self.myUUIDCache.set(result[1]['uuid'], MACAddress, result[1]['shortname'], result[1]['fqdn'])
                    self.logger.info('Imaging: Updating cache for %s' % (MACAddress))
                    return result[1]
                else:
                    return False
            except Exception, e:
                self.logger.warning('Imaging: While processing result %s for %s : %s' % (result, MACAddress, e))

        if not isMACAddress(MACAddress):
            raise TypeError

        # try to extract from our cache
        res = self.myUUIDCache.getByMac(MACAddress)
        if res: # fetched from cache
            return maybeDeferred(lambda x: x, res)
        else: # cache fetching failed, try to obtain the real value
            self.logger.info('Imaging: Getting computer UUID for %s' % (MACAddress))
            client = self._getXMLRPCClient()
            func = 'imaging.getComputerByMac'
            args = [MACAddress]
            d = client.callRemote(func, *args)
            d.addCallbacks(onSuccess, client.onError, errbackArgs=(func, args, 0))
            return d

    def xmlrpc_computersMenuSet(self, menus):
        """
        Set computers imaging boot menu.

        @param menus: list of (uuid, menu) couples
        @type menus: list

        @ret: list of the computer uuid which menu have been successfully set
        @rtype: list
        """
        ret = []
        for cuuid in menus:
            menu = menus[cuuid]
            if not isUUID(cuuid):
                self.logger.error('Invalid computer UUID %s' % cuuid)
                continue
            if not isMenuStructure(menu):
                self.logger.error("Invalid menu structure for computer UUID %s" % cuuid)
                continue
            macaddress = self.myUUIDCache.getByUUID(cuuid)
            if macaddress == False:
                self.logger.error("Can't get MAC address for UUID %s" % cuuid)
                continue
            else:
                try:
                    macaddress = macaddress['mac']
                    self.logger.debug('Setting menu for computer UUID/MAC %s/%s' % (cuuid, macaddress))
                    imb = ImagingComputerMenuBuilder(self.config, macaddress, menu)
                    imenu = imb.make()
                    imenu.write()
                    ret.append(cuuid)
                except Exception, e:
                    self.logger.exception("Error while setting new menu of computer uuid/mac %s: %s" % (cuuid, e))
                    # FIXME: Rollback to the previous menu
        return ret

    def xmlrpc_imagingServerDefaultMenuSet(self, menu):
        """
        Set the imaging server default boot menu displayed to all un-registered
        computers.

        Called by the MMC agent.

        @param menu: default menu to set
        @type menu: dict

        @return: True if successful
        @rtype: bool
        """
        if not isMenuStructure(menu):
            self.logger.error("Can't set default computer menu: bad menu structure")
            ret = False
        else:
            try:
                self.logger.debug('Setting default boot menu for computers')
                imb = ImagingDefaultMenuBuilder(self.config, menu)
                imenu = imb.make()
                imenu.write()
                ret = True
            except Exception, e:
                self.logger.exception("Error while setting default boot menu of unregistered computers: %s" % e)
                ret = False
        return ret

    ## Image management

    def xmlrpc_computerCreateImageDirectory(self, mac):
        """
        Create an image folder for client <mac>

        This is quiet different as for the LRS, where the UUID was given
        in revosavedir (kernel command line) : folder is now generated
        real-time, if no generation has been done backup is dropped
        client-side

        @param mac : The mac address of the client
        @type menus: MAC Address
        """

        def _getmacCB(result):
            if result and type(result) == dict :
                computer_uuid = result['uuid']
                self.logger.warn('Imaging: New image %s for client %s' % (image_uuid, computer_uuid))
                return image_uuid

            self.logger.warn('Imaging: Failed resolving UUID for client %s : %s' % (mac, result))
            return False

        if not isMACAddress(mac):
            raise TypeError

        self.logger.debug('Imaging: Client %s want to create an image' % (mac))

        target_folder = os.path.join(PackageServerConfig().imaging_api['base_folder'], PackageServerConfig().imaging_api['masters_folder'])
        # compute our future UUID, using the MAC address as node
        # according the doc, the node is a 48 bits (= 6 bytes) integer
        attempts = 10
        while attempts:
            image_uuid = str(uuid.uuid1(macToNode(mac)))
            if not os.path.exists(os.path.join(target_folder, image_uuid)):
                break
            attempts -= 1

        if not attempts:
            self.logger.warn('Imaging: I was not able to create a folder for client %s' % (mac))
            return maybeDeferred(lambda x: x, False)

        try:
            os.mkdir(os.path.join(target_folder, image_uuid))
        except Exception, e:
            self.logger.warn('Imaging: I was not able to create folder %s for client %s : %s' % (os.path.join(target_folder, image_uuid), mac, e))
            return maybeDeferred(lambda x: x, False)

        # now the folder is created (and exists), if can safely be used
        d = self.xmlrpc_getComputerByMac(mac)
        d.addCallback(_getmacCB)
        return d

    def xmlrpc_computerChangeDefaultMenuItem(self, mac, num):
        """
        Called by computer MAC when he want to set its default entry to num

        @param mac : The mac address of the client
        @param num : The menu number
        @type mac: MAC Address
        @type num: int
        """

        def onSuccess(result):
            if type(result) != list and len(result) != 2:
                self.logger.error('Imaging: Couldn\'t set default entry on %s for %s : %s' % (num, computerUUID, str(result)))
                ret = False
            elif not result[0]:
                self.logger.error('Imaging: Couldn\'t set default entry on %s for %s : %s' % (num, computerUUID, str(result)))
                ret = False
            else:
                self.logger.error('Imaging: Couldn\'t set default entry on %s for %s : %s' % (num, computerUUID, str(result)))
                ret = True
            return ret

        if not isMACAddress(mac):
            self.logger.error("Bad computer MAC %s" % str(mac))
            ret = False
        else:
            computerUUID = self.myUUIDCache.getByMac(mac)
            if not computerUUID:
                self.logger.error("Can't get computer UUID for MAC address %s" % mac)
                ret = False
            else:
                computerUUID = computerUUID['uuid']
                client = self._getXMLRPCClient()
                func = 'imaging.computerChangeDefaultMenuItem'
                args = (self.config.imaging_api['uuid'], computerUUID, num)
                d = client.callRemote(func, *args)
                d.addCallbacks(onSuccess, client.onError, errbackArgs = (func, args, False))
                return d
        return ret

    def xmlrpc_imageDone(self, computerMACAddress, imageUUID):
        """
        Called by the imaging server to register a new image.

        @return: True if successful
        @rtype: bool
        """

        def _onSuccess(result):
            if type(result) != list and len(result) != 2:
                self.logger.error('Imaging: Couldn\'t register on the MMC agent the image with UUID %s : %s' % (imageUUID, str(result)))
                ret = False
            elif not result[0]:
                self.logger.error('Imaging: Couldn\'t register on the MMC agent the image with UUID %s : %s' % (imageUUID, result[1]))
                ret = False
            else:
                self.logger.debug('Imaging: Successfully registered image %s' % imageUUID)
                ret = True
            return ret

        def _gotMAC(result):
            """
            Process result return by xmlrpc_getComputerByMac, BTW should be either False or the required info
            """
            if not result:
                self.logger.error("Can't get computer UUID for MAC address %s" % (computerMACAddress))
                return False
            else:
                # start gathering details about our image

                c_uuid = result['uuid']
                isMaster = False # by default, an image is private
                path = os.path.join(self.config.imaging_api['base_folder'], self.config.imaging_api['masters_folder'], imageUUID)
                image = Pulse2Image(path)
                size = image.size
                creationDate = tuple(gmtime())
                name = "Backup of %s" % result['shortname']
                desc = "%s, %s" % (rfc3339Time(), humanReadable(size))
                creator = ""

                client = self._getXMLRPCClient()
                func = 'imaging.imageRegister'
                args = (self.config.imaging_api['uuid'], c_uuid, imageUUID, isMaster, name, desc, path, size, creationDate, creator)
                d = client.callRemote(func, *args)
                d.addCallbacks(_onSuccess, client.onError, errbackArgs = (func, args, False))
                return d

        if not isUUID(imageUUID):
            self.logger.error("Bad image UUID %s" % str(imageUUID))
            ret = False
        elif not isMACAddress(computerMACAddress):
            self.logger.error("Bad computer MAC %s" % str(computerMACAddress))
            ret = False
        else:
            d = self.xmlrpc_getComputerByMac(computerMACAddress)
            d.addCallback(_gotMAC)
            return d
        return ret

    def xmlrpc_imagingServerImageDelete(self, imageUUID):
        """
        Delete an image (backup or master) from the imaging server.
        The corresponding directory is simply removed.

        @param imageUUID: image UUID
        @type: str

        @return: True if it worked, else False
        @rtype: bool
        """
        if not isUUID(imageUUID):
            self.logger.warn("Bad image UUID %s" % str(imageUUID))
            ret = False
        else:
            path = os.path.join(self.config.imaging_api['base_folder'], self.config.imaging_api['masters_folder'], imageUUID)
            if os.path.exists(path):
                try:
                    shutil.rmtree(path)
                    ret = True
                except Exception, e:
                    self.logger.error("Error while removing image with UUID %s: %s" % (imageUUID, e))
                    ret = False

            else:
                self.logger.warn("Can't delete unavailable image with UUID %s" % imageUUID)
                ret = False
        return ret

    ## Imaging server configuration

    def xmlrpc_imagingServerConfigurationSet(self, conf):
        """
        Set the global imaging server configuration (traffic shaping, etc.)

        @param conf: imaging server configuration to apply
        @type conf: dict
        """
        self.logger.warn("Not yet implemented !")
        return True
