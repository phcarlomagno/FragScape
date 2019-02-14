# -*- coding: utf-8 -*-
"""
/***************************************************************************
 FragScape
                                 A QGIS plugin
 Computes ecological continuities based on environments permeability
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2018-04-12
        git sha              : $Format:%H$
        copyright            : (C) 2018 by IRSTEA
        email                : mathieu.chailloux@irstea.fr
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

from qgis.core import QgsMapLayerProxyModel, QgsProcessing, QgsProcessingAlgorithm, QgsProcessingException, QgsProcessingParameterFeatureSource, QgsProcessingParameterExpression, QgsProcessingParameterFeatureSink, QgsFieldProxyModel
# from PyQt5 import QtGui, QtCore, QtWidgets
# from PyQt5.QtCore import QCoreApplication
from ..shared import utils, abstract_model, qgsUtils, progress, qgsTreatments
from ..algs import FragScape_algs 
from . import params

landuseModel = None

        
class LanduseFieldItem(abstract_model.DictItem):

    VALUE_FIELD = "value"
    DESCR_FIELD = "description"
    TO_SELECT_FIELD = "toSelect"
    FIELDS = [VALUE_FIELD,
              DESCR_FIELD,
              TO_SELECT_FIELD]

    def __init__(self,val,descr="",toSelect=False):
        dict = { self.VALUE_FIELD : val,
                 self.DESCR_FIELD : descr,
                 self.TO_SELECT_FIELD : toSelect }
        super().__init__(dict)#,fields=self.FIELDS)
        
    def equals(self,other):
        return (self.dict[self.VALUE_FIELD] == other.dict[self.VALUE_FIELD])
    
    # @classmethod
    # def fromVals(cls,val,descr="",isNatural=False):
        # dict = {self.VALUE_FIELD : val,
                # self.DESCR_FIELD : descr,
                # self.TO_SELECT_FIELD : isNatural}
        # return cls(dict)
        
class LanduseModel(abstract_model.DictModel):

    INPUT_FIELD = "in_layer"
    CLIP_LAYER = "clip_layer"
    SELECT_MODE_FIELD = "select_mode"
    SELECT_FIELD_FIELD = "select_field"
    SELECT_DESCR_FIELD = "select_field"
    SELECT_EXPR_FIELD = "select_expr"
    
    ALG_INPUT = FragScape_algs.PrepareLanduseAlgorithm.INPUT
    ALG_CLIP_LAYER = FragScape_algs.PrepareLanduseAlgorithm.CLIP_LAYER
    ALG_SELECT_EXPR = FragScape_algs.PrepareLanduseAlgorithm.SELECT_EXPR
    ALG_OUTPUT = FragScape_algs.PrepareLanduseAlgorithm.OUTPUT
    
    SELECT_FIELD_MODE = 0
    SELECT_EXPR_MODE = 1

    def __init__(self,fragScapeModel):
        self.parser_name = "Landuse"
        self.fsModel = fragScapeModel
        self.landuseLayer = None
        self.select_field = None
        self.descr_field = None
        self.dataClipFlag = False
        self.clip_layer = None
        self.select_mode = self.SELECT_FIELD_MODE
        self.select_expr = ""
        super().__init__(self,LanduseFieldItem.FIELDS)
                        
    def mkItemFromDict(self,dict):
        v = dict[LanduseFieldItem.VALUE_FIELD]
        if LanduseFieldItem.DESCR_FIELD in dict:
            d = dict[LanduseFieldItem.DESCR_FIELD]
        else:
            d = ""
        i = (dict[LanduseFieldItem.TO_SELECT_FIELD] == "True")
        return LanduseFieldItem(v,d,i)
        
    def changeLayer(self,path):
        if not utils.pathEquals(path,self.landuseLayer):
            utils.debug("path = " + str(path))
            utils.debug("old path = " + str(self.landuseLayer))
            self.landuseLayer = path
            if self.select_field:
                loaded_layer = qgsUtils.loadLayer(path)
                if self.select_field not in loaded_layer.fields().names():
                    self.setSelectField(None)
            if self.descr_field:
                if self.descr_field not in loaded_layer.fields().names():
                    self.setDescrField(None)
            self.setSelectExpr("")
            
    def setDataClipFlag(self,flag):
        self.dataClipFlag = flag
            
    def setDataClipLayer(self,layer_path):
        self.clip_layer = layer_path
        
    def setSelectField(self,fieldname):
        utils.debug("Setting select_field to " + str(fieldname))
        self.select_field = fieldname
        
    def setDescrField(self,fieldname):
        utils.debug("Setting descr to " + str(fieldname))
        self.descr_field = fieldname
        
    def setSelectExpr(self,expr):
        self.select_expr = expr
        
    def checkLayerSelected(self):
        if not self.landuseLayer:
            utils.user_error("No layer selected")
            
    def checkFieldSelected(self):
        if not self.select_field:
            utils.user_error("No field selected")
            
    def getClipLayer(self):
        return self.fsModel.mkOutputFile("landuseClip.gpkg")
            
    def getSelectionLayer(self):
        return self.fsModel.mkOutputFile("landuseSelection.gpkg")
            
    def getDissolveLayer(self):
        return self.fsModel.mkOutputFile("landuseSelectionDissolve.gpkg")
        
    # def switchDataClipFlag(self,state):
        # utils.debug("switchDataClipFlag")
        # self.dataClipFlag = not self.dataClipFlag

    def mkSelectionExpr(self):
        expr = ""
        for item in self.items:
            if item.dict[LanduseFieldItem.TO_SELECT_FIELD]:
                if expr != "":
                    expr += " + "
                field_val = item.dict[LanduseFieldItem.VALUE_FIELD].replace("'","''")
                expr += "(\"" + self.select_field + "\" = '" + field_val + "')"
        utils.debug("selectionExpr = " + expr)
        return expr
        
    def getSelectionExpr(self):
        utils.debug("select mode = " + str(self.select_mode))
        utils.debug("items = " + str(self.items))
        if self.select_mode == self.SELECT_FIELD_MODE:
            expr = self.mkSelectionExpr()
            if not expr:
                utils.user_error("No value selected")
        elif self.select_mode == self.SELECT_EXPR_MODE:
            expr = self.select_expr
        else:
            utils.internal_error("Unexpected selection mode : " + str(self.select_mode))
        return expr
                
    def applyItemsWithContext(self,context,feedback):
        progress.progressFeedback.beginSection("Landuse classification")
        self.fsModel.checkWorkspaceInit()
        self.checkLayerSelected()
        self.checkFieldSelected()
        #in_layer = qgsUtils.pathOfLayer(self.landuseLayer)
        #clip_layer = self.fsModel.paramsModel.getTerritoryLayer()
        clip_layer = self.clip_layer if self.dataClipFlag else None
        utils.debug("clip_layer1 = " + str(self.clip_layer))
        utils.debug("dataflag = " + str(self.dataClipFlag))
        utils.debug("clip_layer = " + str(clip_layer))
        #clip_layer = self.fsModel.paramsModel.getTerritoryLayer()
        expr = self.getSelectionExpr()
        #if not expr:
        #    utils.user_error("No expression selected : TODO select everything")
        dissolveLayer = self.getDissolveLayer()
        qgsUtils.removeVectorLayer(dissolveLayer)
        parameters = { self.ALG_INPUT : self.landuseLayer,
                       self.ALG_CLIP_LAYER : clip_layer,
                       self.ALG_SELECT_EXPR : expr,
                       self.ALG_OUTPUT : dissolveLayer }
        res = qgsTreatments.applyProcessingAlg(
            "FragScape","prepareLanduse",parameters,
            context,feedback)
        qgsUtils.loadVectorLayer(dissolveLayer,loadProject=True)
        progress.progressFeedback.endSection()
        
    def toXML(self,indent=" "):
        if not self.landuseLayer:
            utils.warn("No layer selected")
            return ""
        if not self.select_field:
            utils.warn("No field selected")
            return ""
        #layerRelPath = self.fsModel.normalizePath(qgsUtils.pathOfLayer(self.landuseLayer))
        layerRelPath = self.fsModel.normalizePath(self.landuseLayer)
        attribs_dict = { self.INPUT_FIELD : layerRelPath,
                         self.SELECT_MODE_FIELD : self.select_mode }
        if self.dataClipFlag and self.clip_layer:
            attribs_dict[self.CLIP_LAYER] = self.fsModel.normalizePath(self.clip_layer)
        if self.select_field:
            attribs_dict[self.SELECT_FIELD_FIELD] = self.select_field
        if self.descr_field:
            attribs_dict[self.SELECT_DESCR_FIELD] = self.descr_field
        if self.select_mode == self.SELECT_EXPR_MODE:
            attribs_dict[self.SELECT_EXPR_FIELD] = self.select_expr
        xmlStr = super().toXML(indent,attribs_dict)
        return xmlStr
        
    def fromXMLAttribs(self,attribs):
        utils.debug("attribs = " + str(attribs))
        if self.INPUT_FIELD in attribs:
            abs_layer = self.fsModel.getOrigPath(attribs[self.INPUT_FIELD])
            utils.debug("abs_layer = " + str(abs_layer))
            self.landuseLayer = abs_layer
        if self.CLIP_LAYER in attribs:
            self.dataClipFlag = True
            self.clip_layer = self.fsModel.getOrigPath(attribs[self.CLIP_LAYER])
        if self.SELECT_MODE_FIELD in attribs:
            self.select_mode = int(attribs[self.SELECT_MODE_FIELD])
        if self.SELECT_FIELD_FIELD in attribs:
            utils.debug("sf1 = " + str(self.select_field))
            utils.debug("sf2 = " + str(attribs[self.SELECT_FIELD_FIELD]))
            self.select_field = attribs[self.SELECT_FIELD_FIELD]
        if self.SELECT_DESCR_FIELD in attribs:
            self.descr_field = attribs[self.SELECT_DESCR_FIELD]
        if self.SELECT_EXPR_FIELD in attribs:
            self.select_expr = attribs[self.SELECT_EXPR_FIELD]
        
    def fromXMLRoot(self,root):
        self.fromXMLAttribs(root.attrib)
        self.items = []
        for parsed_item in root:
            dict = parsed_item.attrib
            item = self.mkItemFromDict(dict)
            self.addItem(item)
        self.layoutChanged.emit()

        
class LanduseConnector(abstract_model.AbstractConnector):

    # SELECTION_MODE_FIELD = 0
    # SELECTION_MODE_EXPR = 1

    def __init__(self,dlg,landuseModel):
        self.dlg = dlg
        self.parser_name = "Landuse"
        self.dlg.landuseView.setItemDelegateForColumn(2,abstract_model.CheckBoxDelegate(self.dlg.landuseView))
        #landuse_model = LanduseModel()
        super().__init__(landuseModel,self.dlg.landuseView,
                         addButton=None,removeButton=self.dlg.landuseRemove,
                         runButton=self.dlg.landuseRun)
        
    def initGui(self):
        self.dlg.landuseInputLayerCombo.setFilters(QgsMapLayerProxyModel.VectorLayer)
        #self.dlg.landuseInputLayer.setFilter(qgsUtils.getVectorFilters())
        self.dlg.landuseDescrField.setFilters(QgsFieldProxyModel.String)
        
    def connectComponents(self):
        super().connectComponents()
        self.dlg.landuseInputLayerCombo.layerChanged.connect(self.setLayer)
        #self.dlg.landuseInputLayer.fileChanged.connect(self.loadLayer)
        self.layerComboDlg = qgsUtils.LayerComboDialog(self.dlg,
                                                       self.dlg.landuseInputLayerCombo,
                                                       self.dlg.landuseInputLayer)
        self.dlg.landuseSelectionMode.currentIndexChanged.connect(self.switchSelectionMode)
        self.dlg.landuseSelectField.fieldChanged.connect(self.model.setSelectField)
        self.dlg.landuseDescrField.fieldChanged.connect(self.model.setDescrField)
        self.dlg.landuseSelectExpr.fieldChanged.connect(self.model.setSelectExpr)
        self.dlg.landuseLoadFields.clicked.connect(self.loadFields)
        #self.dlg.landuseRun.clicked.connect(self.applyItems)
        self.dlg.landuseClipDataFlag.stateChanged.connect(self.switchDataClipFlag)
        self.dlg.landuseClipLayer.fileChanged.connect(self.model.setDataClipLayer)
        #self.dlg.landuseSelectionMode.activated.connect(self.switchSelectionMode)
        
    def switchDataClipFlag(self,state):
        utils.debug("switchDataClipFlag")
        if state == 0:
            self.model.dataClipFlag = False
        elif state == 2:
            self.model.dataClipFlag = True
        else:
            utils.internal_error("Unexpected check state : " + str(state))
        self.dlg.landuseClipLayer.setEnabled(self.model.dataClipFlag)
        
    def setLayerUI(self,layer):
        utils.debug("setlayerUI")
        if layer:
            #self.dlg.landuseInputLayerCombo.setLayer(layer)
            self.dlg.landuseSelectField.setLayer(layer)
            self.dlg.landuseDescrField.setLayer(layer)
            self.dlg.landuseSelectExpr.setLayer(layer)
        
    def setLayer(self,layer):
        utils.debug("setLayer")
        if layer:
            utils.debug("setLayer " + str(layer.type))
            layer_path = qgsUtils.pathOfLayer(layer)
            self.model.changeLayer(layer_path)
            self.setLayerUI(layer)
  
    # def loadLayer(self,path):
        # utils.debug("loadLayer")
        # loaded_layer = qgsUtils.loadVectorLayer(path,loadProject=True)
        # self.setLayer(loaded_layer)
        # self.dlg.landuseInputLayerCombo.setLayer(loaded_layer)
        
    def loadFields(self,fieldname):
        utils.debug("loadField")
        curr_layer = self.dlg.landuseInputLayerCombo.currentLayer()
        if not curr_layer:
            utils.internal_error("No layer selected in landuse tab")
        if not self.model.select_field:
            utils.user_error("No selection field selected")
        #fieldVals = qgsUtils.getLayerFieldUniqueValues(curr_layer,fieldname)
        new_items = []
        if self.model.descr_field:
            fieldsAssoc = qgsUtils.getLayerAssocs(curr_layer,self.model.select_field,self.model.descr_field)
            new_items = [ LanduseFieldItem(v,str(l)) for v, l in fieldsAssoc.items() ]
            # for k, descriptions in fieldsAssoc.items():
                # descr = descriptions.join(" -- ")
                # new_item = LanduseItem(k,descr=descr)
                # old_item = self.model.getMatchingItem(new_item)
                # if old_item:
                    # new_item[LanduseFieldItem.TO_SELECT_FIELD] = old_item[LanduseFieldItem.TO_SELECT_FIELD]
                # new_items.append(new_item)
        else:
            fieldVals = qgsUtils.getLayerFieldUniqueValues(curr_layer,self.model.select_field)
            new_items = [LanduseFieldItem(v) for v in fieldVals]
        for new_item in new_items:
            old_item = self.model.getMatchingItem(new_item)
            if old_item:
                new_item.dict[LanduseFieldItem.TO_SELECT_FIELD] = old_item.dict[LanduseFieldItem.TO_SELECT_FIELD]
        self.model.items = new_items
        self.model.layoutChanged.emit()
        # self.model.items = []
        # for fieldVal in fieldVals:
            # utils.debug("fieldVal : " + str(fieldVal))
            # item = LanduseFieldItem.fromVals(fieldVal,False)
            # self.model.addItem(item)
        # self.model.select_field = fieldname
        # self.model.layoutChanged.emit()
        
    def switchSelectionMode(self,index):
        utils.debug("switchSelectMode : " + str(index))
        if index == 0:
            self.dlg.landuseSelectionStack.setCurrentIndex(0)
            self.model.select_mode = LanduseModel.SELECT_FIELD_MODE
        elif index == 1:
            self.dlg.landuseSelectionStack.setCurrentIndex(1)
            self.model.select_mode = LanduseModel.SELECT_EXPR_MODE
        else:
            utils.internal_error("Unexpected index for landuse selection mode : " + str(index))
        
    def updateUI(self):
        if self.model.landuseLayer:
            loaded_layer = qgsUtils.loadVectorLayer(self.model.landuseLayer,loadProject=True)
            self.dlg.landuseInputLayerCombo.setLayer(loaded_layer)
        utils.debug("clipflag1" + str(self.model.dataClipFlag))
        if self.model.dataClipFlag:
            self.dlg.landuseClipDataFlag.setCheckState(2)
        else:
            self.dlg.landuseClipDataFlag.setCheckState(0)
        utils.debug("clipflag2" + str(self.model.dataClipFlag))
        if self.model.clip_layer:
            self.dlg.landuseClipLayer.setFilePath(self.model.clip_layer)
        if self.model.select_field:
            utils.debug("setting select_field : " + str(self.model.select_field))
            self.dlg.landuseSelectField.setField(self.model.select_field)
        if self.model.descr_field:
            self.dlg.landuseDescrField.setField(self.model.descr_field)
        if self.model.select_expr:
            self.dlg.landuseSelectExpr.setExpression(self.model.select_expr)
        if self.model.select_mode is not None:
            self.switchSelectionMode(self.model.select_mode)
        
    def fromXMLRoot(self,root):
        self.model.fromXMLRoot(root)
        self.updateUI()

    # def fromXMLAttribs(self,attribs):
        # attrib_fields = ["layer", "field"]
        # utils.checkFields(attrib_fields,attribs.keys())
        # abs_layer = self.model.fsModel.getOrigPath(attribs["layer"])
        # self.loadLayer(abs_layer)
        # self.dlg.select_fieldCombo.setField(attribs["field"])
        
    # def fromXMLRoot(self,root):
        # self.fromXMLAttribs(root.attrib)
        # self.model.items = []
        # for parsed_item in root:
            # dict = parsed_item.attrib
            # item = self.model.mkItemFromDict(dict)
            # self.model.addItem(item)
        # self.model.layoutChanged.emit()
        
    def toXML(self):
        return self.model.toXML()
    