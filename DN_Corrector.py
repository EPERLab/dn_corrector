# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DN_Corrector
                                 A QGIS plugin
 This plugin identifies and correct errors of connection on radial electrical distribution networks
                              -------------------
        begin                : 2017-02-28
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Abdenago Guzman L.
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
from __future__ import print_function
from __future__ import absolute_import
from builtins import str
from builtins import range
from builtins import object
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qgis.core import * #QgsMapLayerRegistry, QgsVectorDataProvider, QgsField
from qgis.gui import QgsMessageBar
import time
from qgis.PyQt.QtWidgets import QProgressBar
from PyQt5 import QtCore 

from PyQt5 import QtGui #Paquetes requeridos para crear ventanas de diálogo e interfaz gráfica.
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog, QMessageBox, QDialog, QStyleFactory, QAction
import traceback

#from qgis2opendss_progress import Ui_Progress


# Initialize Qt resources from file resources.py
from . import resources
# Import the code for the dialog
from .DN_Corrector_dialog import DN_CorrectorDialog
import os.path
from . import func_connector


from random import randint
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import time
import math


class DN_Corrector(object):
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'DN_Corrector_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)


        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&DN Corrector')
                # Create the dialog (after translation) and keep reference
        self.dlg = DN_CorrectorDialog()
        #self.progress = Ui_Progress()
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'DN_Corrector')
        self.toolbar.setObjectName(u'DN_Corrector')
        self.dlg.pushButton_incons_BT.clicked.connect(self.reporteInconsis)
        self.dlg.pushButton_incons_MT.clicked.connect(self.inconsistencias_MT)
        self.dlg.pushButton_traf.clicked.connect(self.trafConec)
        self.dlg.pushButton_cargas.clicked.connect(self.loadConec)
        self.dlg.pushButton_lines.clicked.connect(self.lineConec)
        self.dlg.pushButton_split.clicked.connect(self.split_iteration)
        self.dlg.button_box.helpRequested.connect(self.show_help)
        self.output_folder = ""
        
        self.dlg.pushButton_output_folder.clicked.connect(self.select_output_folder)
        
        self.tolerance = 0.1
    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('DN_Corrector', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """



        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/DN_Corrector/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Connection of distribution network elements'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&DN Corrector'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
        
    def show_help(self):
        """Display application help to the user."""
      
        help_file = 'file:///%s/help/Manual_DNCorrector_ESP.pdf' % self.plugin_dir        
        QDesktopServices.openUrl(QUrl(help_file))
        
     
        """Get a list of all the layers.      
        
        :returns: A list of the layers
        :rtype: list
        """

    def readerLayers(self):
        Index_line_MT_1 = self.dlg.layerComboBox_aerea_MT_1.currentIndex()
        Index_line_MT_2 = self.dlg.layerComboBox_aerea_MT_2.currentIndex()
        Index_line_MT_3 = self.dlg.layerComboBox_aerea_MT_3.currentIndex()
        
        
        Index_carga_MT_1 = self.dlg.layerComboBox_carga_MT_1.currentIndex()
        Index_carga_MT_2 = self.dlg.layerComboBox_carga_MT_2.currentIndex()
        Index_carga_MT_3 = self.dlg.layerComboBox_carga_MT_3.currentIndex()
        
        Index_trafo_1 = self.dlg.layerComboBox_trafo_1.currentIndex()
        Index_trafo_2 = self.dlg.layerComboBox_trafo_2.currentIndex()
        Index_trafo_3 = self.dlg.layerComboBox_trafo_3.currentIndex()

        Index_line_BT_1 = self.dlg.layerComboBox_aer_1.currentIndex()
        Index_line_BT_2 = self.dlg.layerComboBox_aer_2.currentIndex()
        Index_line_BT_3 = self.dlg.layerComboBox_aer_3.currentIndex()
                
        Index_Carga_1 = self.dlg.layerComboBox_Carga_1.currentIndex()
        Index_Carga_2 = self.dlg.layerComboBox_Carga_2.currentIndex()
        Index_Carga_3 = self.dlg.layerComboBox_Carga_3.currentIndex()

        Index_acometida_1 = self.dlg.layerComboBox_acometida_1.currentIndex()
        Index_acometida_2 = self.dlg.layerComboBox_acometida_2.currentIndex()
        Index_acometida_3 = self.dlg.layerComboBox_acometida_3.currentIndex()
######
        layers_line_MT = [] 
        if Index_line_MT_1 != 0:
            Name_line_MT_1 = self.dlg.layerComboBox_aerea_MT_1.currentText()
            #print( "Name_line_MT_1 = ", Name_line_MT_1 )
            layers_line_MT.append(QgsProject.instance().mapLayersByName(Name_line_MT_1))#[0]
        if Index_line_MT_2 != 0:
            Name_line_MT_2 = self.dlg.layerComboBox_aerea_MT_2.currentText()
            layers_line_MT.append(QgsProject.instance().mapLayersByName(Name_line_MT_2))#[0]
        if Index_line_MT_3 != 0:
            Name_line_MT_3 = self.dlg.layerComboBox_aerea_MT_3.currentText()
            layers_line_MT.append(QgsProject.instance().mapLayersByName(Name_line_MT_3))#[0]

            
        layers_carga_MT=[]
        if Index_carga_MT_1 != 0:
            Name_carga_MT_1 = self.dlg.layerComboBox_carga_MT_1.currentText()
            layers_carga_MT.append(QgsProject.instance().mapLayersByName(Name_carga_MT_1))#[0]
        if Index_carga_MT_2 != 0:
            Name_carga_MT_2 = self.dlg.layerComboBox_carga_MT_2.currentText()
            layers_carga_MT.append(QgsProject.instance().mapLayersByName(Name_carga_MT_2))#[0]
        if Index_carga_MT_3 != 0:
            Name_carga_MT_3 = self.dlg.layerComboBox_carga_MT_3.currentText()
            layers_carga_MT.append(QgsProject.instance().mapLayersByName(Name_carga_MT_3))#[0]
        
        layers_trafo=[]
        if Index_trafo_1 != 0:
            Name_trafo_1 = self.dlg.layerComboBox_trafo_1.currentText()
            layers_trafo.append(QgsProject.instance().mapLayersByName(Name_trafo_1))#[0]
        if Index_trafo_2 != 0:
            Name_trafo_2 = self.dlg.layerComboBox_trafo_2.currentText()
            layers_trafo.append(QgsProject.instance().mapLayersByName(Name_trafo_2))#[0]
        if Index_trafo_3 != 0:
            Name_trafo_3 = self.dlg.layerComboBox_trafo_3.currentText()
            layers_trafo.append(QgsProject.instance().mapLayersByName(Name_trafo_3))#[0]
          
        layers_line_BT=[]
        if Index_line_BT_1 != 0:
            Name_line_BT_1 = self.dlg.layerComboBox_aer_1.currentText()
            layers_line_BT.append(QgsProject.instance().mapLayersByName(Name_line_BT_1))#[0]
        if Index_line_BT_2 != 0:
            Name_line_BT_2 = self.dlg.layerComboBox_aer_2.currentText()
            layers_line_BT.append(QgsProject.instance().mapLayersByName(Name_line_BT_2))#[0]
        if Index_line_BT_3 != 0:
            Name_line_BT_3 = self.dlg.layerComboBox_aer_3.currentText()
            layers_line_BT.append(QgsProject.instance().mapLayersByName(Name_line_BT_3))#[0]
        

        layers_acometida=[]
        if Index_acometida_1 != 0:
            Name_acometida_1 = self.dlg.layerComboBox_acometida_1.currentText()
            layers_acometida.append(QgsProject.instance().mapLayersByName(Name_acometida_1))#[0]
        if Index_acometida_2 != 0:
            Name_acometida_2 = self.dlg.layerComboBox_acometida_2.currentText()
            layers_acometida.append(QgsProject.instance().mapLayersByName(Name_acometida_2))#[0]
        if Index_acometida_3 != 0:
            Name_acometida_3 = self.dlg.layerComboBox_acometida_3.currentText()
            layers_acometida.append(QgsProject.instance().mapLayersByName(Name_acometida_3))#[0]
            
        layers_Carga=[]
        if Index_Carga_1 != 0:
            Name_Carga_1 = self.dlg.layerComboBox_Carga_1.currentText()
            layers_Carga.append(QgsProject.instance().mapLayersByName(Name_Carga_1))#[0]
        if Index_Carga_2 != 0:
            Name_Carga_2 = self.dlg.layerComboBox_Carga_2.currentText()
            layers_Carga.append(QgsProject.instance().mapLayersByName(Name_Carga_2))#[0]
        if Index_Carga_3 != 0:
            Name_Carga_3 = self.dlg.layerComboBox_Carga_3.currentText()
            layers_Carga.append(QgsProject.instance().mapLayersByName(Name_Carga_3))#[0] 
        
        inputLayers = {"MT_lines":layers_line_MT,"carga_MT":layers_carga_MT, "trafos": layers_trafo, "BT_lines":layers_line_BT,"acometida": layers_acometida, "carga_BT":layers_Carga}
        
        return inputLayers
        

    def attributeUpdateLines(self, layer):
        layer.startEditing()
        X1Index = layer.fields().indexFromName("X1")
        Y1Index = layer.fields().indexFromName("Y1")
        X2Index = layer.fields().indexFromName("X2")
        Y2Index = layer.fields().indexFromName("Y2")
        for obj in layer.getFeatures():
            geom = obj.geometry()
            line = self.MultiStringToMatrix(geom)
			            
            n = len(line)
            x1= line[0][0]
            y1=line[0][1]
            x2=line[n-1][0]
            y2=line[n-1][1]
            layer.changeAttributeValue(obj.id(), X1Index, x1)
            layer.changeAttributeValue(obj.id(), Y1Index, y1)
            layer.changeAttributeValue(obj.id(), X2Index, x2)
            layer.changeAttributeValue(obj.id(), Y2Index, Y2)
    def attributeUpdatePoints(self, layer):
        layer.startEditing()
        XIndex = layer.fields().indexFromName("X1")
        YIndex = layer.fields().indexFromName("Y1")
        for feat in layer.getFeatures():
            point = feat.geometry().asPoint()
            x = point[0]
            y = point[1]
            layer.changeAttributeValue(feat.id(), XIndex, x)
            layer.changeAttributeValue(feat.id(), YIndex, y)
            
    def getAttributeIndex(self, aLayer, attrName): # Crea el atributo y obtiene el ID
        """Find the attribute index, adding a new Int column, if necessary"""
        
        """
        if len(attrName) > 10 and aLayer.storageType() == 'ESRI Shapefile':
            self.iface.messageBar().pushCritical("Error", "For ESRI Shapefiles, the maximum length of any attribute name is 10. Please choose a shorter attribute name.")
            return -3
        """
        AttrIdx = aLayer.dataProvider().fieldNameIndex(attrName)
        
        if AttrIdx == -1: # attribute doesn't exist, so create it
            caps = aLayer.dataProvider().capabilities()
            if caps & QgsVectorDataProvider.AddAttributes:
                res = aLayer.dataProvider().addAttributes([QgsField(attrName, QVariant.Int)])

                AttrIdx = aLayer.dataProvider().fieldNameIndex(attrName)
                aLayer.updateFields()
                if AttrIdx == -1:
                    self.iface.messageBar().pushCritical("Error", "Failed to create attribute!")
                    return -1
            else:
                self.iface.messageBar().pushCritical("Error", "Failed to add attribute!")
                return -1
        else:
            pass
        return AttrIdx
 
    def changeGroupValue(self, layerlist, islandList):
        for LayerX in layerlist: 
                layer = LayerX[0]
                layer.startEditing()
        for (data1, data2) in list(islandList.items()):
            idx = data1[0]
            idlayer = data1[1]
            attId = data2["attIndx"]
            group = data2["GROUP"]
            donea = layerlist[idlayer][0].changeAttributeValue(idx, attId, group)
        for LayerX in layerlist: 
            layer = LayerX[0]
            layer.commitChanges()
    def ringRender(self, layerList):
        for layerX in layerList:
            layer = layerX[0]
            layer.beginEditCommand("Update layer styling")
            categories = []
            firstCat = True
            idx = layer.fields().indexFromName('RING')
            values = layer.uniqueValues(idx)
            for cat in values:
                if cat == -1:
                    color = QColor(10, 44, 236)
                    widthLineMult=1
                else:
                    color = QColor(236, 10, 10)
                    widthLineMult=3
               
                symbol = QgsSymbol.defaultSymbol(layer.geometryType())
                symbol.setColor(color)
                symbol.setWidth(symbol.width()*widthLineMult)
                category = QgsRendererCategory(cat, symbol, str(cat))#"%d" % 
                categories.append(category)

            field = 'RING'
            renderer = QgsCategorizedSymbolRenderer(field, categories)
            layer.setRenderer(renderer)
            layer.triggerRepaint()
            layer.endEditCommand()
            
    def inconsistencias_MT(self):
        inputLayers = self.readerLayers()
        line_MT_Layers = inputLayers["MT_lines"]
        carga_MT_Layers = inputLayers["carga_MT"]
        trafo_MT_Layers = inputLayers["trafos"]
        if len(line_MT_Layers) == 0:
            QMessageBox.critical(None,"DN Corrector","Debe seleccionar al menos una capa de lineas de MT")
        else:
            ##### Establece la tolerancia para reconocer uniones entre segmentos
            tolerance = self.dlg.toleranceSpinBox.value()
            if tolerance == 0:
                tolerance = self.tolerance
            GrafoMT = nx.Graph()
            GrafoLMT = nx.Graph()
            GrafoTrafosMT = nx.Graph()
            GrafoLoadMT = nx.Graph()
            
            indexLayer=0
            for aereaMTLayerX in line_MT_Layers: #Si la lista de capas esta vacia no entra al ciclo, por lo que no es necesario un IF
                aereaMTLayer = aereaMTLayerX[0]
                aereaMTLayer.startEditing()
                MTAerAttrIdx = self.getAttributeIndex(aereaMTLayer, 'RING')
                MTAerAttrIdxConnect = self.getAttributeIndex(aereaMTLayer, 'MV_GROUP')
                for feat in aereaMTLayer.getFeatures():
                    done = aereaMTLayer.changeAttributeValue(feat.id(), MTAerAttrIdx, -1)
                    done = aereaMTLayer.changeAttributeValue(feat.id(), MTAerAttrIdxConnect, -1)
                    #try:
                    
                    geom = feat.geometry()
                    line = self.MultiStringToMatrix(geom)
                    if line == []:
                        message =  "Error al leer la geometrìa. Se ha finalizado el programa."
                        QMessageBox.warning(None, QCoreApplication.translate('dialog', u'REGISTRO DE INCONSISTENCIAS'), message)
                        return
           
                    
                    n= len(line)
                    
                    if self.dlg.checkBox_intNodes.isChecked(): 
                        for i in range(len(line)-1):
                            if int(line[i][0]/tolerance) == int(line[i+1][0]/tolerance) and int(line[i][1]/tolerance) == int(line[i+1][1]/tolerance):
                                continue
                            GrafoMT.add_edges_from([((int(line[i][0]/tolerance), int(line[i][1]/tolerance)), (int(line[i+1][0]/tolerance), int(line[i+1][1]/tolerance)),
                            {"attIndexGroup":MTAerAttrIdxConnect, "ringAttIndex":MTAerAttrIdx, 'fid': feat.id(), 'element': 'lineMT', "FEAT":feat, "idLAYER": indexLayer})])     # first scale by tolerance, then convert to int.  Before doing this, there were problems with floats not equating, thus creating disconnects that weren't there.
                            GrafoLMT.add_edges_from([((int(line[i][0]/tolerance), int(line[i][1]/tolerance)), (int(line[i+1][0]/tolerance), int(line[i+1][1]/tolerance)),
                            {"attIndexGroup":MTAerAttrIdxConnect, "ringAttIndex":MTAerAttrIdx, 'fid': feat.id(), 'element': 'lineMT', "FEAT":feat, "idLAYER": indexLayer})])
                    else:
                        GrafoMT.add_edges_from([((int(line[0][0]/tolerance), int(line[0][1]/tolerance)), (int(line[n-1][0]/tolerance), int(line[n-1][1]/tolerance)),
                        {"attIndexGroup":MTAerAttrIdxConnect, "ringAttIndex":MTAerAttrIdx, 'fid': feat.id(), 'element': 'lineMT', "FEAT":feat, "idLAYER": indexLayer})])     # first scale by tolerance, then convert to int.  Before doing this, there were problems with floats not equating, thus creating disconnects that weren't there.
                        GrafoLMT.add_edges_from([((int(line[0][0]/tolerance), int(line[0][1]/tolerance)), (int(line[n-1][0]/tolerance), int(line[n-1][1]/tolerance)),
                        {"attIndexGroup":MTAerAttrIdxConnect, "ringAttIndex":MTAerAttrIdx, 'fid': feat.id(), 'element': 'lineMT', "FEAT":feat, "idLAYER": indexLayer})])
                indexLayer +=1
                aereaMTLayer.endEditCommand()

            indexLayer = 0
            for cargaMTLayerX in carga_MT_Layers:
                cargaMTLayer = cargaMTLayerX[0]
                cargaMTLayer.startEditing()
                MTCargaAttrIdxConnect = self.getAttributeIndex(cargaMTLayer, 'MV_GROUP')
                for feat in cargaMTLayer.getFeatures():
                    done = cargaMTLayer.changeAttributeValue(feat.id(), MTCargaAttrIdxConnect, -1)
                    point = feat.geometry().asPoint()
                    x = int(point[0]/tolerance)
                    y = int(point[1]/tolerance)
                    p = (x, y)
                    GrafoMT.add_node(p)
                    GrafoMT.nodes[p].update( {'fid': feat.id(), 'element': 'cargaMT', "FEAT":feat, "LAYER": indexLayer, "attIndexGroup":MTCargaAttrIdxConnect} )
                    
                    GrafoLoadMT.add_node(p)
                    GrafoLoadMT.nodes[p].update( {'fid': feat.id(), "FEAT":feat, "LAYER": indexLayer, "attIndexGroup":MTCargaAttrIdxConnect} )
                indexLayer +=1
                cargaMTLayer.endEditCommand()
                
            indexLayer = 0
            for trafoLayerX in trafo_MT_Layers:
                trafoLayer = trafoLayerX[0]
                trafoLayer.startEditing()
                trafoLayer.beginEditCommand("Update group attribute")
                TrafLayerEditingMode = True
                trafoAttrIdxConnect = self.getAttributeIndex(trafoLayer, 'MV_GROUP')
                for feat in trafoLayer.getFeatures():
                    done = trafoLayer.changeAttributeValue(feat.id(), trafoAttrIdxConnect, -1)
                    point = feat.geometry().asPoint()
                    x = int(point[0]/tolerance)
                    y = int(point[1]/tolerance)
                    p = (x, y)
                    GrafoMT.add_node(p)
                    GrafoMT.nodes[p].update( {'fid': feat.id(), 'element': 'trafo', "FEAT":feat, "LAYER": indexLayer, "attIndexGroup":trafoAttrIdxConnect} )
                    
                    GrafoTrafosMT.add_node(p)
                    GrafoTrafosMT.nodes[p].update( {'fid': feat.id(), 'element': 'trafo', "FEAT":feat, "LAYER": indexLayer, "attIndexGroup":trafoAttrIdxConnect} )
                indexLayer +=1
                trafoLayer.endEditCommand()
                
            anillos = nx.cycle_basis(GrafoMT)
            
            if len(anillos)==0:
                message =  "No existen anillos en la red de MT"                
            else:
                message =  "Existen "+ str(len(anillos))+ " anillos en la red de MT"          

                
                N=1
                for anillo in anillos:
                    idlayer = GrafoMT[anillo[0]][anillo[len(anillo)-1]]["idLAYER"]
                    AttrIdx = GrafoMT[anillo[0]][anillo[len(anillo)-1]]["ringAttIndex"]
                    idMTline= GrafoMT[anillo[0]][anillo[len(anillo)-1]]["fid"]
                    done = line_MT_Layers[idlayer][0].changeAttributeValue(idMTline, AttrIdx, N)

                    for i in range(len(anillo)-1):
                        idlayer = GrafoMT[anillo[i]][anillo[i+1]]["idLAYER"]
                        AttrIdx = GrafoMT[anillo[i]][anillo[i+1]]["ringAttIndex"]
                        idMTline= GrafoMT[anillo[i]][anillo[i+1]]["fid"]
                        done = line_MT_Layers[idlayer][0].changeAttributeValue(idMTline, AttrIdx, N)
                    N+=1
                ###RENDER MT LINES 
                if self.dlg.checkBox_anillos.isChecked() : 
                    self.ringRender(line_MT_Layers)
                    self.iface.mapCanvas().refresh()
                    
            Lines_Islands = {}
            trafos_Islands = {}
            cargas_Islands ={}
            
            Lines_Groups = {0:[], 1:[], 2:[]}
            trafos_Groups = []
            cargas_Groups = []
            
            connected_components_MT = list(nx.connected_component_subgraphs(GrafoMT))    # Determina cuales son los componentes conectados en baja tension
            i=1
            for graph in connected_components_MT:
                for edge in list( graph.edges(data=True) ):
                    #Lines_Islands[edge[2].get('fid', None)] = i  
                    Lines_Islands[(edge[2]["fid"], edge[2]["idLAYER"])] = {"GROUP":i,"attIndx":edge[2]["attIndexGroup"]}#    {(id, layer):{group, idGroup],....,}
                    if i not in Lines_Groups[edge[2]["idLAYER"]]:
                        Lines_Groups[edge[2]["idLAYER"]].append(i)
                for node in list( graph.nodes(data=True) ):
                    if len(node[1])!=0 and node[1]['element']=='trafo':
                        #trafos_Islands[node[1].get('fid', None)] = i  
                        trafos_Islands[(node[1]["fid"],node[1]["LAYER"])] = {"GROUP":i ,"attIndx": node[1]["attIndexGroup"]}  #  {(id, layer):{group, idGroup],....,}
                        if i not in trafos_Groups:
                            trafos_Groups.append(i)
                    if len(node[1])!=0 and node[1]['element']== 'cargaMT':
                        #cargas_Islands[node[1].get('fid', None)] = i
                        cargas_Islands[(node[1]["fid"],node[1]["LAYER"])] = {"GROUP":i , "attIndx": node[1]["attIndexGroup"]}  #  {(id, layer):{group, idGroup],....,}
                        if i not in cargas_Groups:
                            cargas_Groups.append(i)
                i+=1
            ###### Actualiza los atributos por el valor de su grupo respectivo
            
            self.changeGroupValue(line_MT_Layers, Lines_Islands)
            self.changeGroupValue(carga_MT_Layers, cargas_Islands)
            self.changeGroupValue(trafo_MT_Layers, trafos_Islands)

            ### islands render
            if self.dlg.colorCheckBox.isChecked() : 
                for i in range(len(line_MT_Layers)):
                    layer = line_MT_Layers[i][0]
                    groupsLines = Lines_Groups[i]
                    self.render(layer, groupsLines, "MV_GROUP")

            ####Reporte de inconsistencias
            MTLinesDesc =[]
            for line in Lines_Groups[0]+Lines_Groups[1]+Lines_Groups[2]:
                if (line not in trafos_Groups) and (line not in MTLinesDesc):
                    MTLinesDesc.append(line)
            
            trafoDesc =[]
            for trafo in trafos_Groups:
                if (trafo not in  Lines_Groups[0]) and (trafo not in  Lines_Groups[1])  and (trafo not in  Lines_Groups[2])  and (trafo not in trafoDesc):
                    trafoDesc.append(trafo)
                    
            cargaMTDesc =[]
            for cargas in cargas_Groups:
                if (cargas not in  Lines_Groups[0])and (cargas not in  Lines_Groups[1])  and (cargas not in  Lines_Groups[2])  and (cargas not in cargaMTDesc):
                    cargaMTDesc.append(cargas)
             
                    # #######################################
            if len(MTLinesDesc) > 0 :
                repLines = u"\nLas lineas de MT desconectadas están clasificadas en los siguientes grupos: "+str(MTLinesDesc)
            else:
                repLines = u'\nNo existen lineas de media tension desconectadas.'
                
            if len(trafoDesc) > 0 :
                repTraf = "\nLos transformadores desconectados se encuentran en los grupos de MT: " + str(trafoDesc)
            else:
                repTraf = '\nNo existen transformadores desconectados de media tension.'
            
            if len(cargaMTDesc) > 0 :
                repLoad = u"\nLas cargas de MT desconectadas están en los siguientes grupos: " + str(cargaMTDesc)
            else:
                repLoad = '\nNo existen cargas de media tension desconectadas.'
                
            msg = message + repLines + repTraf + repLoad
            filename_report = self.output_folder + "/Inconsistencias_MT.txt"
            if self.output_folder != "":
                with open(filename_report, 'w') as file_report:
                    file_report.write(msg)
            QMessageBox.warning(None, QCoreApplication.translate('dialog', u'Registro de incosistencias'), msg)
            QgsApplication.instance().messageLog().logMessage(msg, tag="REGISTRO DE INCONSISTENCIAS",level=Qgis.MessageLevel(1))
            self.iface.messageBar().pushMessage("DN_Corrector", QCoreApplication.translate('dialog', u"Se ha analizado la red de media tension, vea los mensajes de registro para ver los errores") )
            
    #Función que permite seleccionar la carpeta de salida
    def select_output_folder(self):
        self.output_folder = QFileDialog.getExistingDirectory(self.dlg, QCoreApplication.translate('dialog',
                                                                                              "Seleccione carpeta de salida"), "")
        self.dlg.lineEdit_dirOutput.setText(self.output_folder)
    def inconsistencias_BT(self):
        inputLayers = self.readerLayers()
        trafo_Layers = inputLayers["trafos"]
        line_BT_Layers = inputLayers["BT_lines"]
        acomet_Layers = inputLayers["acometida"]
        carga_BT_Layers = inputLayers["carga_BT"]
        NOGEOMETRY = False
        
##### Establece la tolerancia para reconocer uniones entre segmentos
        tolerance = self.dlg.toleranceSpinBox.value()
        if tolerance == 0:
            tolerance = self.tolerance
##### Crea un grafo vacio y le añade las lineas y nodos
        GrafoBT = nx.Graph()
        indexLayer = 0
        for trafoLayerX in trafo_Layers:
            trafoLayer = trafoLayerX[0]
            trafoLayer.startEditing()
            trafoLayer.beginEditCommand("Update group attribute")
            trafoAttrIdx = self.getAttributeIndex(trafoLayer, 'LV_GROUP')
            for feat in trafoLayer.getFeatures():
                done = trafoLayer.changeAttributeValue(feat.id(), trafoAttrIdx, 0)
                try:
                    point = feat.geometry().asPoint()
                    x = int(point[0]/tolerance)
                    y = int(point[1]/tolerance)
                    p = (x, y)
                    GrafoBT.add_node(p)
                    GrafoBT.nodes[p].update( {'fid': feat.id(), 'element': 'trafo', "FEAT":feat,"idLAYER": indexLayer, "attIndexGroup":trafoAttrIdx} )
                except:
                    Geom_Idx = self.getAttributeIndex(trafoLayer, 'NO_GEOMETRY')
                    done = trafoLayer.changeAttributeValue(feat.id(), Geom_Idx, 0)
                    NOGEOMETRY = True
                    

            trafoLayer.endEditCommand()
            indexLayer +=1
            
        indexLayer=0
        for BTLinesLayerX in line_BT_Layers: #Si la lista de capas esta vacia no entra al ciclo, por lo que no es necesario un IF
            BTLayer = BTLinesLayerX[0]
            BTLayer.startEditing()
            BTLayer.beginEditCommand("Update group attribute")
            groupAttrIdx = self.getAttributeIndex(BTLayer, 'LV_GROUP')
            ringAttrIdx = self.getAttributeIndex(BTLayer, 'RING')
            for feat in BTLayer.getFeatures():
                done = BTLayer.changeAttributeValue(feat.id(), groupAttrIdx, 0)
                done = BTLayer.changeAttributeValue(feat.id(), ringAttrIdx, 0)
                try:
                    geom = feat.geometry()
                    line = self.MultiStringToMatrix(geom)
                                        
                    n= len(line)
                    if self.dlg.checkBox_intNodes.isChecked(): 
                        for i in range(len(line)-1):
                            if int(line[i][0]/tolerance) == int(line[i+1][0]/tolerance) and int(line[i][1]/tolerance) == int(line[i+1][1]/tolerance):
                                continue
                            GrafoBT.add_edges_from([((int(line[i][0]/tolerance), int(line[i][1]/tolerance)), (int(line[i+1][0]/tolerance), int(line[i+1][1]/tolerance)),
                            {"attIndexGroup":groupAttrIdx, "ringAttIndex":ringAttrIdx, 'fid': feat.id(), 'element': 'BTLine', "FEAT":feat, "idLAYER": indexLayer})])     # first scale by tolerance, then convert to int.  Before doing this, there were problems with floats not equating, thus creating disconnects that weren't there.
                    else:
                        GrafoBT.add_edges_from([((int(line[0][0]/tolerance), int(line[0][1]/tolerance)), (int(line[n-1][0]/tolerance), int(line[n-1][1]/tolerance)),
                        {"attIndexGroup":groupAttrIdx, "ringAttIndex":ringAttrIdx, 'fid': feat.id(), 'element': 'BTLine', "FEAT":feat, "idLAYER": indexLayer})])     # first scale by tolerance, then convert to int.  Before doing this, there were problems with floats not equating, thus creating disconnects that weren't there.
                except:
                    Geom_Idx = self.getAttributeIndex(BTLayer, 'NO_GEOMETRY')
                    done = BTLayer.changeAttributeValue(feat.id(), Geom_Idx, 0)
                    NOGEOMETRY = True
            BTLayer.endEditCommand()
            indexLayer +=1
            
        indexLayer=0
        for acomLinesLayerX in acomet_Layers: #Si la lista de capas esta vacia no entra al ciclo, por lo que no es necesario un IF
            acomLayer = acomLinesLayerX[0]            
            acomLayer.startEditing()
            acomLayer.beginEditCommand("Update group attribute")
            groupAttrIdx = self.getAttributeIndex(acomLayer, 'LV_GROUP')
            ringAttrIdx = self.getAttributeIndex(acomLayer, 'RING')
            for feat in acomLayer.getFeatures():
                done = acomLayer.changeAttributeValue(feat.id(), groupAttrIdx, 0)
                done = acomLayer.changeAttributeValue(feat.id(), ringAttrIdx, 0)
                try:
                    geom = feat.geometry()
                    line = self.MultiStringToMatrix(geom)
                    
                    n= len(line)
                    if self.dlg.checkBox_intNodes.isChecked(): 
                        for i in range(len(line)-1):
                            if int(line[i][0]/tolerance) == int(line[i+1][0]/tolerance) and int(line[i][1]/tolerance) == int(line[i+1][1]/tolerance):
                                continue
                            GrafoBT.add_edges_from([((int(line[i][0]/tolerance), int(line[i][1]/tolerance)), (int(line[i+1][0]/tolerance), int(line[i+1][1]/tolerance)),
                            {"attIndexGroup":groupAttrIdx, "ringAttIndex":ringAttrIdx, 'fid': feat.id(), 'element': 'acom', "FEAT":feat, "idLAYER": indexLayer})])     # first scale by tolerance, then convert to int.  Before doing this, there were problems with floats not equating, thus creating disconnects that weren't there.
                    else:
                        GrafoBT.add_edges_from([((int(line[0][0]/tolerance), int(line[0][1]/tolerance)), (int(line[n-1][0]/tolerance), int(line[n-1][1]/tolerance)),
                        {"attIndexGroup":groupAttrIdx, "ringAttIndex":ringAttrIdx, 'fid': feat.id(), 'element': 'acom', "FEAT":feat, "idLAYER": indexLayer})])     # first scale by tolerance, then convert to int.  Before doing this, there were problems with floats not equating, thus creating disconnects that weren't there.
                except:
                    Geom_Idx = self.getAttributeIndex(acomLayer, 'NO_GEOMETRY')
                    done = acomLayer.changeAttributeValue(feat.id(), Geom_Idx, 0)
                    NOGEOMETRY = True
            acomLayer.endEditCommand()
            indexLayer +=1
            
        indexLayer = 0
        for cargaLayerX in carga_BT_Layers:
            cargaLayer = cargaLayerX[0]
            cargaLayer.startEditing()
            cargaLayer.beginEditCommand("Update group attribute")
            groupAttrIdx = self.getAttributeIndex(cargaLayer, 'LV_GROUP')
            for feat in cargaLayer.getFeatures():
                done = cargaLayer.changeAttributeValue(feat.id(), groupAttrIdx, 0)
                try:
                    point = feat.geometry().asPoint()
                    x = int(point[0]/tolerance)
                    y = int(point[1]/tolerance)
                    p = (x, y)
                    GrafoBT.add_node(p)
                    GrafoBT.nodes[p].update( {"attIndexGroup":groupAttrIdx, 'fid': feat.id(), 'element': 'carga', "FEAT":feat, "idLAYER": indexLayer} )
                except:
                    Geom_Idx = self.getAttributeIndex(cargaLayer, 'NO_GEOMETRY')
                    done = cargaLayer.changeAttributeValue(feat.id(), Geom_Idx, 0)
                    NOGEOMETRY = True
            cargaLayer.endEditCommand()
            indexLayer +=1
                
############################################################################

        connected_components_BT = list(nx.connected_component_subgraphs(GrafoBT))    # Determina cuales son los componentes conectados en baja tension

        trafo_group = {0:[], 1:[], 2:[]}
        BT_lines_group = {0:[], 1:[], 2:[]}
        aco_group = {0:[], 1:[], 2:[]}
        carga_group = {0:[], 1:[], 2:[]}
        
        lines_BT_Islands = {}   #{(id, layer):{group, idGroup],....,}
        lines_acom_Islands = {}       #{(id, layer):{group, idGroup],....,}
        trafos_islands = {}     #{(id, layer):{group, idGroup],....,}
        loads_islands ={}      #{(id, layer):{group, idGroup],....,}
        
        trafoCount = []
        i = 1
        for graph in connected_components_BT:
            for edge in list( graph.edges(data=True) ):
                if edge[2]['element'] == 'BTLine':
                    lines_BT_Islands[(edge[2]["fid"], edge[2]["idLAYER"])] = {"GROUP": i,"attIndx":edge[2]["attIndexGroup"]}
                    if i not in BT_lines_group[edge[2]["idLAYER"]]:
                        BT_lines_group[edge[2]["idLAYER"]].append(i)

                if edge[2]['element']== 'acom':
                    lines_acom_Islands[(edge[2]["fid"], edge[2]["idLAYER"])] = {"GROUP":i,"attIndx":edge[2]["attIndexGroup"]}
                    if i not in aco_group[edge[2]["idLAYER"]]:
                        aco_group[edge[2]["idLAYER"]].append(i)
                    
            for node in list( graph.nodes(data=True) ):
                if len(node[1])!=0 and node[1]['element']=='trafo':
                    trafos_islands[(node[1]["fid"],node[1]["idLAYER"])] = {"GROUP":i ,"attIndx": node[1]["attIndexGroup"]}
                    trafoCount.append(i)
                    if i not in trafo_group[node[1]["idLAYER"]]:
                        trafo_group[node[1]["idLAYER"]].append(i)
                    
                if len(node[1])!=0 and node[1]['element']== 'carga':
                    loads_islands[(node[1]["fid"],node[1]["idLAYER"])] = {"GROUP":i ,"attIndx": node[1]["attIndexGroup"]}
                    if i not in carga_group[node[1]["idLAYER"]]:
                        carga_group[node[1]["idLAYER"]].append(i)
            i += 1

################################################################## Actualiza los atributos por el valor de su grupo respectivo
        
        self.changeGroupValue(trafo_Layers, trafos_islands)
        self.changeGroupValue(line_BT_Layers, lines_BT_Islands)
        self.changeGroupValue(acomet_Layers, lines_acom_Islands)
        self.changeGroupValue(carga_BT_Layers, loads_islands)
#####################################Reporte de inconsistencias

        linesGroupTotalList = BT_lines_group[0]+BT_lines_group[1]+BT_lines_group[2]+aco_group[0]+aco_group[1]+aco_group[2]
        trafodGroupTotalList = trafo_group[0] + trafo_group[1] + trafo_group[2]
        
        cargaDesc = {0:[], 1:[], 2:[]}

        for i in range(len(carga_BT_Layers)):
            for group in carga_group[i]:
                if (group not in linesGroupTotalList):
                    cargaDesc[i].append(group)
                
        trafoDesc = {0:[], 1:[], 2:[]}
        for i in range(len(trafo_Layers)):
            for group in trafo_group[i]:
                if (group not in linesGroupTotalList):
                    trafoDesc[i].append(group)
        
        BTDesc = {0:[], 1:[], 2:[]}
        for i in range(len(line_BT_Layers)):
            for group in BT_lines_group[i]:
                if (group not in trafodGroupTotalList):
                    BTDesc[i].append(group)
        
        acoDesc = {0:[], 1:[], 2:[]}
        for i in range(len(acomet_Layers)):
            for group in aco_group[i]:
                if (group not in trafodGroupTotalList):
                    acoDesc[i].append(group)
             
        trafParalelo = []
        for trafo in trafoCount:
            if (trafoCount.count(trafo) > 1) and (trafo not in trafParalelo):
                trafParalelo.append(trafo)

        toReport = [trafoDesc, BTDesc, acoDesc,cargaDesc, trafParalelo, BT_lines_group, aco_group] 
                    
        return lines_BT_Islands, toReport, GrafoBT, NOGEOMETRY
    
    def reporteInconsis(self):
        starTime = time.time()
        inputLayers = self.readerLayers()
        line_BT_Layers = inputLayers["BT_lines"]
        acomet_Layers = inputLayers["acometida"]
        
        fid_comp_aerea, toReport, GrafoBT, NOGEOMETRY = self.inconsistencias_BT()

        trafoDesc    = toReport[0][0] + toReport[0][1] + toReport[0][2]
        BTDesc       = toReport[1][0] + toReport[1][1] + toReport[1][2]
        acoDesc      = toReport[2][0] + toReport[2][1] + toReport[2][2]
        cargaDesc    = toReport[3][0] + toReport[3][1] + toReport[3][2]
        trafParalelo = toReport[4]
        BT_lines_groups = toReport[5]
        aco_groups      = toReport[6]
        
        anillos = nx.cycle_basis(GrafoBT)
        if len(anillos)==0:
            message =  "No existen anillos en las redes secundarias"            
        else:
            message =  "Existen "+ str(len(anillos))+ " anillos en las redes secundarias"            
            N=1
            for LayerX in line_BT_Layers + acomet_Layers: 
                layer = LayerX[0]
                layer.startEditing()

            for anillo in anillos:
                idlayer = GrafoBT[anillo[0]][anillo[len(anillo)-1]]["idLAYER"]
                AttrIdx = GrafoBT[anillo[0]][anillo[len(anillo)-1]]["ringAttIndex"]
                idBTline= GrafoBT[anillo[0]][anillo[len(anillo)-1]]["fid"]
                element = GrafoBT[anillo[0]][anillo[len(anillo)-1]]["element"]
                if element== "BTLine":
                    layer = line_BT_Layers[idlayer][0]
                else:
                    layer = acomet_Layers[idlayer][0]
                done = layer.changeAttributeValue(idBTline, AttrIdx, N)

                for i in range(len(anillo)-1):
                    idlayer = GrafoBT[anillo[i]][anillo[i+1]]["idLAYER"]
                    AttrIdx = GrafoBT[anillo[i]][anillo[i+1]]["ringAttIndex"]
                    idBTline= GrafoBT[anillo[i]][anillo[i+1]]["fid"]
                    element = GrafoBT[anillo[i]][anillo[i+1]]["element"]
                    if element== "BTLine":
                        layer = line_BT_Layers[idlayer][0]
                    else:
                        layer = acomet_Layers[idlayer][0]
                    done = layer.changeAttributeValue(idBTline, AttrIdx, N)
                N+=1
                
            ###RENDER MT LINES 
            if self.dlg.checkBox_anillos.isChecked() : 
                self.ringRender(line_BT_Layers)
                self.ringRender(acomet_Layers)
                self.iface.mapCanvas().refresh()
            for LayerX in line_BT_Layers + acomet_Layers: 
                layer = LayerX[0]
                layer.commitChanges()
        if self.dlg.colorCheckBox.isChecked() : 
            for i in range(len(line_BT_Layers)):
                layer = line_BT_Layers[i][0]
                groupsLines = BT_lines_groups[i]
                self.render(layer, groupsLines, "LV_GROUP")
            for i in range(len(acomet_Layers)):
                layer = acomet_Layers[i][0]
                groupsLines = aco_groups[i]
                self.render(layer, groupsLines, "LV_GROUP")
       
       
        if len(trafoDesc) > 0 :
            repTraf = "\nHay "+str(len(trafoDesc))+" transformadores que no tienen ningún elemento conectado al secundario. Su correspondiente grupo de BT es: "+ str(trafoDesc)
        else:
            repTraf = '\nNo existen transformadores desconectados de BT.'
        
        if len(BTDesc) > 0 :
            repLines = "\nHay "+str(len(BTDesc))+" lineas de BT desconectadas, las cuales están en los siguientes grupos: "+str(BTDesc)
        else:
            repLines = '\nNo existen lineas de BT desconectadas.'
            
            
        if len(acoDesc) > 0 :
            repAco = "\nHay "+str(len(acoDesc))+" acometidas desconectadas. Sus correspondientes grupos de BT grupo son: "+str(acoDesc)
        else:
            repAco = '\nNo existen acometidas desconectadas.'
            
        
        if len(cargaDesc) > 0 :
            repLoad = "\nHay "+str(len(cargaDesc))+" cargas de BT desconectadas, las cuales están en los siguientes grupos: " + str(cargaDesc)
        else:
            repLoad = '\nNo existen cargas de BT desconectadas.'
            
        if len(trafParalelo) > 0 :
            repParalel = "\nHay "+str(len(trafParalelo))+" secundarios con más de un transformador, estos están en los siguientes grupos: " + str(trafParalelo)
        else:
            repParalel = '\nNo existen secundarios con mas de 1 transformador.' 
            
        if NOGEOMETRY:
            repGeome = '\nExisten elementos en el SIG sin geometria, estos elementos tienen un 1 en el atributo NO_GEOMETRY.'
        else:
            repGeome=''
        message +=  repParalel + repTraf + repLines + repAco + repLoad + repGeome
        
        filename_report = self.output_folder + "/Inconsistencias_BT.txt"
        if self.output_folder != "":
            with open(filename_report, 'w') as file_report:
                    file_report.write(message)

        QgsApplication.instance().messageLog().logMessage(message, tag="REGISTRO DE INCONSISTENCIAS",level=Qgis.MessageLevel(1))
        QMessageBox.warning(None, QCoreApplication.translate('dialog', u'REGISTRO DE INCONSISTENCIAS'), message)
        
        self.iface.messageBar().pushMessage("DN_Corrector", QCoreApplication.translate('dialog', "Se ha analizado la red de baja tension, vea los mensajes de registro para ver las inconsistencias"))        
        
        

    def render(self, aereaLayer, groups, field):
################################################################################ Colorea los grupos de LBT aerea con colores distintos
               
        aereaLayer.beginEditCommand("Update layer styling")
        categories = []
        firstCat = True
        for cat in groups:
            symbol = QgsSymbol.defaultSymbol(aereaLayer.geometryType())
            symbol.setColor(QColor(randint(0,255), randint(0,255), randint(0,255)))
            if firstCat:
                firstCat = False
            else:
                symbol.setWidth(symbol.width())
            category = QgsRendererCategory(cat, symbol, "%d" % cat)
            categories.append(category)
       
        renderer = QgsCategorizedSymbolRenderer(field, categories)
        aereaLayer.setRenderer(renderer)
        
        aereaLayer.triggerRepaint()
        aereaLayer.endEditCommand()            
    def trafConec(self):

        inputLayers = self.readerLayers()
        line_MT_Layers = inputLayers["MT_lines"]
        trafo_Layers = inputLayers["trafos"]
        line_BT_Layers = inputLayers["BT_lines"]
        acomet_Layers = inputLayers["acometida"]
        tolerance = self.dlg.toleranceSpinBox.value()
        if tolerance == 0:
            tolerance = self.tolerance
        fid_comp_aerea, toReport, GrafoBT, NOGEOMETRY = self.inconsistencias_BT()
        trafoDesc, linesBTDesc, ACODesc, loadDesc, trafParalelo, BT_lines_group, aco_group = toReport

                    
        func_connector.trafConnectMain(line_BT_Layers, acomet_Layers, trafo_Layers, linesBTDesc, ACODesc, trafoDesc, GrafoBT, tolerance)
        self.iface.messageBar().pushSuccess("Finalizado", "Se ha finalizado el proceso de conexion transformadores")
        self.iface.mapCanvas().refresh()
    def loadConec(self):
        inputLayers = self.readerLayers()
        line_BT_Layers = inputLayers["BT_lines"]
        acomet_Layers = inputLayers["acometida"]
        carga_BT_Layers = inputLayers["carga_BT"]
        
        fid_comp_aerea, toReport, GrafoBT, NOGEOMETRY = self.inconsistencias_BT()
        trafoDesc, linesBTDesc, ACODesc, loadDesc, trafParalelo, BT_lines_group, aco_group = toReport
        
        func_connector.loadConnectMain(carga_BT_Layers, line_BT_Layers, acomet_Layers, loadDesc)
        self.iface.mapCanvas().refresh()
        self.iface.messageBar().pushSuccess("Finalizado", u"Se ha finalizado el proceso de conexion cargas de BT")
    def lineConec(self):
        inputLayers = self.readerLayers()
        trafo_Layers = inputLayers["trafos"]
        line_BT_Layers = inputLayers["BT_lines"]
        acomet_Layers = inputLayers["acometida"]
        tolerance = self.dlg.toleranceSpinBox.value()
        if tolerance == 0:
            tolerance = self.tolerance
        fid_comp_aerea, toReport, GrafoBT, NOGEOMETRY  = self.inconsistencias_BT()
        trafoDesc, linesBTDesc, ACODesc, loadDesc, trafParalelo, BT_lines_group, aco_group = toReport
        
        func_connector.lineConnectMain(line_BT_Layers, acomet_Layers, linesBTDesc, ACODesc, BT_lines_group, aco_group, GrafoBT, tolerance)
        self.iface.messageBar().pushSuccess("Final", u"Se ha finalizado el proceso de conexion de lineas de BT")

        self.iface.mapCanvas().refresh()        
        
    def selectGrup(self, layer, attributeName, VALUE):
        toQgisExp = str("\"")+attributeName+str("\"")+str("=")+str(VALUE)
   
        exp = QgsExpression(toQgisExp )
        it = layer.getFeatures(QgsFeatureRequest(exp))

        ids = [i.id() for i in it]
        if len(ids)==0:
            print ("NO SE HA SELECCIONADO NINGUN ELEMENTO, verifique que el atributo y el valor existen.")
        else:
            #layer.setSelectedFeatures(ids)
            layer.selectByIds(ids)
    def checkvector(self):
        count = 0
        for name, layer in QgsProject.instance().mapLayers().items():
            if layer.type() == QgsMapLayer.VectorLayer:
                count += 1
        return count
    def lineCreator(self, layer, p1, p2):
        x1 = p1[0]
        y1 = p1[1]
        x2 = p2[0]
        y2 = p2[1]
        if x1==x2:
            x1 = x1+0.0000001
        m = (y1-y2)/(x1-x2)
        Ymin = min(y1, y2)
        XMax = max(x1, x2)
        YMax = max(y1, y2)
        XMin = min(x1, x2)
        
        cita = math.atan((YMax-Ymin)/(XMax-XMin))
        toler = self.tolerance
        xToler = toler*math.cos(cita)
        yToler = toler*math.sin(cita)
        if m <= 0:
            X1 = XMin - xToler
            X2 = XMax + xToler
            Y1 = YMax + yToler
            Y2 = Ymin - yToler
        if m > 0:
            Y1 = Ymin - yToler
            X1 = XMin - xToler
            X2 = XMax + xToler
            Y2 = YMax + yToler
            
        
        dp = layer.dataProvider()
        point1 = QgsPoint(X1, Y1)
        
        point2 = QgsPoint(X2, Y2)
        lin = QgsFeature()
        lin.setGeometry(QgsGeometry.fromPolyline([point1,point2]))
        list = [None]*len(dp.fields())
        list[layer.fields().indexFromName("LV_GROUP")]=888888
        lin.setAttributes(list)
        dp.addFeatures([lin])
        QgsProject.instance().addMapLayers([layer])
        return lin
    def pendientesIguales(self, La, Lb):
        toler = self.tolerance #Tolerancia
        x1a = La[0][0]
        y1a = La[0][1]
        x2a = La[1][0]
        y2a = La[1][1]
        if x1a==x2a:
            x1a = x1a + 0.0000001
            
        ma = (y1a-y2a)/(x1a-x2a)
        ##Linea b
        x1b = Lb[0][0]
        y1b = Lb[0][1]
        x2b = Lb[1][0]
        y2b = Lb[1][1]
        if x1b==x2b:
            x1b = x1b + 0.0000001
            
        mb = (y1b-y2b)/(x1b-x2b)
        if ma == mb:
            return True
        else:
            return False
    def intersection(self, La, Lb):
        toler = 0.001 #Tolerancia
        ##Linea a
        x1a = La[0][0]
        y1a = La[0][1]
        x2a = La[1][0]
        y2a = La[1][1]
        if x1a==x2a:
            x1a = x1a + 0.0000001
        ma = (y1a-y2a)/(x1a-x2a)
        Ba = y1a - ma*x1a
        ##Linea b
        x1b = Lb[0][0]
        y1b = Lb[0][1]
        x2b = Lb[1][0]
        y2b = Lb[1][1]
        if x1b==x2b:
            x1b = x1b + 0.0000001
        mb = (y1b-y2b)/(x1b-x2b)
        Bb = y1b - mb*x1b
        ##PUNTO DE INTERSECCIoN
        Xi = (Ba-Bb)/(mb-ma)
        Yi = mb*Xi +Bb
        
        
        XaMax = max(x1a, x2a)
        XbMax = max(x1b, x2b)
        XaMin = min(x1a, x2a)
        XbMin = min(x1b, x2b)

        YaMax = max(y1a, y2a)
        YbMax = max(y1b, y2b)
        YaMin = min(y1a, y2a)
        YbMin = min(y1b, y2b)        
        
        #######################
        cita = math.atan((YaMax-YaMin)/(XaMax-XaMin))
        xaToler = toler*math.cos(cita)
        yaToler = toler*math.sin(cita)
        if ma <= 0:
            XaMin = XaMin - xaToler
            XaMax = XaMax + xaToler
            YaMax = YaMax + yaToler
            YaMin = YaMin - yaToler
        if ma > 0:
            YaMin = YaMin - yaToler
            XaMin = XaMin - xaToler
            XaMax = XaMax + xaToler
            YaMax = YaMax + yaToler
        #######################
        #######################
        cita = math.atan((YbMax-YbMin)/(XbMax-XbMin))
        xbToler = toler*math.cos(cita)
        ybToler = toler*math.sin(cita)
        if ma <= 0:
            XbMin = XbMin - xbToler
            XbMax = XbMax + xbToler
            YbMax = YbMax + ybToler
            YbMin = YbMin - ybToler
        if ma > 0:
            YbMin = YbMin - ybToler
            XbMin = XbMin - xbToler
            XbMax = XbMax + xbToler
            YbMax = YbMax + ybToler
        ##########################3
        
        if ma == mb:
            return -1
        elif (XaMin<=Xi<=XaMax) and (XbMin<= Xi <= XbMax) and (YaMin<= Yi <= YaMax) and (YbMin<= Yi <= YbMax):
            point = (Xi, Yi)
            
            return point
        else:
            return -1
    def get_layer(self):#Carga la capa para Split 
        layerName = self.dlg.layerComboBox_split.currentText()
        try:
            layer = QgsProject.instance().mapLayersByName(layerName)[0]
        except:
            self.iface.messageBar().pushCritical("DN_Corrector", QCoreApplication.translate('dialog', u' Debe seleccionar una capa'), duration=3)
        return layer
    def spliter(self, selection):
        z = 0
        LastInter = 0
        layer = self.get_layer()#carga la capa
        #print("layer.wkbType() = ", layer.wkbType(), " QgsWkbTypes.LineString = ", QgsWkbTypes.LineString )
        #if layer.wkbType() == QgsWkbTypes.LineString:#Verifica que la capa sea de lineas
        if layer.wkbType() == QgsWkbTypes.MultiLineString:#Verifica que la capa sea de multi lineas
            layer.startEditing() #Activa modo edicion
            layer.beginEditCommand("Feature triangulation")
            newSelection = []
            grupoNum = -1
            
            for feat in selection:
                newSelection.append(feat)
                grupoNum=feat['LV_GROUP']
            
            """
            length = -1
            for feat in layer.getFeatures(): 
                length += 1
            """
            if len(newSelection) >= 1:#asegura que exista mas de 1 linea seleccionada
                flag = 0
                while flag == 0:#ITERA SIEMPRE Y CUANDO EXISTAN CORTES
                    flag = 1
                    pp = 0
                    for obj in newSelection:#RECORRE CADA LINEA SELECCIONADA
                        geom = obj.geometry()
                        line = self.MultiStringToMatrix(geom)
                        
                        n = len(line)
                        startPointA = (round(line[0][0],4), round(line[0][1],4))
                        endPointA = (round(line[n-1][0],4), round(line[n-1][1],4))
    
                        
                        for i in range(len(line)-1):#entra a cada segmento de la polilinea 'OBJ'
                            vert1a = i 
                            vert2a = i+1
                            p1a = (line[vert1a][0],line[vert1a][1])
                            p2a = (line[vert2a][0],line[vert2a][1])
                            La =(p1a, p2a)
    
                            for seg in newSelection:#RECORRE CADA LINEA SELECCIONADA
                                if (seg == obj):
                                    pass
                                else:
                                    geom = seg.geometry()
                                    lineSeg = self.MultiStringToMatrix(geom)
                                    print(lineSeg)
                                    n = len(lineSeg)
                                    startPointB = (round(lineSeg[0][0],4), round(lineSeg[0][1],4))
                                    endPointB = (round(lineSeg[n-1][0],4), round(lineSeg[n-1][1],4))
                                    if (startPointB == startPointA) or (endPointB == startPointA) or (startPointB== endPointA) or (endPointB == endPointA):  #No necesita cortar
                                        inter = -1
                                        print(21)
                                    else:        
                                        for i in range(len(lineSeg)-1):#entra a cada segmento de la polilinea 'SEG'
                                            print(lineSeg)
                                            vert1b = i 
                                            vert2b = i+1
                                            p1b = (lineSeg[vert1b][0],lineSeg[vert1b][1])
                                            p2b = (lineSeg[vert2b][0],lineSeg[vert2b][1])
                                            Lb =(p1b, p2b)
                                                
                                            if self.pendientesIguales(La, Lb):
                                                inter = -1
                                                print(22)
                                            else:
                                                inter = self.intersection(La, Lb) # Si intersecan devuelve el punto de interseccion, sino -1
                                                print(23)
                                                break                                                
                                            if inter != (-1): #Existe interseccion
                                                if inter == LastInter:
                                                    z +=1
                                                else:                                                    
                                                    z = 0
                                                LastInter = inter

                                                if z > 6:
                                                    message = "PROBLEMAS AL PROCESAR LA INTERSECCION " + str(inter) + "  de la isla: "+str(grupoNum)+ ". VERIFIQUELA MANUALMENTE Y EJECUTE LA HERRAMIENTA DE NUEVO."
                                                    
                                                    QMessageBox.warning(None, QCoreApplication.translate('dialog', u'CORTE DE LINEAS'), message)
                                                     
                                                    pp = 1
                                                    flag = 1
                                                    break
                                                print(inter)
                                                coord_a = inter[0]
                                                coord_b = inter[1]
                                                inter = (round(coord_a[0],4), round(coord_b[0],4))
                                            
                                            if (inter != startPointA) and (inter != endPointA) and (inter != startPointB) and (inter!= endPointB):
                                            
                                                # c = 0
                                                # for feat in layer.selectedFeatures():
                                                    # c += 1
                                                                                      
                                                geom = obj.geometry()
                                                line_a = self.MultiStringToMatrix(geom)
                                                line_a = [QgsPointXY(line_a[0][0], line_a[0][1]),QgsPointXY(line_a[1][0], line_a[1][1])]
                                                a = layer.splitFeatures( line_a )
                                                
                                                geom = seg.geometry()
                                                line_b = self.MultiStringToMatrix(geom)                                                	
                                                line_b = [QgsPointXY(line_b[0][0], line_b[0][1]),QgsPointXY(line_b[1][0], line_b[1][1])]											
                                                b = layer.splitFeatures( line_b )
                                                
                                                self.iface.mapCanvas().refresh()
                                                self.selectGrup(layer, 'LV_GROUP', grupoNum)
                                                
                                                flag = 0
                                                for feat in layer.selectedFeatures():
                                                   if feat.geometry().length() < 0.05:
                                                        layer.deleteFeature(feat.id())
                                                
                                                self.iface.mapCanvas().refresh()
                                                newSelection = layer.selectedFeatures()
                                                pp = 1
                                                break
                                                
                                            elif ((inter != startPointA) and (inter != endPointA)):
                                                a = self.lineCreator(layer, p1b, p2b)
                                                self.iface.mapCanvas().refresh()
                                                
                                                geom = seg.geometry()
                                                nodos = self.MultiStringToMatrix(geom)
                                                nodos_qgspoint=[]
                                                
                                                for nodo in nodos:
                                                    nodos_qgspoint.append(QgsPoint(nodo[0], nodo[1]))
                                                                                                
                                                att=seg.attributes()
                                                layer.deleteFeature(seg.id())
                                                self.iface.mapCanvas().refresh()
                                                
                                                geom = a.geometry()
                                                line_a = self.MultiStringToMatrix(geom)
                                                line_a = [QgsPointXY(line_a[0][0], line_a[0][1]),QgsPointXY(line_a[1][0], line_a[1][1])]
                       
                                                a = layer.splitFeatures( line_a )
                                                ###if a != 0:
                                                    
                                                flag = 0
                                                self.iface.mapCanvas().refresh()
                                                
                                                toQgisExp = str("\"")+"LV_GROUP"+str("\"")+str("=")+str(888888)
                                                exp = QgsExpression(toQgisExp )
                                                featToDelete = layer.getFeatures(QgsFeatureRequest(exp))
                                                for feat in featToDelete:
                                                    layer.deleteFeature(feat.id())
                                                self.iface.mapCanvas().refresh()
                                                
                                                dp = layer.dataProvider()
                                                lin = QgsFeature()
                                                lin.setGeometry(QgsGeometry.fromPolyline(nodos_qgspoint))
                                                lin.setAttributes(att)
                                                dp.addFeatures([lin])
                                                QgsProject.instance().addMapLayers([layer])
                                                self.iface.mapCanvas().refresh()
                                                
                                                self.selectGrup(layer, 'LV_GROUP', grupoNum)
                                                newSelection = layer.selectedFeatures()
                                                pp = 1
                                                break
                                        
                                            elif ((inter != startPointB) and (inter != endPointB)): 
                                                b = self.lineCreator(layer, p1a, p2a)
                                                self.iface.mapCanvas().refresh()
    
                                                geom = obj.geometry()
                                                nodos = self.MultiStringToMatrix(geom)
                                                
                                                nodos_qgspoint=[]
                                                for nodo in nodos:
                                                    nodos_qgspoint.append(QgsPoint(nodo[0], nodo[1]))
                                    
                                                                                                
                                                att = obj.attributes()
                                                layer.deleteFeature(obj.id())
                                                self.iface.mapCanvas().refresh()
                                                
                                                geom = b.geometry()
                                                line_a = self.MultiStringToMatrix(geom)
                                                line_a = [QgsPointXY(line_a[0][0], line_a[0][1]),QgsPointXY(line_a[1][0], line_a[1][1])]
                                                a = layer.splitFeatures( line_a )
                                                ###if a != 0:
                                                ###    print 'no se pudo cortar en la interseccion ' + str(inter)
                                                
                                                flag = 0
                                                self.iface.mapCanvas().refresh()
                                                
                                                toQgisExp = str("\"")+"LV_GROUP"+str("\"")+str("=")+str(888888)
                                                exp = QgsExpression(toQgisExp )
                                                featToDelete = layer.getFeatures(QgsFeatureRequest(exp))
                                                for feat in featToDelete:
                                                    layer.deleteFeature(feat.id())
                                                self.iface.mapCanvas().refresh()
                                                #
                                                dp = layer.dataProvider()
                                                lin = QgsFeature()
                                                lin.setGeometry(QgsGeometry.fromPolyline(nodos_qgspoint))
                                                lin.setAttributes(att)
                                                dp.addFeatures([lin])
                                                QgsProject.instance().addMapLayers([layer])
                                                self.iface.mapCanvas().refresh()
    
                                                self.selectGrup(layer, 'LV_GROUP', grupoNum)
                                                newSelection = layer.selectedFeatures()
                                                pp = 1
                                                break
                                if pp == 1:
                                    break
                            if pp == 1:
                                break
                        if pp == 1:
                            break
            else:
                self.iface.messageBar().pushCritical("Split Line",u" Debe seleccionar mas de una linea")
        
            self.iface.mapCanvas().refresh()
       
    def split_iteration(self):
        progressMessageBar = self.iface.messageBar().createMessage(u"Cortando lineas en intersecciones...")
        progress = QProgressBar()

        
        timeStar = time.time()
        layer = self.get_layer()#carga la capa
        clipped = []
        toClipped = []
        
        idx = layer.fields().indexFromName('LV_GROUP')
        toClipped = list(layer.uniqueValues(idx))
        toClipped =  list(QgsVectorLayerUtils.getValues(layer,"LV_GROUP")) 
                
        progress.setMaximum(len(toClipped))
        progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        progressMessageBar.layout().addWidget(progress)
        
        
        i = 0
        xx = []
        paso = 100/len(toClipped)
        #self.progress.progressBar.setValue(int(paso))
        pasoi=paso
        for spliting in toClipped:
            #self.progress.progressBar.setValue(int(pasoi))
            progress.setValue(i + 1)
            xx.append(spliting)
            toQgisExp = str("\"LV_GROUP")+str("\"")+str("=")+str(spliting)
            exp = QgsExpression(toQgisExp)
            it = layer.getFeatures(QgsFeatureRequest(exp))
            self.spliter(it)
            i += 1
            #pasoi = pasoi+paso
        
        #self.attributeUpdateLines(layer)
        timeEnd = time.time()
        #self.progress.close()
        self.iface.messageBar().clearWidgets()
        # fix_print_with_import
        print('fin, tardo: '+ str(timeEnd-timeStar)+' segundos')
        # fix_print_with_import
        print('Islas analizadas' +str(xx))
        self.iface.messageBar().pushInfo("DN_corrector", QCoreApplication.translate('dialog', "Función de corte finalizada exitosamente"))  # Aviso de finalizado en barra de QGIS
        
    #####################################################
    """    
    Esta función lo que hace es pasar de un MultiLineString a una matriz.
    """    
    def MultiStringToMatrix(self, geom):
        if geom.wkbType() == 0: #sin geometría
            print ("LINEA NO TIENE GEOMETRÍA")
        elif geom.wkbType()== 5: #MultiLineString
            line = geom.asMultiPolyline()
            line = line[0] ###### verificar si es necesario hacer esto....
        else:
            line = geom.asPolyline()#PolyLine
        matriz = []
        
        for punto in line:
            x = punto.x()
            y = punto.y()
            punto_t = [x, y]
            matriz.append(punto_t)
        return matriz
        
        
    #####################################################
    
    def run(self):
        """Run method that performs all the real work"""
        
        # Carga los nombres de las capas actualmente abiertas y las muestra en las listas desplegables
        lista_ant =  [self.dlg.layerComboBox_aerea_MT_1.itemText(i) for i in range(self.dlg.layerComboBox_aerea_MT_1.count())] #Lista anterior en combobox
        
        layers = QgsProject.instance().mapLayers().values()
        layer_list = []
        layer_list.append("")
        
        for layer in layers:
            layer_list.append(layer.name())
        
        layers = QgsProject.instance().mapLayers().values()
        layer_list = []
        layer_list.append("")
        
        for layer in layers:
            layer_list.append(layer.name())
        
        """
        layers = self.iface.mapCanvas().layers()
        layer_list = []
        for layer in layers:
            layer_list.append(layer.name())
        """
        
        #Cambia los valores en los comboBox sólo si hay algún cambio en la lista de capas
        if lista_ant != layer_list:
            self.dlg.layerComboBox_aerea_MT_1.clear()
            self.dlg.layerComboBox_carga_MT_1.clear()
            self.dlg.layerComboBox_aer_1.clear()
            self.dlg.layerComboBox_trafo_1.clear()
            self.dlg.layerComboBox_Carga_1.clear()
            self.dlg.layerComboBox_acometida_1.clear()
            
            self.dlg.layerComboBox_aerea_MT_2.clear()
            self.dlg.layerComboBox_carga_MT_2.clear()
            self.dlg.layerComboBox_aer_2.clear()
            self.dlg.layerComboBox_trafo_2.clear()
            self.dlg.layerComboBox_Carga_2.clear()
            self.dlg.layerComboBox_acometida_2.clear()
            
            self.dlg.layerComboBox_aerea_MT_3.clear()
            self.dlg.layerComboBox_carga_MT_3.clear()
            self.dlg.layerComboBox_aer_3.clear()
            self.dlg.layerComboBox_trafo_3.clear()
            self.dlg.layerComboBox_Carga_3.clear()
            self.dlg.layerComboBox_acometida_3.clear()
            
            self.dlg.layerComboBox_split.clear()
            
            self.dlg.layerComboBox_aerea_MT_1.addItems(layer_list)
            self.dlg.layerComboBox_carga_MT_1.addItems(layer_list)
            self.dlg.layerComboBox_aer_1.addItems(layer_list)
            self.dlg.layerComboBox_Carga_1.addItems(layer_list)
            self.dlg.layerComboBox_trafo_1.addItems(layer_list)
            self.dlg.layerComboBox_acometida_1.addItems(layer_list)
    
            self.dlg.layerComboBox_aerea_MT_2.addItems(layer_list)
            self.dlg.layerComboBox_carga_MT_2.addItems(layer_list)
            self.dlg.layerComboBox_aer_2.addItems(layer_list)
            self.dlg.layerComboBox_Carga_2.addItems(layer_list)
            self.dlg.layerComboBox_trafo_2.addItems(layer_list)
            self.dlg.layerComboBox_acometida_2.addItems(layer_list)
            
            self.dlg.layerComboBox_aerea_MT_3.addItems(layer_list)
            self.dlg.layerComboBox_carga_MT_3.addItems(layer_list)
            self.dlg.layerComboBox_aer_3.addItems(layer_list)
            self.dlg.layerComboBox_Carga_3.addItems(layer_list)
            self.dlg.layerComboBox_trafo_3.addItems(layer_list)
            self.dlg.layerComboBox_acometida_3.addItems(layer_list)
            
            self.dlg.layerComboBox_split.addItems(layer_list)
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        
        if result:
            pass
