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

from PyQt5.QtCore import QCoreApplication, QVariant
from qgis.core import QgsProcessing, QgsProcessingAlgorithm, QgsProcessingException
from qgis.core import (QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterExpression,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingProvider,
                       QgsProcessingParameterMultipleLayers,
                       QgsProcessingUtils,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterMatrix,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterCrs,
                       QgsProcessingParameterVectorDestination,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterString,
                       QgsProcessingParameterEnum,
                       QgsProperty,
                       QgsWkbTypes,
                       QgsProcessingMultiStepFeedback)
from qgis.core import QgsField, QgsFields, QgsFeature, QgsFeatureSink

import processing
import xml.etree.ElementTree as ET

from ..qgis_lib_mc import utils, qgsTreatments, qgsUtils, feedbacks
from ..steps import params

class FragScapeAlgorithmsProvider(QgsProcessingProvider):

    NAME = "FragScape"

    def __init__(self):
        self.alglist = [PrepareLanduseAlgorithm(),
                        PrepareFragmentationAlgorithm(),
                        ApplyFragmentationAlgorithm(),
                        #ReportingIntersection(),
                        EffectiveMeshSizeReportingAlgorithm(),
                        EffectiveMeshSizeGlobalAlgorithm()]
        for a in self.alglist:
            a.initAlgorithm()
        super().__init__()
        
    def unload(self):
        pass
        
    def id(self):
        return self.NAME
        
    def name(self):
        return self.NAME
        
    def longName(self):
        return self.name()
        
    def loadAlgorithms(self):
        for a in self.alglist:
            self.addAlgorithm(a)
            
            
class PrepareLanduseAlgorithm(QgsProcessingAlgorithm):

    ALG_NAME = "prepareLanduse"

    INPUT = "INPUT"
    CLIP_LAYER = "CLIP_LAYER"
    SELECT_EXPR = "SELECT_EXPR"
    OUTPUT = "OUTPUT"

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return PrepareLanduseAlgorithm()
        
    def name(self):
        return self.ALG_NAME
        
    def displayName(self):
        return self.tr("1 - Prepare land cover data")
        
    def shortHelpString(self):
        return self.tr("This algorithms prepares land cover data by applying selection (from expression) and dissolving geometries")

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr("Input layer"),
                [QgsProcessing.TypeVectorAnyGeometry]))
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.CLIP_LAYER,
                description=self.tr("Clip layer"),
                types=[QgsProcessing.TypeVectorPolygon],
                optional=True))
        self.addParameter(
            QgsProcessingParameterExpression(
                self.SELECT_EXPR,
                self.tr("Selection expression"),
                "",
                self.INPUT))
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("Output layer")))
                
    def processAlgorithm(self,parameters,context,feedback):
        # Dummy function to enable running an alg inside an alg
        # def no_post_process(alg, context, feedback):
            # pass
        input = self.parameterAsVectorLayer(parameters,self.INPUT,context)
        feedback.pushDebugInfo("input = " + str(input))
        if input is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
        qgsUtils.normalizeEncoding(input)
        feedback.pushDebugInfo("input ok")
        clip_layer = self.parameterAsVectorLayer(parameters,self.CLIP_LAYER,context)
        expr = self.parameterAsExpression(parameters,self.SELECT_EXPR,context)
        select_layer = params.mkTmpLayerPath("select.gpkg")
        feedback.pushDebugInfo("select_layer = " + str(select_layer))
        if clip_layer is None:
            clipped = input
        else:
            clipped_path = params.mkTmpLayerPath('landuseClipped.gpkg')
            qgsTreatments.applyVectorClip(input,clip_layer,clipped_path,context,feedback)
            clipped = qgsUtils.loadVectorLayer(clipped_path)
            feedback.pushDebugInfo("clipped  = " + str(clipped))
            #clipped = clipped_path
        selected_path = params.mkTmpLayerPath('landuseSelection.gpkg')
        qgsTreatments.selectGeomByExpression(clipped,expr,selected_path,'landuseSelection')
        #selected = qgsUtils.loadVectorLayer(selected_path)
        #selected = qgsTreatments.extractByExpression(
        #    clipped,expr,'memory:',
        #    context=context,feedback=feedback)
        feedback.pushDebugInfo("selected = " + str(selected_path))
        output = parameters[self.OUTPUT]
        dissolved = qgsTreatments.dissolveLayer(selected_path,output,context=context,feedback=feedback)
        dissolved = None
        return {self.OUTPUT : dissolved}
        
        
