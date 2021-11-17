# -*- coding: utf-8 -*-
from __future__ import absolute_import
from builtins import str
from builtins import range
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qgis.core import * #QgsMapLayerRegistry, QgsVectorDataProvider, QgsField
from qgis.gui import QgsMessageBar
from .DN_Corrector_dialog import DN_CorrectorDialog



#####################################################
"""    
Esta función lo que hace es pasar de un MultiLineString a una matriz.
"""    
def MultiStringToMatrix(geom):
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


def nodesToTree(lines):
    treeStartPoint = [] #Lista de puntos iniciales de las lineas
    treeEndPoint = [] #Lista de puntos puntos de las lineas
    dataLine = []
    for feat in lines:
        geom = feat.geometry()
        line = []
        line = MultiStringToMatrix(geom)
                
        n = len(line)
        startPoint = (line[0][0], line[0][1]) #(X, Y) inicial de la linea
        #print startPoint
        endPoint = (line[n-1][0], line[n-1][1]) #(X, Y) final de la linea
        treeStartPoint.append(startPoint)
        treeEndPoint.append(endPoint)
    #print treeStartPoint
    linesPoint = treeStartPoint + treeEndPoint # puntos iniciales y finales anexados
    leng = len(treeStartPoint)
    return linesPoint ,leng
    
def loadConnect (layer, lines, loadFeatDesc):
    from scipy import spatial 
    import numpy as np
    from scipy.spatial import KDTree
    linesPoint,leng = nodesToTree(lines)
    layer.startEditing() #Activa modo edicion
    for feat in loadFeatDesc: #Lista de trafos desconectados
        point = feat.geometry().asPoint()
        Tree = KDTree(linesPoint) #Arbol creado con lineas desconectadas
        pointx= point[0]
        #print pointx
        pointy= point[1]
        radio = 0.1
        existe = False
        idx= []
        while (radio <= 2) and len(idx) == 0:
            idx = Tree.query_ball_point([pointx,pointy],r=radio)
            if len(idx) != 0:
                existe = True
                break
            else :
                radio += 0.1
            
        if existe:
            newPointx =  linesPoint[idx[0]][0]
            newPointy =  linesPoint[idx[0]][1]
            layer.moveVertex(newPointx, newPointy, feat.id(), 0)
    layer.commitChanges()
def trafConnect(layer, linesFEAT, elementDesc, grafo, tolerance): 
    from scipy import spatial 
    import numpy as np
    from scipy.spatial import KDTree
    linesPoint, leng = nodesToTree(linesFEAT)
    for feat in elementDesc: #Lista de trafos desconectados

        point = feat.geometry().asPoint()
        #print linesPoint
        Tree = KDTree(linesPoint) #Arbol creado con lineas desconectadas
        pointx= point[0]
        #print pointx
        pointy= point[1]
        radio = 0.1
        
        existe = False
        idx= []
        while (radio <= 2) and len(idx) == 0:
            idx = Tree.query_ball_point([pointx,pointy],r=radio)
            if len(idx) != 0:
                existe = True
                break
            else :
                radio += 0.1
        if existe:
            layer.startEditing() #Activa modo edicion
            for id in idx:#Mueve mas de una linea en caso de que esten cercanas al trafo
                if id > (leng -1) :
                    idLine = linesFEAT[id - leng].id()###################
                    
                    geom = linesFEAT[id - leng].geometry()
                    line = []
                    line = MultiStringToMatrix(geom)
                    vert = len(line)-1
                    
                else:
                    vert = 0
                    idLine = linesFEAT[id].id()
                    
                    geom = linesFEAT[id].geometry()
                    line = []
                    line = MultiStringToMatrix(geom)
                                        
                nodo=(int(line[vert][0]/tolerance), int(line[vert][1]/tolerance))
                try:
                    if grafo.node[nodo]['element']=="carga": #Verifica que el extremo de linea a mover no este conectado a una carga
                        mover = False
                except:
                    mover = True
                if mover:
                    layer.moveVertex(pointx, pointy, idLine, vert)#####################
            layer.commitChanges()
