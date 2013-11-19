# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import sys

import maya.cmds as cmds

import sgtk
import tank
from tank import Hook
from tank import TankError

sys.path.append('K:/')
import CodeRepo.Deadline.utils as cdu
reload(cdu)

class PostSubmitHook(Hook):
    
    def execute(self,app,outputs, **kwargs):
        '''
        
        app:        main class app
        outputs:    list of dicts with the following keys:
                
                    jobname:    String
                                Jobname from UI.
                                
                    priority:   Int
                                Priority value from UI.
                                
                    output['start']:      Int
                                output['start'] frame from UI.
                                
                    output['end']:        Int
                                output['end'] frame from UI.
                                
                    limit:      String
                                Limit from UI.
                    
                    work_file:  String
                                Path to work file.
                    
                    output:     Dict
                                Dictionary with all data from the outputs:
                                
                                name:         String
                                              output['name'] of output in the environment.
                                
                                tank_type:    String
                                              Tank type specified in the environment.
        
        '''
        
        self.app=app
        self.outputs=outputs
        
        for output in self.outputs:
            
            if output['output']['name'] == "arnold_render":
                
                try:
                    self._arnold_render(output)
                except:
                    print 'Arnold submittal failed!'
            
            if output['output']['name'] == "maya_render":
                try:
                    self._maya_render(output)
                except:
                    print 'Maya submittal failed!'
            
            if output['output']['name'] == "ass_render":
                try:
                    self._export_ass()
                    
                    self._ass_render(output)
                except:
                    print 'ASS submittal failed!'
    
    def _export_ass(self):
        
        import mtoa.cmds.arnoldRender as ar
        
        filePath=cmds.file(q=True,sn=True)
        
        #getting fields for version
        shot_temp=self.parent.sgtk.templates["maya_shot_work"]
        shotgunFields=shot_temp.get_fields(filePath)
        
        #getting output path
        area_temp=self.parent.sgtk.templates['maya_ass_export_area']
        path=area_temp.apply_fields(shotgunFields).replace('\\','/')
        
        #setting ass export path
        cmds.workspace(fileRule = ['ASS', path])
        
        #account for renderlayers
        for layer in cmds.ls(type='renderLayer'):
            
            #discarding referenced layers
            if ':' not in layer:
                
                #checking whether layer needs to be rendered
                if cmds.getAttr(layer+'.renderable')==1:
                    
                    cmds.editRenderLayerGlobals( currentRenderLayer=layer )
                    
                    try:
                        ar.arnoldBatchRender('')
                    except Exception, e:
                        raise TankError("Failed to export Ass files: %s" % e)
    
    def _ass_render(self,output):
        
        print 'Rendering ASS'
        
        pluginArgs=['']
        submitArgs=['Comment=Shotgun Publish submit']
        shotgunContext=self.parent.context
        
        #getting fields for version
        shot_temp=self.parent.sgtk.templates["maya_shot_work"]
        shotgunFields=shot_temp.get_fields(output['work_file'])
        
        #getting output path
        area_temp=self.parent.sgtk.templates['maya_shot_render_area']
        outputPath=area_temp.apply_fields(shotgunFields).replace('\\','/')
        
        #getting ass file path
        area_temp=self.parent.sgtk.templates['maya_ass_export']
        inputFilepath=area_temp.apply_fields(shotgunFields).replace('\\','/') % 1
        
        inputFiles=[]
        for layer in cmds.ls(type='renderLayer'):
            
            #discarding referenced layers
            if ':' not in layer:
            
                #checking whether layer needs to be rendered
                if cmds.getAttr(layer+'.renderable')==1:
                
                    if layer=='defaultRenderLayer':
                        
                        layer='masterLayer'
                    
                    #hardcoded replace of name string---
                    p=inputFilepath.replace('/data/','/data/%s/' % layer)
                    
                    inputFiles.append(p)
        
        #getting output fields
        render_temp=self.parent.sgtk.templates['maya_shot_render']
        outputFiles=render_temp.apply_fields(shotgunFields)
        outputFields=render_temp.get_fields(outputFiles)
        
        #replacing name with file name
        outputFields['name']='.'.join(output['work_file'].split('/')[-1].split('.')[0:-2])
        
        #generate outputFiles
        shotgunFiles=render_temp.apply_fields(outputFields)
        
        outputFiles=[]
        publishFiles=[]
        for layer in cmds.ls(type='renderLayer'):
            
            #discarding referenced layers
            if ':' not in layer:
            
                #checking whether layer needs to be rendered
                if cmds.getAttr(layer+'.renderable')==1:
                
                    if layer=='defaultRenderLayer':
                        
                        layer='masterLayer'
                    
                    #clunky code to replace seq format with ?
                    cmd=''
                    maxCount=int(shotgunFiles.split('%')[-1].split('.')[0].replace('d',''))
                    for count in xrange(0,maxCount):
                        
                        cmd+='?'
                    
                    path=shotgunFiles.split('%')[0][0:-1]
                    ext=shotgunFiles.split('%')[-1].split('.')[-1]
                    
                    outputFile='.'.join([path,cmd,ext]).replace('\\','/')
                    
                    #adding renderlayer to outputfiles
                    filename=os.path.basename(outputFile)
                    dirpath=os.path.dirname(outputFile)
                    
                    outputFiles.append(os.path.join(dirpath,layer+'_'+filename))
                    
                    #adding renderlayer to shotgunfiles
                    filename=os.path.basename(shotgunFiles)
                    dirpath=os.path.dirname(shotgunFiles)
                    
                    publishFiles.append(os.path.join(dirpath,layer+'_'+filename))
        
        #getting login for user and replacing with user in shotgunContext
        shotgunUser=sgtk.util.get_current_user(self.parent.sgtk)
        
        #creating the folders for rendering
        for outputfile in outputFiles:
            
            dirpath=os.path.dirname(outputfile)
            
            if not os.path.exists(dirpath):
                os.makedirs(dirpath)
        
        for f in inputFiles:
            
            count=inputFiles.index(f)
            
            #generate jobname
            layer=f.split('/')[-2]
            
            jobname=output['jobname']+'.'+layer
            
            #execute deadline submittal
            cdu.submit('arnold', jobname, output['start'], output['end'], f, outputPath,[outputFiles[count]], pluginArgs,
                       submitArgs,shotgunContext=shotgunContext, shotgunFields=shotgunFields,shotgunUser=shotgunUser,
                       mayaGUI=True,priority=output['priority'])
                
    def _maya_render(self,output):
        
        print 'Rendering Maya'
        
        pluginArgs=['']
        submitArgs=['Comment=Shotgun Publish submit']
        shotgunContext=self.app.context
        
        #getting fields for version
        shot_temp=self.parent.sgtk.templates["maya_shot_work"]
        shotgunFields=shot_temp.get_fields(output['work_file'])
        
        #getting output path
        area_temp=self.parent.sgtk.templates['maya_shot_render_area']
        outputPath=area_temp.apply_fields(shotgunFields).replace('\\','/')
        
        #getting ass file path
        area_temp=self.parent.sgtk.templates['maya_ass_export']
        inputFilepath=area_temp.apply_fields(shotgunFields).replace('\\','/') % 1
        
        inputFiles=[]
        for layer in cmds.ls(type='renderLayer'):
            
            #discarding referenced layers
            if ':' not in layer:
            
                #checking whether layer needs to be rendered
                if cmds.getAttr(layer+'.renderable')==1:
                
                    if layer=='defaultRenderLayer':
                        
                        layer='masterLayer'
                    
                    #hardcoded replace of name string---
                    p=inputFilepath.replace('/data/','/data/%s/' % layer)
                    
                    inputFiles.append(p)
        
        #getting output fields
        render_temp=self.parent.sgtk.templates['maya_shot_render']
        outputFiles=render_temp.apply_fields(shotgunFields)
        outputFields=render_temp.get_fields(outputFiles)
        
        #replacing name with file name
        outputFields['name']='.'.join(output['work_file'].split('/')[-1].split('.')[0:-2])
        
        #generate outputFiles
        shotgunFiles=render_temp.apply_fields(outputFields)
        
        outputFiles=[]
        publishFiles=[]
        for layer in cmds.ls(type='renderLayer'):
            
            #discarding referenced layers
            if ':' not in layer:
            
                #checking whether layer needs to be rendered
                if cmds.getAttr(layer+'.renderable')==1:
                
                    if layer=='defaultRenderLayer':
                        
                        layer='masterLayer'
                    
                    #clunky code to replace seq format with ?
                    cmd=''
                    maxCount=int(shotgunFiles.split('%')[-1].split('.')[0].replace('d',''))
                    for count in xrange(0,maxCount):
                        
                        cmd+='?'
                    
                    path=shotgunFiles.split('%')[0][0:-1]
                    ext=shotgunFiles.split('%')[-1].split('.')[-1]
                    
                    outputFile='.'.join([path,cmd,ext]).replace('\\','/')
                    
                    #adding renderlayer to outputfiles
                    filename=os.path.basename(outputFile)
                    dirpath=os.path.dirname(outputFile)
                    
                    outputFiles.append(os.path.join(dirpath,layer+'_'+filename))
                    
                    #adding renderlayer to shotgunfiles
                    filename=os.path.basename(shotgunFiles)
                    dirpath=os.path.dirname(shotgunFiles)
                    
                    publishFiles.append(os.path.join(dirpath,layer+'_'+filename))
        
        #getting login for user and replacing with user in shotgunContext
        shotgunUser=sgtk.util.get_current_user(self.app.sgtk)
        
        #creating the folders for rendering
        for outputfile in outputFiles:
            
            dirpath=os.path.dirname(outputfile)
            
            if not os.path.exists(dirpath):
                os.makedirs(dirpath)
        
        for f in inputFiles:
            
            count=inputFiles.index(f)
            
            #generate jobname
            layer=f.split('/')[-2]
            
            jobname=output['jobname']+'.'+layer
            
            #execute deadline submittal
            cdu.submit('maya', jobname, output['start'], output['end'], f, outputPath,[outputFiles[count]], pluginArgs,submitArgs,
                       shotgunContext=shotgunContext, shotgunFields=shotgunFields,shotgunUser=shotgunUser,mayaGUI=True,
                       limit=output['limit'],priority=output['priority'])
        
    def _arnold_render(self,output):
        
        print 'Rendering Arnold!'
        
        pluginArgs=['']
        submitArgs=['Comment=Shotgun Publish submit']
        shotgunContext=self.app.context
        
        #getting fields for version
        shot_temp=self.app.sgtk.templates["maya_shot_work"]
        shotgunFields=shot_temp.get_fields(output['work_file'])
        
        #getting output path
        area_temp=self.parent.sgtk.templates['maya_shot_render_area']
        outputPath=area_temp.apply_fields(shotgunFields).replace('\\','/')
        
        #getting ass file path
        area_temp=self.parent.sgtk.templates['maya_ass_export']
        inputFilePath=area_temp.apply_fields(shotgunFields).replace('\\','/') % 1
        
        inputFiles=[]
        for layer in cmds.ls(type='renderLayer'):
            
            #discarding referenced layers
            if ':' not in layer:
            
                #checking whether layer needs to be rendered
                if cmds.getAttr(layer+'.renderable')==1:
                
                    if layer=='defaultRenderLayer':
                        
                        layer='masterLayer'
                    
                    #hardcoded replace of output['name'] string---
                    p=inputFilePath.replace('/data/','/data/%s/' % layer)
                    
                    inputFiles.append(p)
        
        #getting output fields
        render_temp=self.parent.sgtk.templates['maya_shot_render']
        outputFiles=render_temp.apply_fields(shotgunFields)
        outputFields=render_temp.get_fields(outputFiles)
        
        #replacing output['name'] with file output['name']
        outputFields['name']='.'.join(output['work_file'].split('/')[-1].split('.')[0:-2])
        
        #generate outputFiles
        shotgunFiles=render_temp.apply_fields(outputFields)
        
        outputFiles=[]
        for layer in cmds.ls(type='renderLayer'):
            
            #discarding referenced layers
            if ':' not in layer:
            
                #checking whether layer needs to be rendered
                if cmds.getAttr(layer+'.renderable')==1:
                
                    if layer=='defaultRenderLayer':
                        
                        layer='masterLayer'
                    
                    #clunky code to replace seq format with ?
                    cmd=''
                    maxCount=int(shotgunFiles.split('%')[-1].split('.')[0].replace('d',''))
                    for count in xrange(0,maxCount):
                        
                        cmd+='?'
                    
                    path=shotgunFiles.split('%')[0][0:-1]
                    ext=shotgunFiles.split('%')[-1].split('.')[-1]
                    
                    outputFile='.'.join([path,cmd,ext]).replace('\\','/')
                    
                    #adding renderlayer to outputfiles
                    filename=os.path.basename(outputFile)
                    dirpath=os.path.dirname(outputFile)
                    
                    outputFiles.append(os.path.join(dirpath,layer+'_'+filename))
                    
                    #adding renderlayer to shotgunfiles
                    filename=os.path.basename(shotgunFiles)
                    dirpath=os.path.dirname(shotgunFiles)
        
        #getting login for user and replacing with user in shotgunContext
        shotgunUser=sgtk.util.get_current_user(self.app.sgtk)
        
        #creating the folders for rendering
        for outputfile in outputFiles:
            
            dirpath=os.path.dirname(outputfile)
            
            if not os.path.exists(dirpath):
                os.makedirs(dirpath)
        
        #submit to deadline
        exportId=cdu.submit('arnoldExport', output['jobname'], output['start'], output['end'], output['work_file'], outputPath,[outputFiles[0]],
                            ['ProjectPath=%s' % outputPath], submitArgs,shotgunContext='', shotgunFields='',shotgunUser='',mayaGUI=True,
                            limit=output['limit'],priority=output['priority'])
        
        for f in inputFiles:
            
            count=inputFiles.index(f)
            
            #generate jobname
            layer=f.split('/')[-2]
                    
            jobname=output['jobname']+'.'+layer
            
            #execute deadline submittal
            cdu.submit('arnold', jobname, output['start'], output['end'], f, outputPath,[outputFiles[count]], pluginArgs,
                       submitArgs=['JobDependencies=%s' % exportId],shotgunContext=shotgunContext, shotgunFields=shotgunFields,
                       shotgunUser=shotgunUser,mayaGUI=True,priority=output['priority'])