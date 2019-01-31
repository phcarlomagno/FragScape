# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Utils
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

import datetime
import os.path
import pathlib
import sys
import subprocess
import time
import html
import platform
import glob

from PyQt5.QtWidgets import QFileDialog

file_dir = os.path.dirname(__file__)
if file_dir not in sys.path:
    sys.path.append(file_dir)

# LOG UTILITIES

def printLine(msg):
    print(msg + "\n")
    
def doNothing(msg):
    pass

debug_flag=False
#print_func = printLine
print_func = doNothing
curr_language = "fr"
dialog_base_dir = None

platform_sys = platform.system()
    

class CustomException(Exception):

    def __init__(self, message):
        super().__init__(message)


def printDate(msg):
    print_func ("[" + str(datetime.datetime.now()) + "] " + msg)
    
def debug(msg):
    if debug_flag:
        printDate("<font color=\"gray\">[debug] " + msg + "</font>")
    
def info(msg):
    printDate("<font color=\"black\">[info] " + msg + "</font>")
    
def warn(msg):
    printDate("<font color=\"orange\">[warn] " + html.escape(msg) + "</font>")
    
def mkBoldRed(msg):
    return "<b><font color=\"red\">" + msg + "</font></b>"
    
def error_msg(msg,prefix=""):
    printDate(mkBoldRed("[" + prefix + "] " + msg))
    
def user_error(msg):
    error_msg(msg,"user error")
    raise CustomException(msg)
    
def internal_error(msg):
    error_msg(msg,"internal error")
    raise CustomException(msg)
    
def todo_error(msg):
    error_msg(msg,"Feature not yet implemented")
    raise CustomException(msg)

class Section:

    def __init__(self,title,prefix=">>>>"):
        self.title = title
        self.prefix = prefix
            
    def start_section(self):
        self.start_time = time.time()
        info(self.prefix + " Start " + self.title)
    
    def end_section(self):
        info(self.prefix + " End " + self.title)
        self.end_time = time.time()
        diff_time = self.end_time - self.start_time
        info(self.title + " finished in " + str(diff_time) + " seconds")
    
    
# FILE UTILITIES

def normPath(fname):
    p = pathlib.Path(fname)
    pp = p.as_posix()
    return pp
    #return fname.replace('\\','/')
    
def joinPath(p1,p2):
    pp1 = pathlib.Path(p1)
    res = pp1.joinpath(p2)
    return res.as_posix()
    
def createSubdir(par_dir,name):
    path = joinPath(par_dir,name)
    if not os.path.isdir(path):
        info("Creating directory '" + path + "'")
        os.makedirs(path)
    return path
    
def pathEquals(p1,p2):
    if p1 and p2:
        p1_parts = pathlib.Path(p1).parts
        p2_parts = pathlib.Path(p2).parts
        return (p1 == p2)
    else:
        return False
     
def fileExists(fname,prefix=""):
    if not fname:
        return False
    print("fe 1")
    path = pathlib.Path(fname)
    print("fe 2")
    if not path.exists():
        return False
    if not (os.path.isfile(fname)):
        return False
    return True

def checkFileExists(fname,prefix=""):
    path = pathlib.Path(fname)
    debug("path = " + str(path))
    debug("pathparts = " + str(path.parts))
    if not path.exists():
        user_error("path does not exist : " + str(path))
    if not fname:
        user_error(prefix + " File not selected")
    if not (os.path.isfile(fname)):
        user_error(prefix + "File '" + fname + "' does not exist")
        
def removeFile(path):
    if os.path.isfile(path):
        debug("Deleting existing file '" + path + "'")
        os.remove(path)
    
def writeFile(fname,str):
    with open(fname,"w",encoding="utf-8") as f:
        f.write(str)
        
# Opens file dialog in open mode
def openFileDialog(parent,msg="",filter=""):
    fname, filter = QFileDialog.getOpenFileName(parent,
                                                caption=msg,
                                                directory=dialog_base_dir,
                                                filter=filter)
    return fname
    
# Opens file dialog in save mode
def saveFileDialog(parent,msg="",filter=""):
    fname, filter = QFileDialog.getSaveFileName(parent,
                                                caption=msg,
                                                directory=dialog_base_dir,
                                                filter=filter)
    return fname
    
# PATH UTILITIES

def mkTmpPath(path,suffix="_tmp"):
    bn,extension = os.path.splitext(path)
    return (bn + suffix + extension)
    
def fromTmpPath(tmp_path):
    bn, extension = os.path.splitext(path)
    return (bn[:-4] + extension)
    
def findFileFromDir(dir,fname):
    #if dir.endsWith('/'):
    if False:
        regexp = dir + "**/" + fname
    else:
        regexp = dir + "/**/" + fname
    glob_res = glob.glob(regexp,recursive=True)
    nb_res = len(glob_res)
    if nb_res == 0:
        user_error("No file '" + fname + "' found in directory '" + dir + "'")
    else:
        res = glob_res[0]
        debug("Found " + str(nb_res) + " files named '" + fname + "' in directory '" + dir + "'")
        return res
    

# TYPE UTILITIES
    
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
    
def is_integer(s):
    try:
        int(s)
        return True
    except ValueError:
        return False
        
        
# Validity checkers
        
def checkFields(ref_fields,fields):
    if ref_fields != fields:
        for rf in ref_fields:
            if rf not in fields:
                user_error("Missing field '" + rf + "' in " + str(fields))
             
def checkDictField(item,fieldname,prefix=None):
    if prefix == None:
        prefix = item.__class__.name
    if not item.dict[fieldname]:
        user_error(prefix + " with empty name '" + str(item.dict[fieldname]) + "'")
        
def checkName(item,prefix=None):
    checkDictField(item,"name",prefix)
    
def checkDescr(item,prefix=None):
    if prefix == None:
        prefix = item.__class__.name
    if not item.dict["descr"]:
        if "name" in item.dict:
            name = " " + str(item.dict["name"])
        else:
            name = " "
        warn(prefix + name + " with empty description")
        

# Subprocess utils
        
def executeCmd(cmd_args):
    debug("command = " + str(cmd_args))
    p = subprocess.Popen(cmd_args,
                         stderr=subprocess.PIPE,
                         stdout=subprocess.PIPE)
    out,err = p.communicate()
    debug(str(p.args))
    if out:
        info(str(out))
    if err:
        if "invalid value encountered in less" in str(err):
            warn(str(err))
        else:
            user_error(str(err))
        
def executeCmdAsScript(cmd_args):
    debug("executeCmdAsScript")
    new_args = [sys.executable] + cmd_args
    debug(str(new_args))
    ret = subprocess.call(new_args)
    debug("return code = " + str(ret))
    
        