class PrepareFragmentationAlgorithm(QgsProcessingAlgorithm):

    ALG_NAME = "prepareFragm"

    INPUT = "INPUT"
    CLIP_LAYER = "CLIP_LAYER"
    SELECT_EXPR = "SELECT_EXPR"
    BUFFER = "BUFFER_EXPR"
    NAME = "NAME"
    OUTPUT = "OUTPUT"
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return PrepareFragmentationAlgorithm()
        
    def name(self):
        return self.ALG_NAME
        
    def displayName(self):
        return self.tr("2.1 - Prepare fragmentation data")
        
    def shortHelpString(self):
        return self.tr("This algorithm prepares a fragmentation layer by applying clip, selection and buffer")

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                description=self.tr("Input layer"),
                types=[QgsProcessing.TypeVectorLine]))
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.CLIP_LAYER,
                description=self.tr("Clip layer"),
                types=[QgsProcessing.TypeVectorPolygon],
                optional=True))
        self.addParameter(
            QgsProcessingParameterExpression(
                self.SELECT_EXPR,
                description=self.tr("Selection expression"),
                parentLayerParameterName=self.INPUT,
                optional=True))
        self.addParameter(
            QgsProcessingParameterExpression(
                self.BUFFER,
                description=self.tr("Buffer expression"),
                parentLayerParameterName=self.INPUT,
                optional=True))
        self.addParameter(
            QgsProcessingParameterString(
                self.NAME,
                description=self.tr("Identifier"),
                optional=True))
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                description=self.tr("Output layer")))
                
    def processAlgorithm(self,parameters,context,feedback):
        # Parameters
        #assert(False)
        feedback.pushDebugInfo("parameters = " + str(parameters))
        input = self.parameterAsVectorLayer(parameters,self.INPUT,context)
        if input is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
        qgsUtils.normalizeEncoding(input)
        #input = qgsUtils.loadVectorLayer(parameters[self.INPUT])
        clip = self.parameterAsVectorLayer(parameters,self.CLIP_LAYER,context)
        clip_flag = (clip is None)
        select_expr = self.parameterAsExpression(parameters,self.SELECT_EXPR,context)
        #feedback.pushDebugInfo("select_expr : " + str(select_expr))
        #feedback.pushDebugInfo("select_expr type : " + str(type(select_expr)))
        buffer_expr = self.parameterAsExpression(parameters,self.BUFFER,context)
        name = self.parameterAsString(parameters,self.NAME,context)
        if not name:
            name = 'fragm'
        #buffer_expr = ""
        #feedback.pushDebugInfo("buffer_expr : " + str(buffer_expr))
        #if buffer_expr == "" and input.geometryType() != QgsWkbTypes.PolygonGeometry:
        #    raise QgsProcessingException("Empty buffer with non-polygon layer")
        output = parameters[self.OUTPUT]
        if clip is None:
            clipped = input
        else:
            clipped_path = params.mkTmpLayerPath(name + 'Clipped.gpkg')
            qgsTreatments.applyVectorClip(input,clip,clipped_path,context,feedback)
            clipped = qgsUtils.loadVectorLayer(clipped_path)
        if select_expr == "":
            selected = clipped
        else:
            selected_path = params.mkTmpLayerPath(name + 'Selected.gpkg')
            qgsTreatments.selectGeomByExpression(clipped,select_expr,selected_path,name)
            #selected = qgsUtils.loadVectorLayer(selected_path)
            selected = selected_path
            #selected = qgsTreatments.extractByExpression(clipped,select_expr,'memory:',context,feedback)
        if buffer_expr == "":
            buffered = selected
        else:
            buffer_expr_prep = QgsProperty.fromExpression(buffer_expr)
            buffered = qgsTreatments.applyBufferFromExpr(selected,buffer_expr_prep,output,context,feedback)
        #buffered = qgsTreatments.applyBufferFromExpr(selected,parameters[self.BUFFER],output,context,feedback)
        if buffered == input:
            buffered = qgsUtils.pathOfLayer(buffered)
        return {self.OUTPUT : buffered}
        

        
