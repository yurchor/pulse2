<?php
/**
 * (c) 2004-2007 Linbox / Free&ALter Soft, http://linbox.com
 * (c) 2007 Mandriva, http://www.mandriva.com/
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

require('modules/msc/includes/utilities.php');
require('modules/msc/includes/commands_xmlrpc.inc.php');
require('modules/msc/includes/package_api.php');
require('modules/msc/includes/scheduler_xmlrpc.php');

/* start_tele_diff.php is called when a user hit the "deploy button", rightmost of a package */

#### FORM POST HANDLING ####
/* User did confirm his action => do a deployment */
if (isset($_POST["bconfirm"])) {
    $from = $_POST['from'];
    $path =  explode('|', $from);
    $module = $path[0];
    $submod = $path[1];
    $page = $path[2];
    $tab = $path[3];

    $p_api = new ServerAPI();
    $p_api->fromURI($_POST["papi"]);

    $params = array();
    foreach (array('create_directory', 'start_script', 'delete_file_after_execute_successful', 'wake_on_lan', 'next_connection_delay', 'max_connection_attempt', 'start_inventory') as $param) {
        $params[$param] = $_POST[$param];
    }

    $hostname = $_POST['hostname'];
    $uuid = $_POST['uuid'];
    $gid = $_POST['gid'];
    $pid = $_POST['pid'];
    $mode = $_POST['copy_mode'];

    $cible = array($uuid, $hostname);
    if ($gid) {
        $group = new Group($_GET['gid']);
        $cible = array_map("onlyValues", $group->getResult(0, -1));
    }

    // TODO: activate this  : msc_command_set_pause($cmd_id);
    add_command_api($pid, $cible, $params, $p_api, $mode, $gid);
    dispatch_all_commands();
    scheduler_start_all_commands();
    header("Location: " . urlStrRedirect("$module/$submod/$page", array('tab'=>$tab, 'uuid'=>$uuid, 'hostname'=>$hostname, 'gid'=>$gid)));
}

/* User wants do do custom stuff => display the "advanced" form */
if (isset($_POST["badvanced"])) {
    $from = $_POST['from'];
    $path =  explode('|', $from);
    $module = $path[0];
    $submod = $path[1];
    $page = $path[2];
    $tab = $path[3];

    $params = array();
    foreach (array('hostname', 'gid', 'uuid', 'hostname', 'from', 'pid', 'create_directory', 'start_script', 'delete_file_after_execute_successful', 'wake_on_lan', 'next_connection_delay', 'max_connection_attempt', 'start_inventory', 'papi', 'copy_mode') as $param) {
        $params[$param] = $_POST[$param];
    }
    $params['tab'] = 'tablaunch';
    $params['badvanced'] = True;
    header("Location: " . urlStrRedirect("$module/$submod/$page", $params));
}
#### /FORM POST HANDLING ####

#### FORM DISPLAY HANDLING ####
// vars preseeding
$from = $_GET['from'];
$hostname = $_GET['hostname'];
$uuid = $_GET['uuid'];
$gid = $_GET['gid'];
$pid = $_GET['pid'];
$p_api = new ServerAPI();
$p_api->fromURI($_GET['papi']);
$cible = array($uuid, $hostname);
if ($gid) {
    $group = new Group($_GET['gid'], true);
    $cible = $group->getName();
}
$name = getPackageLabel($p_api, $_GET["pid"]);
$version = getPackageVersion($p_api, $_GET["pid"]);
$f = new PopupForm(sprintf(_T("Deploy <b>%s v.%s</b><br/> on <b>%s</b>", "msc"), $name, $version, $hostname));

// form preseeding
$hidden = new HiddenTpl("papi");
$f->add($hidden, array("value" => $_GET["papi"], "hide" => True));
$hidden = new HiddenTpl("name");
$f->add($hidden, array("value" => $hostname, "hide" => True));
$hidden = new HiddenTpl("uuid");
$f->add($hidden, array("value" => $uuid, "hide" => True));
$hidden = new HiddenTpl("gid");
$f->add($hidden, array("value" => $gid, "hide" => True));
$hidden = new HiddenTpl("from");
$f->add($hidden, array("value" => $from, "hide" => True));
$hidden = new HiddenTpl("pid");
$f->add($hidden, array("value" => $pid, "hide" => True));
$hidden = new HiddenTpl("create_directory");
$f->add($hidden, array("value" => 'on', "hide" => True));
$hidden = new HiddenTpl("start_script");
$f->add($hidden, array("value" => 'on', "hide" => True));
$hidden = new HiddenTpl("delete_file_after_execute_successful");
$f->add($hidden, array("value" => 'on', "hide" => True));
$hidden = new HiddenTpl("next_connection_delay");
$f->add($hidden, array("value" => 60, "hide" => True));
$hidden = new HiddenTpl("max_connection_attempt");
$f->add($hidden, array("value" => 3, "hide" => True));
$check = new TrFormElement(_T('awake', 'msc'), new CheckboxTpl("wake_on_lan"));
$f->add($check, array("value" => ''));
$check = new TrFormElement(_T('invent.', 'msc'), new CheckboxTpl("start_inventory"));
$f->add($check, array("value" => ''));
$rb = new RadioTpl("copy_mode");
$rb->setChoices(array(_T('push', 'msc'), _T('p/p', 'msc')));
$rb->setvalues(array('push', 'push_pull'));
$check = new TrFormElement(_T('mode', 'msc'), $rb);
$f->add($check, array("value" => ''));

$f->addValidateButton("bconfirm");
$f->addButton("badvanced", _T("Advanced", 'msc'));
$f->addCancelButton("bback");
$f->display();
#### /FORM DISPLAY HANDLING ####

?>