def lineConnect(layer, mainFeatLines, linesFeatDesc, grafo, tolerance):
    from scipy import spatial 
    import numpy as np
    from scipy.spatial import KDTree
    mainPoints, lengMain = nodesToTree(mainFeatLines) #imputs = feats
    #subtPoints, lengSubt = nodesToTree(subtLines)
    descPoint, lengDesc = nodesToTree(linesFeatDesc)
    
    mainTree = KDTree(mainPoints) #Arbol creado con lineas aereas
    descTree = KDTree(descPoint) #Arbol creado con lineas desconectadas
    
    existe = False
    radio = 0.1
    layer.startEditing()

    while (not existe) and (radio < 2):
        idx = mainTree.query_ball_tree(descTree, radio) #encuentra los pares de puntos con distanrias de máximo "radio"
        mainId = 0
        for main in idx: # cada ciclo representa al id de arbol main o conectado
            if len(main) != 0:
                 #Activa modo edicion
                if mainId >= lengMain:
                    IdrealMain = mainId - lengMain
                    
                    geom = mainFeatLines[IdrealMain].geometry()
                    vertex = []
                    vertex = MultiStringToMatrix(geom)
                                        
                    newPoint = vertex[len(vertex)-1]
                else:
                    
                    IdrealMain = mainId
                    
                    geom = mainFeatLines[IdrealMain].geometry()
                    vertex = []
                    vertex = MultiStringToMatrix(geom)
                                                           
                    newPoint = vertex[0]
                
                
                for id in main: #cada ciclo representa el id de desc que esta cerca del id del main
                    
                    if id > (lengDesc -1) :
                        idLine = linesFeatDesc[id - lengDesc].id()##
                        
                        geom = linesFeatDesc[id - lengDesc].geometry()
                        line = []
                        line = MultiStringToMatrix(geom)
                                               
                        
                        vert = len(line)-1
                        
                    else:
                        vert = 0
                        idLine = linesFeatDesc[id].id()
                        
                        geom = linesFeatDesc[id].geometry()
                        line = []
                        line = MultiStringToMatrix(geom)
                                                
                    nodo=(int(line[vert][0]/tolerance), int(line[vert][1]/tolerance))
                    try:
                        if grafo.node[nodo]['element']=="carga": #Verifica que el extremo de línea a mover no esté conectado a una carga
                            mover = False
                    except:
                        mover = True
                    if mover:
                        layer.moveVertex(newPoint[0], newPoint[1], idLine, vert)#
            else:
                pass
            mainId +=1
        radio += 0.1
    layer.commitChanges()


def trafConnectMain(BTLayers, acoLayerS,trafo_Layers , BTLinesDesc, AcoLinesDesc, trafosDesc, GrafoBT, tolerance):
    linesBTFeatDesc = {0:[], 1:[], 2:[]}
    ACOFeatDesc   = {0:[], 1:[], 2:[]}
    trafFeatDesc  = []

    for i in range(len(BTLayers)): #Obtiene los objetos QGS de las lineas de BT desconectadas
        for group in BTLinesDesc[i]:
            toQgisExp = str("\"LV_GROUP")+str("\"")+str("=")+str(group)
            exp = QgsExpression(toQgisExp )
            it = BTLayers[i][0].getFeatures(QgsFeatureRequest(exp))
            for feat in it:
                linesBTFeatDesc[i].append(feat)

    for i in range(len(acoLayerS)):#Obtiene los objetos QGS de las acometidas desconectadas
        for group in AcoLinesDesc[i]:
            toQgisExp = str("\"LV_GROUP")+str("\"")+str("=")+str(group)
            exp = QgsExpression(toQgisExp )
            it = acoLayerS[i][0].getFeatures(QgsFeatureRequest(exp))
            for feat in it:
                ACOFeatDesc[i].append(feat)
                
    for i in range(len(trafo_Layers)):#Obtiene los objetos QGS de los transformadores desconectados
        for group in trafosDesc[i]:
            toQgisExp = str("\"LV_GROUP")+str("\"")+str("=")+str(group)
            exp = QgsExpression(toQgisExp )
            it = trafo_Layers[i][0].getFeatures(QgsFeatureRequest(exp))
            for feat in it:
                trafFeatDesc.append(feat)
                
    for i in range(len(BTLayers)):
        layer=BTLayers[i][0]
        iBTDesc = linesBTFeatDesc[i]
        if len(iBTDesc) != 0:
            trafConnect(layer, iBTDesc, trafFeatDesc, GrafoBT, tolerance)

    for i in range(len(acoLayerS)):
        layer=acoLayerS[i][0]
        iACODesc = ACOFeatDesc[i]
        if len(iACODesc) != 0:
            trafConnect(layer, iACODesc, trafFeatDesc, GrafoBT, tolerance)

    