class ApplyFragmentationAlgorithm(QgsProcessingAlgorithm):

    ALG_NAME = "applyFragm"

    LANDUSE = "LANDUSE"
    FRAGMENTATION = "FRAGMENTATION"
    CRS = "CRS"
    OUTPUT = "OUTPUT"

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return ApplyFragmentationAlgorithm()
        
    def name(self):
        return self.ALG_NAME
        
    def displayName(self):
        return self.tr("2.2 - Apply fragmentation")
        
    def shortHelpString(self):
        return self.tr("This algorithm builds a layer of patches from a land cover layer and fragmentation layers. Overlaying geometries are removed and remaining ones are cast to single geometry type.")

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.LANDUSE,
                self.tr("Land cover layer"),
                [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.FRAGMENTATION,
                self.tr("Fragmentation layers"),
                QgsProcessing.TypeVectorPolygon))
        self.addParameter(
            QgsProcessingParameterCrs(
                self.CRS,
                description=self.tr("Output CRS"),
                defaultValue=params.defaultCrs))
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("Output layer")))
                
    def processAlgorithm(self,parameters,context,feedback):
        # Parameters
        #feedback.pushInfo("parameters = " + str(parameters))
        landuse = self.parameterAsVectorLayer(parameters,self.LANDUSE,context)
        if landuse is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.LANDUSE))
        qgsUtils.normalizeEncoding(landuse)
        fragm_layers = self.parameterAsLayerList(parameters,self.FRAGMENTATION,context)
        #output = self.parameterAsOutputLayer(parameters,self.OUTPUT,context)
        crs = self.parameterAsCrs(parameters,self.CRS,context)
        output = parameters[self.OUTPUT]
        # Merge fragmentation layers
        fragm_path = params.mkTmpLayerPath("fragm.gpkg")
        fragm_layer = qgsTreatments.mergeVectorLayers(fragm_layers,crs,fragm_path)
        feedback.pushDebugInfo("fragm_layer = " + str(fragm_layer))
        if fragm_layer is None:
            raise QgsProcessingException("Fragmentation layers merge failed")
        # Apply difference
        diff_layer = qgsTreatments.applyDifference(
            landuse,fragm_layer,'memory:',
            context=context,feedback=feedback)
        if fragm_layer is None:
            raise QgsProcessingException("Difference landuse/fragmentation failed")
        # Multi to single part
        singleGeomLayer = qgsTreatments.multiToSingleGeom(
            diff_layer,output,
            context=context,feedback=feedback)
        if fragm_layer is None:
            raise QgsProcessingException("Multi to single part failed")
        return {self.OUTPUT : singleGeomLayer}
        
                
class ReportingIntersection(QgsProcessingAlgorithm):

    INPUT = "INPUT"
    REPORTING = "REPORTING"
    OUTPUT = "OUTPUT"
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return ReportingIntersection()
        
    def name(self):
        return "reportingIntersection"
        
    def displayName(self):
        return self.tr("3.1 - Reporting Intersection")
        
    def shortHelpString(self):
        return self.tr("Computes intersections with each reporting unit")

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr("Input layer"),
                [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.REPORTING,
                self.tr("Reporting layer"),
                [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("Output layer")))
                
    def processAlgorithm(self,parameters,context,feedback):
        feedback.pushDebugInfo("begin")
        # Parameters
        source = self.parameterAsVectorLayer(parameters,self.INPUT,context)
        feedback.pushDebugInfo("source = " + str(source))
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
        reporting = self.parameterAsVectorLayer(parameters,self.REPORTING,context)
        feedback.pushDebugInfo("reporting = " + str(reporting))
        if reporting is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.REPORTING))
        patch_id_field = QgsField("patch_id", QVariant.Int)
        report_id_field = QgsField("report_id", QVariant.Int)
        area_field = QgsField("area", QVariant.Double)
        report_area_field = QgsField("report_area", QVariant.Double)
        output_fields = QgsFields()
        output_fields.append(patch_id_field)
        output_fields.append(report_id_field)
        output_fields.append(area_field)
        output_fields.append(report_area_field)
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            output_fields,
            reporting.wkbType(),
            reporting.sourceCrs()
        )
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))
        # progress step
        nb_feats = source.featureCount() * reporting.featureCount()
        if nb_feats == 0:
            raise QgsProcessingException("Empty layers")
        progress_step = 100.0 / nb_feats
        curr_step = 0
        # gna gna
        for f in source.getFeatures():
            f_geom = f.geometry()
            f_area = f_geom.area()
            patches_area_sum = 0
            for report_feat in  reporting.getFeatures():
                report_geom = report_feat.geometry()
                report_area = report_geom.area()
                if f_geom.intersects(report_geom):
                    intersection = f_geom.intersection(report_geom)
                    intersection_area = intersection.area()
                    #f_area2 = pow(f_area,2)
                    #intersection_area2 = pow(intersection_area,2)
                    f_area_cbc = intersection_area * (f_area - intersection_area)
                    patches_area_sum += f_area_cbc
                    new_f = QgsFeature(output_fields)
                    new_f["patch_id"] = f.id()
                    new_f["report_id"] = report_feat.id()
                    new_f["area"] = f_area
                    new_f["report_area"] = intersection_area
                    new_f.setGeometry(f_geom)
                    sink.addFeature(new_f,QgsFeatureSink.FastInsert)
                    curr_step += 1
                    feedback.setProgress(int(curr_step * progress_step))
            #coh = patches_area_sum / f_area
            #utils.debug("coh = " + str(coh))
        return {self.OUTPUT: dest_id}


