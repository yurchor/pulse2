--
-- (c) 2016 Siveo, http://siveo.net/
--
-- $Id$
--
-- This file is part of Pulse 2, http://siveo.net
--
-- Pulse 2 is free software; you can redistribute it and/or modify
-- it under the terms of the GNU General Public License as published by
-- the Free Software Foundation; either version 2 of the License, or
-- (at your option) any later version.
--
-- Pulse 2 is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU General Public License for more details.
--
-- You should have received a copy of the GNU General Public License
-- along with Pulse 2; if not, write to the Free Software
-- Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
-- MA 02110-1301, USA.

SET SESSION character_set_server=UTF8;
SET NAMES 'utf8';

-- Add new parameter ##PULSE2_DAVOS_OPTS## for boot services using davos
UPDATE BootService SET default_name = 'backup', default_desc = 'Create a Backup', value = 'KERNEL ../##PULSE2_DISKLESS_DIR##/##PULSE2_DISKLESS_KERNEL##\nAPPEND ##PULSE2_KERNEL_OPTS## ##PULSE2_REVO_RAW## ##PULSE2_DISKLESS_OPTS## davos_action=SAVE_IMAGE ##PULSE2_DAVOS_OPTS##\nINITRD ../##PULSE2_DISKLESS_DIR##/##PULSE2_DISKLESS_INITRD##' WHERE id = 3;
UPDATE BootService SET default_name = 'diskless', default_desc = 'Diskless Boot', value = 'KERNEL ../##PULSE2_DISKLESS_DIR##/##PULSE2_DISKLESS_KERNEL## ##PULSE2_KERNEL_OPTS## ##PULSE2_DISKLESS_OPTS## davos_debug=i ##PULSE2_DAVOS_OPTS##\nINITRD ../##PULSE2_DISKLESS_DIR##/##PULSE2_DISKLESS_INITRD##' where id='4';

UPDATE version set Number = 13;
