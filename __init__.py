# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DN_Corrector
                                 A QGIS plugin
 This plugin identifies and correct errors of connection on radial electrical distribution networks
                             -------------------
        begin                : 2017-02-28
        copyright            : (C) 2017 by UCR, EPERLab, Abdenago Guzmán L
        email                : Abdenago.guzman@ucr.ac.cr
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load DN_Corrector class from file DN_Corrector.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .DN_Corrector import DN_Corrector
    return DN_Corrector(iface)
