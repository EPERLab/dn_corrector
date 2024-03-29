# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DN_CorrectorDialog
                                 A QGIS plugin
 This plugin identifies and correct errors of connection on radial electrical distribution networks
                             -------------------
        begin                : 2017-02-28
        git sha              : $Format:%H$
        copyright            : (C) 2017 by UCR, EPERLab, Abdenago Guzmán L
        email                : Abdenago.guzman@ucr.ac.cr
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from qgis.PyQt import QtGui, uic
from PyQt5.QtWidgets import QDialog

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'DN_Corrector_dialog_base.ui'))


class DN_CorrectorDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(DN_CorrectorDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