class EffectiveMeshSizeGlobalAlgorithm(QgsProcessingAlgorithm):

    ALG_NAME = "effectiveMeshSizeGlobal"

    # Algorithm parameters
    INPUT = "INPUT"
    SELECT_EXPR = "SELECT_EXPR"
    BOUNDARY = "BOUNDARY"
    CRS = "CRS"
    CUT_MODE = "CUT_MODE"
    UNIT = "UNIT"
    OUTPUT = "OUTPUT"
    
    UNIT_DIVISOR = [1, 100, 10000, 1000000]
    
    OUTPUT_GLOBAL_MEFF = "GLOBAL_MEFF"
    
    # Output layer fields
    ID = "fid"
    NB_PATCHES = "nb_patches"
    REPORT_AREA = "report_area"
    INTERSECTING_AREA = "intersecting_area"
    # Main measures
    MESH_SIZE = "effective_mesh_size"
    DIVI = "landscape_division"
    SPLITTING_INDEX = "splitting_index"
    # Auxiliary measures
    COHERENCE = "coherence"
    SPLITTING_DENSITY = "splitting_density"
    NET_PRODUCT = "net_product"
    
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return EffectiveMeshSizeGlobalAlgorithm()
        
    def name(self):
        return self.ALG_NAME
        
    def displayName(self):
        return self.tr("Effective mesh size (Boundary)")
        
    def shortHelpString(self):
        return self.tr("Computes effective mesh size from boundary layer")

    def initAlgorithm(self, config=None):
        self.unit_options = [
            self.tr("m² (square meters)"),
            self.tr("dm² (square decimeters / ares)"),
            self.tr("hm² (square hectometers / hectares)"),
            self.tr("km² (square kilometers)")]
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr("Input layer"),
                [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(
            QgsProcessingParameterExpression(
                self.SELECT_EXPR,
                self.tr("Filter expression"),
                optional=True))
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.BOUNDARY,
                self.tr("Boundary layer"),
                [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(
            QgsProcessingParameterCrs(
                self.CRS,
                description=self.tr("Output CRS"),
                defaultValue=params.defaultCrs))
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.CUT_MODE,
                self.tr("Cross-boundary connection method")))
        self.addParameter(
            QgsProcessingParameterEnum(
                self.UNIT,
                description=self.tr("Report areas unit"),
                options=self.unit_options))
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("Output layer")))
                
    def processAlgorithm(self,parameters,context,feedback):
        feedback.pushDebugInfo("Start " + str(self.name()))
        # Parameters
        source = self.parameterAsVectorLayer(parameters,self.INPUT,context)
        feedback.pushDebugInfo("source = " + str(source))
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
        select_expr = self.parameterAsExpression(parameters,self.SELECT_EXPR,context)
        boundary = self.parameterAsVectorLayer(parameters,self.BOUNDARY,context)
        feedback.pushDebugInfo("boundary = " + str(boundary))
        if boundary is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.BOUNDARY))
        crs = self.parameterAsCrs(parameters,self.CRS,context)
        cut_mode = self.parameterAsBool(parameters,self.CUT_MODE,context)
        unit = self.parameterAsEnum(parameters,self.UNIT,context)
        utils.debug("unit : " + str(unit))
        unit_divisor = self.UNIT_DIVISOR[unit]
        utils.debug("unit divisor : " + str(unit_divisor))
        # CRS reprojection
        source_crs = source.crs().authid()
        boundary_crs = boundary.crs().authid()
        feedback.pushDebugInfo("source_crs = " + str(source_crs))
        feedback.pushDebugInfo("boundary_crs = " + str(boundary_crs))
        feedback.pushDebugInfo("crs = " + str(crs.authid()))
        if source_crs != crs.authid():
            source_path = params.mkTmpLayerPath('res_source_reproject.gpkg')
            qgsTreatments.applyReprojectLayer(source,crs,source_path,context,feedback)
            source = qgsUtils.loadVectorLayer(source_path)
        if boundary_crs != crs.authid():
            boundary_path = params.mkTmpLayerPath('res_boundary_reproject.gpkg')
            qgsTreatments.applyReprojectLayer(boundary,crs,boundary_path,context,feedback)
            boundary = qgsUtils.loadVectorLayer(boundary_path)
        # Clip
        if cut_mode:
            clipped_path = params.mkTmpLayerPath('res_source_clipped.gpkg')
            qgsTreatments.applyVectorClip(source,boundary,clipped_path,context,feedback)
            sg_path = params.mkTmpLayerPath('res_source_single_geom.gpkg')
            qgsTreatments.multiToSingleGeom(clipped_path,sg_path,context,feedback)
            source = qgsUtils.loadVectorLayer(sg_path)
        else:
            intersected_path = params.mkTmpLayerPath('res_source_intersected.gpkg')
            qgsTreatments.selectIntersection(source,boundary,context,feedback)
            qgsTreatments.saveSelectedFeatures(source,intersected_path,context,feedback)
            source = qgsUtils.loadVectorLayer(intersected_path)
        # Selected
        if select_expr:# != "":
            selected_path = params.mkTmpLayerPath('res_source_selected.gpkg')
            qgsTreatments.extractByExpression(source,select_expr,selected_path,context,feedback)
            source = qgsUtils.loadVectorLayer(selected_path)
        # Dissolve
        if boundary.featureCount() > 1:
            dissolved_path = params.mkTmpLayerPath('res_boundary_dissolved.gpkg')
            qgsTreatments.dissolveLayer(boundary,dissolved_path,context,feedback)
            boundary = qgsUtils.loadVectorLayer(dissolved_path)
        # Output fields
        report_id_field = QgsField(self.ID, QVariant.Int)
        nb_patches_field = QgsField(self.NB_PATCHES, QVariant.Int)
        report_area_field = QgsField(self.REPORT_AREA, QVariant.Double)
        intersecting_area_field = QgsField(self.INTERSECTING_AREA, QVariant.Double)
        mesh_size_field = QgsField(self.MESH_SIZE, QVariant.Double)
        div_field = QgsField(self.DIVI, QVariant.Double)
        split_index_field = QgsField(self.SPLITTING_INDEX, QVariant.Double)
        coherence_field = QgsField(self.COHERENCE, QVariant.Double)
        split_density_field = QgsField(self.SPLITTING_DENSITY, QVariant.Double)
        net_product_field = QgsField(self.NET_PRODUCT, QVariant.Double)
        output_fields = QgsFields()
        output_fields.append(report_id_field)
        output_fields.append(nb_patches_field)
        output_fields.append(report_area_field)
        output_fields.append(intersecting_area_field)
        output_fields.append(mesh_size_field)
        output_fields.append(div_field)
        output_fields.append(split_index_field)
        output_fields.append(coherence_field)
        output_fields.append(split_density_field)
        output_fields.append(net_product_field)
        feedback.pushDebugInfo("fields =  " + str(output_fields.names()))
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            output_fields,
            boundary.wkbType(),
            #reporting.sourceCrs()
            crs
        )
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))
        # Algorithm
        # progress step
        nb_feats = source.featureCount()
        feedback.pushDebugInfo("nb_feats = " + str(nb_feats))
        if nb_feats == 0:
            utils.warn("Empty layer : " + qgsUtils.pathOfLayer(source))
            progress_step = 1
            #raise QgsProcessingException("Empty layer : " + qgsUtils.pathOfLayer(source))
        else:
            progress_step = 100.0 / nb_feats
        curr_step = 0
        # Reporting area
        for report_feat in boundary.getFeatures():
            report_geom = report_feat.geometry()
        report_area = report_geom.area() / unit_divisor
        sum_Ai = 0
        feedback.pushDebugInfo("report_area = " + str(report_area))
        if report_area == 0:
            raise QgsProcessingException("Empty reporting area")
        else:
            feedback.pushDebugInfo("ok")
        # Iteration over source features
        res_feat = QgsFeature(output_fields)
        res_feat = QgsFeature(output_fields)
        res_feat.setGeometry(report_geom)
        res_feat[self.ID] = report_feat.id()
        res_feat[self.NB_PATCHES] = 0
        res_feat[self.REPORT_AREA] = report_area
        res_feat[self.COHERENCE] = 0
        net_product = 0
        intersecting_area = 0
        for f in source.getFeatures():
            f_geom = f.geometry()
            f_area = f_geom.area() / unit_divisor
            sum_Ai += f_area
            intersection = f_geom.intersection(report_geom)
            intersection_area = intersection.area() / unit_divisor
            intersecting_area += intersection_area
            res_feat[self.NB_PATCHES] += 1
            if cut_mode:
                net_product += intersection_area * intersection_area
            else:
                net_product += f_area * intersection_area
            # Progress update
            curr_step += 1
            feedback.setProgress(int(curr_step * progress_step))
        if cut_mode:
            report_area_sq = report_area * report_area
        else:
            report_area_sq = report_area * sum_Ai
        res_feat[self.NET_PRODUCT] = net_product
        res_feat[self.INTERSECTING_AREA] = intersecting_area
        res_feat[self.COHERENCE] = net_product / report_area_sq if report_area_sq > 0 else 0
        res_feat[self.SPLITTING_DENSITY] = report_area / net_product if net_product > 0 else 0
        res_feat[self.MESH_SIZE] = net_product / report_area
        res_feat[self.SPLITTING_INDEX] = report_area_sq / net_product if net_product > 0 else 0
        res_feat[self.DIVI] = 1 - res_feat[self.COHERENCE]
        sink.addFeature(res_feat)
        return {self.OUTPUT: dest_id, self.OUTPUT_GLOBAL_MEFF : res_feat[self.MESH_SIZE]}

        

