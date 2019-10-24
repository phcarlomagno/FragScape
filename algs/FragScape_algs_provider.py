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


from qgis.core import QgsApplication, QgsProcessingProvider

from .FragScape_algs import (PrepareLanduseAlgorithm,
                             PrepareFragmentationAlgorithm,
                             ApplyFragmentationAlgorithm,
                             EffectiveMeshSizeReportingAlgorithm,
                             EffectiveMeshSizeGlobalAlgorithm)
from .FragScape_raster_algs import MeffRaster, MeffRasterCBC

class FragScapeAlgorithmsProvider(QgsProcessingProvider):

    def __init__(self):
        self.alglist = [PrepareLanduseAlgorithm(),
                        PrepareFragmentationAlgorithm(),
                        ApplyFragmentationAlgorithm(),
                        EffectiveMeshSizeReportingAlgorithm(),
                        EffectiveMeshSizeGlobalAlgorithm(),
                        MeffRaster(),
                        MeffRasterCBC()]
        for a in self.alglist:
            a.initAlgorithm()
        super().__init__()
        
    def unload(self):
        pass
        
    def id(self):
        return "FragScape"
        
    def name(self):
        return "FragScape"
        
    def longName(self):
        return self.name()
        
    def loadAlgorithms(self):
        for a in self.alglist:
            self.addAlgorithm(a)