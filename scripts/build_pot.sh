#!/bin/sh
#
# (c) 2004-2007 Linbox / Free&ALter Soft, http://linbox.com
# (c) 2007-2010 Mandriva, http://www.mandriva.com
#
# $Id$
#
# This file is part of Mandriva Management Console (MMC).
#
# MMC is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# MMC is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with MMC.  If not, see <http://www.gnu.org/licenses/>.

for POT_D in `find . -name "locale" -type d`; do
    POT_D=`dirname "$POT_D"`
    POT_N=`basename "$POT_D"`
    POT="$POT_D/locale/$POT_N.pot"

    rm -f ${POT}
    touch ${POT}
    find "$POT_D" -iname "*.php" -exec xgettext --join-existing --output=${POT} --language=PHP --keyword=_T {} \;
    for name in `find ${POT_D} -type f -name *.po`; do
        echo -n "updating ${name}..."
        msgmerge --update --add-location --sort-output --quiet --no-wrap ${name} ${POT}
        echo "done"
    done
done
exit 0