class EffectiveMeshSizeReportingAlgorithm(QgsProcessingAlgorithm):

    ALG_NAME = "effectiveMeshSizeReporting"

    # Algorithm parameters
    INPUT = "INPUT"
    SELECT_EXPR = "SELECT_EXPR"
    REPORTING = "REPORTING"
    CRS = "CRS"
    CUT_MODE = "CUT_MODE"
    UNIT = "UNIT"
    OUTPUT = "OUTPUT"
    
    OUTPUT_GLOBAL_MEFF = "GLOBAL_MEFF"
    
    # Output layer fields
    ID = "fid"
    NB_PATCHES = "nb_patches"
    REPORT_AREA = "report_area"
    INTERSECTING_AREA = "intersecting_area"
    # Main measures
    MESH_SIZE = "effective_mesh_size"
    DIVI = "landscape_division"
    SPLITTING_INDEX = "splitting_index"
    # Auxiliary measures
    COHERENCE = "coherence"
    SPLITTING_DENSITY = "splitting_density"
    NET_PRODUCT = "net_product"
    
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return EffectiveMeshSizeReportingAlgorithm()
        
    def name(self):
        return self.ALG_NAME
        
    def displayName(self):
        return self.tr("3 - Effective mesh size (Reporting)")
        
    def shortHelpString(self):
        return self.tr("Computes effective mesh size and other fragmentation indicators")

    def initAlgorithm(self, config=None):
        self.unit_options = [
            self.tr("m² (square meters)"),
            self.tr("dm² (square decimeters / ares)"),
            self.tr("hm² (square hectometers / hectares)"),
            self.tr("km² (square kilometers)")]
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr("Input layer"),
                [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(
            QgsProcessingParameterExpression(
                self.SELECT_EXPR,
                self.tr("Filter expression"),
                optional=True))
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.REPORTING,
                self.tr("Reporting layer"),
                [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(
            QgsProcessingParameterCrs(
                self.CRS,
                description=self.tr("Output CRS"),
                defaultValue=params.defaultCrs))
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.CUT_MODE,
                self.tr("Cross-boundary connection method")))
        self.addParameter(
            QgsProcessingParameterEnum(
                self.UNIT,
                description=self.tr("Report areas unit"),
                options=self.unit_options))
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("Output layer")))
                
    def processAlgorithm(self,parameters,context,feedback):
        feedback.pushDebugInfo("begin")
        # Parameters
        source = self.parameterAsVectorLayer(parameters,self.INPUT,context)
        feedback.pushDebugInfo("source = " + str(source))
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
        select_expr = self.parameterAsExpression(parameters,self.SELECT_EXPR,context)
        reporting = self.parameterAsVectorLayer(parameters,self.REPORTING,context)
        feedback.pushDebugInfo("reporting = " + str(reporting))
        if reporting is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.REPORTING))
        crs = self.parameterAsCrs(parameters,self.CRS,context)
        cut_mode = self.parameterAsBool(parameters,self.CUT_MODE,context)
        unit = self.parameterAsEnum(parameters,self.UNIT,context)
        output = parameters[self.OUTPUT]
        # CRS reprojection
        # source_crs = source.crs().authid()
        # reporting_crs = reporting.crs().authid()
        # feedback.pushDebugInfo("source_crs = " + str(source_crs))
        # feedback.pushDebugInfo("reporting_crs = " + str(reporting_crs))
        # feedback.pushDebugInfo("crs = " + str(crs.authid()))
        # if source_crs != crs.authid():
            # source_path = params.mkTmpLayerPath('source_reproject.gpkg')
            # qgsTreatments.applyReprojectLayer(source,crs,source_path,context,feedback)
            # source = qgsUtils.loadVectorLayer(source_path)
        # if reporting_crs != crs.authid():
            # reporting_path = params.mkTmpLayerPath('reporting_reproject.gpkg')
            # qgsTreatments.applyReprojectLayer(reporting,crs,reporting_path,context,feedback)
            # reporting = qgsUtils.loadVectorLayer(reporting_path)
        # Algorithm
        # progress step
        nb_feats = reporting.featureCount()
        feedback.pushDebugInfo("nb_feats = " + str(nb_feats))
        if nb_feats == 0:
            raise QgsProcessingException("Empty layer")
        progress_step = 100.0 / nb_feats
        curr_step = 0
        # gna gna
        multi_feedback = feedbacks.ProgressMultiStepFeedback(nb_feats, feedback)
        report_layers = []
        for count, report_feat in enumerate(reporting.getFeatures()):
            multi_feedback.setCurrentStep(count)
            report_id = report_feat.id()
            reporting.selectByIds([report_id])
            select_path = params.mkTmpLayerPath("reportingSelection" + str(report_feat.id()) + ".gpkg")
            qgsTreatments.saveSelectedFeatures(reporting,select_path,context,feedback)
            report_computed_path = params.mkTmpLayerPath("reportingComputed" + str(report_feat.id()) + ".gpkg")
            parameters = { EffectiveMeshSizeGlobalAlgorithm.INPUT : source,
                           EffectiveMeshSizeGlobalAlgorithm.SELECT_EXPR : select_expr,
                           EffectiveMeshSizeGlobalAlgorithm.BOUNDARY : select_path,
                           EffectiveMeshSizeGlobalAlgorithm.CRS : crs,
                           EffectiveMeshSizeGlobalAlgorithm.CUT_MODE : cut_mode,
                           EffectiveMeshSizeGlobalAlgorithm.UNIT : unit,
                           EffectiveMeshSizeGlobalAlgorithm.OUTPUT : report_computed_path }
            qgsTreatments.applyProcessingAlg(FragScapeAlgorithmsProvider.NAME,
                                             EffectiveMeshSizeGlobalAlgorithm.ALG_NAME,
                                             parameters,context,multi_feedback)
            report_layers.append(report_computed_path)
        qgsTreatments.mergeVectorLayers(report_layers,crs,output)
        return {self.OUTPUT: output}
