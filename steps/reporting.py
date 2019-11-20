# -*- coding: utf-8 -*-
"""
/***************************************************************************
 FragScape
                                 A QGIS plugin
 This plugin computes mesh effective size
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2018-11-05
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Mathieu Chailloux
        email                : mathieu@chailloux.org
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

import os.path

from qgis.core import QgsMapLayerProxyModel, QgsField, QgsFeature, QgsProcessingFeedback, QgsVectorLayerCache
from qgis.gui import QgsFileWidget, QgsAttributeTableModel, QgsAttributeTableView, QgsAttributeTableFilterModel
from qgis.utils import iface
from PyQt5.QtCore import QVariant
from processing import QgsProcessingUtils

from ..qgis_lib_mc import utils, abstract_model, qgsUtils, feedbacks, qgsTreatments
from ..algs import FragScape_algs
from . import params, fragm

class ReportingModel(abstract_model.DictModel):

    # Configuration slots
    INPUT = "input_layer"
    SELECT_EXPR = "select_expr"
    REPORTING = "reporting_layer"
    METHOD = "method"
    UNIT = "unit"
    OUTPUT = "output"
    
    CUT_METHOD = 0
    CBC_METHOD = 1

    def __init__(self,fsModel):
        self.parser_name = "Reporting"
        self.fsModel = fsModel
        self.input_layer = None
        self.select_expr = None
        self.reporting_layer = None
        self.method = self.CUT_METHOD
        self.unit = 0
        self.out_layer = None
        self.init_fields = []
        self.fields = self.init_fields
        super().__init__(self,self.fields)
        #super().__init__(self,self.fields)
                
    def getInputLayer(self):
        #return self.fsModel.fragmModel.getFinalLayer()
        if not self.input_layer:
            self.input_layer = self.fsModel.fragmModel.getFinalLayer()
        return self.input_layer
                
    def setOutLayer(self,layer_path):
        self.out_layer = layer_path
        #self.out_layer = self.fsModel.normalizePath(layer_path)
        
    def getOutLayer(self):
        if self.out_layer:
            return self.fsModel.getOrigPath(self.out_layer)
        else:
            return params.mkTmpLayerPath("reportingResults.gpkg")
        
    def mkIntersectionLayer(self):
        pass
        
    def getIntersectionLayerPath(self):
        return self.fsModel.mkOutputFile("reportingIntersection.gpkg")
        
    def getReportingResultsLayerPath(self):
        return self.fsModel.mkOutputFile("reportingResults.gpkg")
                
    def runReportingWithContext(self,context,feedback):
        reportingMsg = "Reporting layer computation"
        feedbacks.progressFeedback.beginSection(reportingMsg)
        input_layer = self.getInputLayer()
        #if self.select_expr:
        if False:
            select_path = params.mkTmpLayerPath("reportingSelection.gpkg")
            qgsUtils.removeVectorLayer(select_path)
            qgsTreatments.extractByExpression(input_layer,self.select_expr,select_path,None,feedback)
            selected = select_path
        else:
            selected = input_layer
        crs = self.fsModel.paramsModel.crs
        results_path = self.getOutLayer()
        global_results_path = params.mkTmpLayerPath("reportingResultsGlobal.gpkg")
        qgsUtils.removeVectorLayer(results_path)
        qgsUtils.removeVectorLayer(global_results_path)
        if self.method == self.CUT_METHOD:
            cut_mode = True
        elif self.method == self.CBC_METHOD:
            cut_mode = False
        else:
            utils.internal_error("Unexpected method : " + str(self.method))
        parameters1 = { FragScape_algs.EffectiveMeshSizeReportingAlgorithm.INPUT : selected,
                       FragScape_algs.EffectiveMeshSizeReportingAlgorithm.SELECT_EXPR : self.select_expr,
                       FragScape_algs.EffectiveMeshSizeReportingAlgorithm.REPORTING : self.reporting_layer,
                       FragScape_algs.EffectiveMeshSizeReportingAlgorithm.CRS : crs,
                       FragScape_algs.EffectiveMeshSizeReportingAlgorithm.CUT_MODE : cut_mode,
                       FragScape_algs.EffectiveMeshSizeReportingAlgorithm.UNIT : self.unit,
                       FragScape_algs.EffectiveMeshSizeReportingAlgorithm.OUTPUT : results_path }
        res1 = qgsTreatments.applyProcessingAlg(
            FragScape_algs.FragScapeAlgorithmsProvider.NAME,
            FragScape_algs.EffectiveMeshSizeReportingAlgorithm.ALG_NAME,
            parameters1,context=context,feedback=feedback,onlyOutput=False)
        #qgsUtils.loadVectorLayer(results_path,loadProject=True)
        #dissolved_path = params.mkTmpLayerPath("reporting_dissolved.gpkg")
        #dissolved = qgsTreatments.dissolveLayer(self.reporting_layer,dissolved_path,context,feedback)
        parameters2 = { FragScape_algs.EffectiveMeshSizeGlobalAlgorithm.INPUT : selected,
                       FragScape_algs.EffectiveMeshSizeGlobalAlgorithm.SELECT_EXPR : self.select_expr,
                       FragScape_algs.EffectiveMeshSizeGlobalAlgorithm.BOUNDARY : self.reporting_layer,
                       FragScape_algs.EffectiveMeshSizeGlobalAlgorithm.CRS : crs,
                       FragScape_algs.EffectiveMeshSizeGlobalAlgorithm.CUT_MODE : cut_mode,
                       FragScape_algs.EffectiveMeshSizeReportingAlgorithm.UNIT : self.unit,
                       FragScape_algs.EffectiveMeshSizeGlobalAlgorithm.OUTPUT : global_results_path }
        res2 = qgsTreatments.applyProcessingAlg(
            FragScape_algs.FragScapeAlgorithmsProvider.NAME,
            FragScape_algs.EffectiveMeshSizeGlobalAlgorithm.ALG_NAME,
            parameters2,
            context=context,feedback=feedback,onlyOutput=False)
        # global_layer = qgsUtils.loadVectorLayer(global_results_path)
        # if global_layer.featureCount() != 1:
            # utils.internal_error("Unexpected number of features for global reporting layer "
                                  # + str(global_results_path) + " : " + str(global_layer.featureCount()))
        # for f in global_layer.dataProvider().getFeatures():
            # global_meff = f[FragScape_algs.EffectiveMeshSizeAlgorithm.MESH_SIZE]
        #global_meff = res[FragScape_algs.EffectiveMeshSizeAlgorithm.OUTPUT_GLOBAL_MEFF]
        #out_path = res[FragScape_algs.EffectiveMeshSizeAlgorithm.OUTPUT]
        feedbacks.progressFeedback.endSection()
        return (res1,res2)
                
    def toXML(self,indent=" "):
        # if not self.reporting_layer:
            # utils.warn("No reporting layer selected")
            # return ""
        #layerRelPath = self.fsModel.normalizePath(qgsUtils.pathOfLayer(self.layer))
        modelParams = {}
        # if self.input_layer:
            # pass
        if self.select_expr:
            modelParams[self.SELECT_EXPR] = self.select_expr
        if self.method >= 0:
            modelParams[self.METHOD] = self.method
        if self.unit:
            modelParams[self.UNIT] = self.unit
        if self.reporting_layer:
            layerRelPath = self.fsModel.normalizePath(self.reporting_layer)
            modelParams[self.REPORTING] = layerRelPath
        if self.out_layer:
            modelParams[self.OUTPUT] = self.fsModel.normalizePath(self.out_layer)
        xmlStr = super().toXML(indent,modelParams)
        return xmlStr
        
    def fromXMLAttribs(self,attribs):
        if self.SELECT_EXPR in attribs:
            self.select_expr = attribs[self.SELECT_EXPR]
        if self.REPORTING in attribs:
            self.reporting_layer = self.fsModel.getOrigPath(attribs[self.REPORTING])
        if self.METHOD in attribs:
            self.method = int(attribs[self.METHOD])
        if self.UNIT in attribs:
            self.unit = int(attribs[self.UNIT])
        if self.OUTPUT in attribs:
            out_layer = self.fsModel.getOrigPath(attribs[self.OUTPUT])
            self.setOutLayer(out_layer)
        
    def fromXMLRoot(self,root):
        self.fromXMLAttribs(root.attrib)
        
class ReportingConnector(abstract_model.AbstractConnector):

    
    def __init__(self,dlg,reportingModel):
        self.dlg = dlg
        self.parser_name = "Reporting"
        #self.model = reportingModel
        #reportingModel = ReportingModel()
        super().__init__(reportingModel,self.dlg.resultsView)
        
    def initGui(self):
        self.dlg.resultsInputLayer.setFilters(QgsMapLayerProxyModel.VectorLayer)
        self.dlg.resultsReportingLayer.setStorageMode(QgsFileWidget.GetFile)
        self.dlg.resultsReportingLayer.setFilter(qgsUtils.getVectorFilters())
        self.dlg.resultsOutLayer.setStorageMode(QgsFileWidget.SaveFile)
        self.dlg.resultsOutLayer.setFilter(qgsUtils.getVectorFilters())
        #self.attrView = QgsAttributeTableView(self.dlg)
        #self.dlg.gridLayout_9.removeWidget(self.dlg.resultsView)
       # self.dlg.gridLayout_9.addWidget(self.attrView)
        #self.dlg.resultsView.hide()
        #self.dlg.gridLayout_9.removeWidget(self.dlg.resultsView)
        
    def connectComponents(self):
        super().connectComponents()
        #self.dlg.reportingLayerCombo.layerChanged.connect(self.setLayer)
        self.dlg.resultsInputLayer.layerChanged.connect(self.setInputLayer)
        self.dlg.resultsSelection.fieldChanged.connect(self.setSelectExpr)
        self.dlg.resultsReportingLayer.fileChanged.connect(self.setReportingLayer)
        self.dlg.resultsCutMode.currentIndexChanged.connect(self.setMethod)
        self.dlg.resultsUnit.currentIndexChanged.connect(self.setUnit)
        self.dlg.resultsOutLayer.fileChanged.connect(self.model.setOutLayer)
        self.dlg.resultsRun.clicked.connect(self.runReporting)
        
    def runReporting(self):
        (res1, res2) = self.model.runReportingWithContext(self.dlg.context,self.dlg.feedback)
        out_path = res1[FragScape_algs.EffectiveMeshSizeGlobalAlgorithm.OUTPUT]
        out_global_meff = res2[FragScape_algs.EffectiveMeshSizeGlobalAlgorithm.OUTPUT_GLOBAL_MEFF]
        # UI update
        self.dlg.resultsGlobalRes.setText(str(out_global_meff))
        self.loaded_layer = qgsUtils.loadVectorLayer(out_path,loadProject=True)
        self.layer_cache = QgsVectorLayerCache(self.loaded_layer,24)
        self.attribute_model = QgsAttributeTableModel(self.layer_cache)
        self.attribute_model.loadLayer()
        self.dlg.resultsView.setModel(self.attribute_model)
        self.dlg.resultsView.show()
        
    def unloadResults(self):
        self.dlg.resultsGlobalRes.setText(str(0))
        self.loaded_layer = None
        self.layer_cache = None
        self.attribute_model = None
        #self.model.items = []
        self.dlg.resultsView.setModel(None)
        
        
    # def setLayer(self,layer):
        # utils.debug("setLayer " + str(layer.type))
        # self.dlg.reportingLayerCombo.setLayer(layer)
        # self.model.reporting_layer = qgsUtils.pathOfLayer(layer)
    
    def setMethod(self,idx):
        if idx == 0:
            self.model.method = ReportingModel.CUT_METHOD
        elif idx == 1:
            self.model.method = ReportingModel.CBC_METHOD
        else:
            utils.internal_error("Unexpected index for reporting method : " + str(idx))
            
    def setUnit(self,idx):
        self.model.unit = idx
    
    def setInputLayer(self,layer):
        utils.debug("setInputLayer to " + str(layer))
        self.dlg.resultsSelection.setLayer(layer)
        self.unloadResults()
        #self.dlg.resultsSelection.setLayer(loaded_layer)
        self.model.input_layer = qgsUtils.pathOfLayer(layer)
        
    def setSelectExpr(self,expr):
        self.model.select_expr = expr
        
    def setReportingLayer(self,path):
        utils.debug("setReportingLayer")
        #loaded_layer = qgsUtils.loadVectorLayer(path,loadProject=True)
        #self.dlg.reportingLayerCombo.setLayer(loaded_layer)
        #self.dlg.resultsSelection.setLayer(loaded_layer)
        self.model.reporting_layer = path
        #self.setLayer(loaded_layer)
        
    def updateUI(self):
        abs_input_layer = self.model.getInputLayer()
        utils.debug("")
        if os.path.isfile(abs_input_layer):
            loaded_layer = qgsUtils.loadVectorLayer(abs_input_layer,loadProject=True)
            self.dlg.resultsInputLayer.setLayer(loaded_layer)
        else:
            utils.warn("Could not find results input layer : " + str(abs_input_layer))
        if self.model.select_expr:
            self.dlg.resultsSelection.setExpression(self.model.select_expr)
        if self.model.reporting_layer:
            #qgsUtils.loadVectorLayer(self.model.reporting_layer,loadProject=True)
            self.dlg.resultsReportingLayer.setFilePath(self.model.reporting_layer)
        if self.model.method:
            self.dlg.resultsCutMode.setCurrentIndex(int(self.model.method))
        if self.model.unit:
            self.dlg.resultsUnit.setCurrentIndex(int(self.model.unit))
        if self.model.out_layer:
            self.dlg.resultsOutLayer.setFilePath(self.model.out_layer)

    def fromXMLRoot(self,root):
        self.model.fromXMLRoot(root)
        self.updateUI()
        
    def toXML(self,indent=" "):
        return self.model.toXML()
        