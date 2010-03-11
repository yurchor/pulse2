<?

/*
 * (c) 2004-2007 Linbox / Free&ALter Soft, http://linbox.com
 * (c) 2007-2009 Mandriva, http://www.mandriva.com
 *
 * $Id$
 *
 * This file is part of Mandriva Management Console (MMC).
 *
 * MMC is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * MMC is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with MMC; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 */

/* Get MMC includes */
require("../../../includes/config.inc.php");
require("../../../includes/i18n.inc.php");
require("../../../includes/acl.inc.php");
require("../../../includes/session.inc.php");
require("../../../includes/PageGenerator.php");
require("../includes/includes.php");
require('../includes/xmlrpc.inc.php');

$params = getParams();
$location = getCurrentLocation();

if (xmlrpc_doesLocationHasImagingServer($location)) {
    $t = new TitleElement(_T("Available masters", "imaging"));
    $t->display();

    $ajax = new AjaxFilter("modules/imaging/manage/ajaxMasterLevel2.php", "Level2", $params, "formLevel2");
    //$ajax->setRefresh(10000);
    $ajax->display();
    echo '<br/><br/><br/>';
    $ajax->displayDivToUpdate();
} else {
    $ajax = new AjaxFilter(urlStrRedirect("imaging/manage/ajaxAvailableImagingServer"), "container", array('from'=>$_GET['from']));
    $ajax->display();
    print "<br/><br/><br/>";
    $ajax->displayDivToUpdate();
}

?>