def loadConnectMain(loadLayers, BTLayers, acoLayers, loadDesc): 
    loadFeatDesc  = {0:[], 1:[], 2:[]}
    for i in range(len(loadLayers)):
        for group in loadDesc[i]:
            toQgisExp = str("\"LV_GROUP")+str("\"")+str("=")+str(group)
            exp = QgsExpression(toQgisExp )
            it = loadLayers[i][0].getFeatures(QgsFeatureRequest(exp))
            for feat in it:
                loadFeatDesc[i].append(feat)

    TotalLines = []
    for i in range(len(BTLayers)):
        layer = BTLayers[i][0]
        for feat in layer.getFeatures():
            TotalLines.append(feat)
    for i in range(len(acoLayers)):
        layer = acoLayers[i][0]
        for feat in layer.getFeatures():
            TotalLines.append(feat)

        
    for i in range(len(loadLayers)):
        loadConnect(loadLayers[i][0], TotalLines, loadFeatDesc[i])


def lineConnectMain(line_BT_Layers, acomet_Layers, BTDesc, acoDesc, BT_lines_group, aco_group, grafo, tolerance):
    groupFeatMain = []
    
    BTfeatDesc = {0:[], 1:[], 2:[]}
    acoFeatDesc = {0:[], 1:[], 2:[]}
    #############################
    for i in range(len(line_BT_Layers)):
        for group in BT_lines_group[i]:
            toQgisExp = str("\"LV_GROUP")+str("\"")+str("=")+str(group)
            exp = QgsExpression(toQgisExp )
            it = line_BT_Layers[i][0].getFeatures(QgsFeatureRequest(exp))
            if group not in BTDesc[i]:
                for feat in it:
                    groupFeatMain.append(feat)
            else:
                for feat in it:
                    BTfeatDesc[i].append(feat)
                
    for i in range(len(acomet_Layers)):
        for group in aco_group[i]:
            toQgisExp = str("\"LV_GROUP")+str("\"")+str("=")+str(group)
            exp = QgsExpression(toQgisExp )
            it = acomet_Layers[i][0].getFeatures(QgsFeatureRequest(exp))
            if group not in acoDesc[i]:
                for feat in it:
                    groupFeatMain.append(feat)
            else:
                for feat in it:
                    acoFeatDesc[i].append(feat)
            
    for i in range(len(line_BT_Layers)):
        if len(BTfeatDesc[i])!= 0:
            lineConnect(line_BT_Layers[i][0], groupFeatMain, BTfeatDesc[i], grafo, tolerance)

    for i in range(len(acomet_Layers)):
        if len(acoFeatDesc[i])!= 0:
            lineConnect(acomet_Layers[i][0], groupFeatMain, acoFeatDesc[i], grafo, tolerance)
        
    #############################

