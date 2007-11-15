<?

/**
 * (c) 2004-2007 Linbox / Free&ALter Soft, http://linbox.com
 *
 * $Id: cmd_state.php 24 2007-10-17 08:23:42Z nrueff $
 *
 * This file is part of LMC.
 *
 * LMC is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * LMC is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with LMC; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 */

require_once("modules/msc/includes/tmpl.inc.php");
require_once("modules/msc/includes/path.inc.php");
require_once("modules/msc/includes/system.inc.php");
require_once("modules/msc/includes/ssh.inc.php");
require_once("modules/msc/includes/widget.inc.php");
require_once("modules/msc/includes/scheduler.php");
require_once("modules/msc/includes/functions.php");
require_once("modules/msc/includes/new_widget.inc.php");

$hostname = $_GET['name'];
$total_commands_number = count_all_commands_on_host($hostname);
$cmds = get_all_commands_on_host($hostname, 0, $total_commands_number);
$a_cmd = array();
$a_uploaded = array();
$a_executed = array();
$a_deleted  = array();
$a_current  = array();
$params = array();

$actionplay = new ActionPopupItem(_T("Start", "msc"),"msctabsplay","start","msc", "base", "computers");
$actionpause = new ActionPopupItem(_T("Pause", "msc"),"msctabspause","pause","msc", "base", "computers");
$actionstop = new ActionPopupItem(_T("Stop", "msc"),"msctabsstop","stop","msc", "base", "computers");
$actiondetails = new ActionItem(_T("Details", "msc"),"msctabs","detail","msc", "base", "computers");
$actionempty = new EmptyActionItem();
$a_start = array();
$a_pause = array();
$a_stop = array();
$a_details = array();

foreach ($cmds as $cmd) {
    $coh_id = $cmd['id_command_on_host'];
    if (($_GET['coh_id'] && $coh_id == $_GET['coh_id']) || !$_GET['coh_id']) {
        $coh = get_commands_on_host($coh_id);
        if ($coh['current_state'] != 'done') {
            $a_cmd[] = $cmd['title'];
            $a_uploaded[] ='<img alt="'.$coh['uploaded'].'" src="modules/msc/graph/images/'.return_icon($coh['uploaded']).'"/> '.$coh['uploaded'];
            $a_executed[] ='<img alt="'.$coh['executed'].'" src="modules/msc/graph/images/'.return_icon($coh['executed']).'"/> '.$coh['executed'];
            $a_deleted[] = '<img alt="'.$coh['deleted'].'" src="modules/msc/graph/images/'.return_icon($coh['deleted']).'"/> '.$coh['deleted'];
            $a_current[] = $coh['current_state'];
            $params[] = array('coh_id'=>$coh_id, 'cmd_id'=>$cmd['id_command'], 'tab'=>'tablogs', 'name'=>$hostname, 'from'=>'base|computers|msctabs|tablogs');


            $icons = state_tmpl($coh['current_state']);
            if ($icons['play'] == '') { $a_start[] = $actionempty; } else { $a_start[] = $actionplay; }
            if ($icons['stop'] == '') { $a_stop[] = $actionempty; } else { $a_stop[] = $actionstop; }
            if ($icons['pause'] == '') { $a_pause[] = $actionempty; } else { $a_pause[] = $actionpause; }
        }
        if ($_GET['coh_id'] && $coh_id == $_GET['coh_id']) {
            $a_details[] = $actionempty;
        } else {
            $a_details[] = $actiondetails;
        }
    }
}


$n = new ListInfos($a_cmd, _T("Command"));
$n->addExtraInfo($a_current, _T("current_state"));
$n->addExtraInfo($a_uploaded, _T("uploaded"));
$n->addExtraInfo($a_executed, _T("executed"));
$n->addExtraInfo($a_deleted, _T("deleted"));

$n->setParamInfo($params);

$n->addActionItemArray($a_details);
$n->addActionItemArray($a_start);
//$n->addActionItemArray($a_pause);
$n->addActionItemArray($a_stop);

$n->drawTable(0);

// bottom of the page : details for the command if coh_id is specified
if ($_GET['coh_id']) {
    print "<hr/><br/>";
    $coh_id = $_GET['coh_id'];
    $ch = new CommandHistory($coh_id);
    $ch->display();
}
  
?>

<style>
li.detail a {
        padding: 3px 0px 5px 20px;
        margin: 0 0px 0 0px;
        background-image: url("modules/msc/graph/images/actions/info.png");
        background-repeat: no-repeat;
        background-position: left top;
        line-height: 18px;
        text-decoration: none;
        color: #FFF;
}
li.stop a {
        padding: 3px 0px 5px 20px;
        margin: 0 0px 0 0px;
        background-image: url("modules/msc/graph/images/stock_media-stop.png");
        background-repeat: no-repeat;
        background-position: left top;
        line-height: 18px;
        text-decoration: none;
        color: #FFF;
}
li.pause a {
        padding: 3px 0px 5px 20px;
        margin: 0 0px 0 0px;
        background-image: url("modules/msc/graph/images/stock_media-pause.png");
        background-repeat: no-repeat;
        background-position: left top;
        line-height: 18px;
        text-decoration: none;
        color: #FFF;
}

li.start a {
        padding: 3px 0px 5px 20px;
        margin: 0 0px 0 0px;
        background-image: url("modules/msc/graph/images/stock_media-play.png");
        background-repeat: no-repeat;
        background-position: left top;
        line-height: 18px;
        text-decoration: none;
        color: #FFF;
}

</style>
