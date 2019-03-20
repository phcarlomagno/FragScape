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

from .qgis_lib_mc import utils
from .steps import params, landuse, fragm,  reporting

class FragScapeModel:

    def __init__(self,context,feedback):
        self.context = None
        self.feedback = feedback
        utils.debug("feedback fs = " + str(feedback))
        self.paramsModel = params.ParamsModel(self)
        self.landuseModel = landuse.LanduseModel(self)
        self.fragmModel = fragm.FragmModel(self)
        self.reportingModel = reporting.ReportingModel(self)
        self.parser_name = "FragScapeModel"
        
    def checkWorkspaceInit(self):
        self.paramsModel.checkWorkspaceInit()
            
    # Returns relative path w.r.t. workspace directory.
    # File separator is set to common slash '/'.
    def normalizePath(self,path):
        return self.paramsModel.normalizePath(path)
            
    # Returns absolute path from normalized path (cf 'normalizePath' function)
    def getOrigPath(self,path):
        return self.paramsModel.getOrigPath(path)
    
    def mkOutputFile(self,name):
        return self.paramsModel.mkOutputFile(name)
        
    def runModel(self):
        utils.debug("feedback fs rm = " + str(self.feedback))
        self.landuseModel.applyItemsWithContext(self.context,self.feedback)
        self.fragmModel.applyItemsWithContext(self.context,self.feedback)
        self.reportingModel.runReportingWithContext(self.context,self.feedback)
        
    def toXML(self,indent=""):
        xmlStr = indent + "<" + self.parser_name + ">"
        new_indent = " "
        if self.paramsModel:
            xmlStr += "\n" + self.paramsModel.toXML(indent=new_indent)
        if self.landuseModel:
            xmlStr += "\n" + self.landuseModel.toXML(indent=new_indent)
        if self.fragmModel:
            xmlStr += "\n" + self.fragmModel.toXML(indent=new_indent)
        if self.reportingModel:
            xmlStr += "\n" + self.reportingModel.toXML(indent=new_indent)
        xmlStr += "\n" + indent + "</" + self.parser_name + ">"
        return xmlStr
        
    def fromXMLRoot(self,root):
        for child in root:
            utils.debug("tag = " + str(child.tag))
            if child.tag == self.paramsModel.parser_name:
                self.paramsModel.fromXMLRoot(child)
                self.paramsModel.layoutChanged.emit()
            elif child.tag == self.landuseModel.parser_name:
                self.landuseModel.fromXMLRoot(child)
                self.landuseModel.layoutChanged.emit()
            elif child.tag == self.fragmModel.parser_name:
                self.fragmModel.fromXMLRoot(child)
                self.fragmModel.layoutChanged.emit()
            elif child.tag == self.reportingModel.parser_name:
                self.reportingModel.fromXMLRoot(child)
                self.reportingModel.layoutChanged.emit()
        
    