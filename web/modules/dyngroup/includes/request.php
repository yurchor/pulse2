<?php
/**
 * (c) 2004-2007 Linbox / Free&ALter Soft, http://linbox.com
 * (c) 2007 Mandriva, http://www.mandriva.com
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

function parse_request($str) {
    $req = new Request();
    $req->parse($str);
    return $req;
}

function parse_subrequest($str) {
    $sub = new SubRequest();
    $sub->parse($str);
    return $sub;
}

class Request {
    function Request() {
        $this->subs = array();
        $this->nextSubId = 1;
    }
    function isEmpty() {
        return (count($this->subs) == 0);
    }
    function addSub($sub) {
        $sub->id = $this->nextSubId++;
        $this->subs[$sub->id] = $sub;
        return $sub->id;
    }
    function removeSub($id) {
        unset($this->subs[$id]);
    }
    function getSub($id) {
        return $this->subs[$id];
    }
    function toS() {
        return implode('||', array_map('to_s', $this->subs));
    }
    function toURL() {
        return urlencode($this->toS());
    }
    function toRPC() {
        return array_map('to_rpc', $this->subs);
    }
    function countPart() {
        return count($this->subs);
    }
    function parse($str) {
        $a_reqs = explode('||', $str);
        $this->subs = array();
        foreach ($a_reqs as $req) {
            $sub = parse_subrequest($req);
            $sub->id = $this->nextSubId++;
            $this->subs[$sub->id] = $sub;
        }
    }
    function display() {
        $ret = array();
        foreach ($this->subs as $id => $sub) {
            $ret[]= $sub->display();
        }
        return $ret;
    }
    function displayReqListInfos($canbedeleted = false, $default_params = array()) {
        if (!$default_params['target']) {
            $default_params['target'] = 'creator';
        }
        $parameters = array();
        $parts = array();
        foreach ($this->subs as $id => $sub) {
            array_push($parts, $sub->display());
            $p = $default_params;
            $p['delete'] = $id;
            $p['request'] = $this->toS();
            array_push($parameters, $p);
        }
        $n = new ListInfos($parts, _T('Search part', 'dyngroup'));
        if ($canbedeleted) {
            $n->setParamInfo($parameters);
            $n->addActionItem(new ActionItem(_T("Delete", 'dyngroup'), $default_params['target'], "delete", "params"));
        }

        $n->disableFirstColumnActionLink();
        $n->display();
        print "<br/>"; // or the previous/next will be on the next line...
    }
}

class SubRequest {
    function SubRequest($module = null, $criterion = null, $value = null, $value2 = null) {
        $this->module = $module;
        $this->crit = $criterion;
        $this->val = $value;
        if ($value2) {
            $this->val = array($value, $value2);
        }
        $this->id = null;
    }
    function toS() {
        if (is_array($this->val)) {
            return $this->id."==".$this->module."::".$this->crit."==(".implode(', ', $this->val).")";
        } else {
            return $this->id."==".$this->module."::".$this->crit."==".$this->val;
        }
    }
    function toURL() {
        return urlencode($this->toS());
    }
    function toRPC() {
        return array($this->id, $this->module, $this->crit, $this->val);
    }
    function display() {
        if (is_array($this->val)) {
            return sprintf(_T("%s) Search %s = (%s) in module %s", "dyngroup"), $this->id, $this->crit, implode(', ', $this->val), $this->module);
        } else {
            return sprintf(_T("%s) Search %s = %s in module %s", "dyngroup"), $this->id, $this->crit, $this->val, $this->module);
        }
    }
    function parse($str) {
        $a = explode('::', $str);
        $b = explode('==', $a[0]);
        $c = explode('==', $a[1]);
        $this->id = $b[0];
        $this->module = $b[1];
        $this->crit = $c[0];
        $this->val = explode(', ', rtrim(ltrim($c[1], '('), ')'));
        #$this->val = explode(', ', $c[1]);
        if (is_array($this->val) && count($this->val) == 1) {
            $this->val = $this->val[0];
        }
    }
}

?>
