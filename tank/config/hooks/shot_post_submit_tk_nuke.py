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

import nuke
import sgtk
import sys

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
                                
                    start:      Int
                                Start frame from UI.
                                
                    end:        Int
                                End frame from UI.
                                
                    limit:      String
                                Limit from UI.
                    
                    work_file:  String
                                Path to work file.
                    
                    output:     Dict
                                Dictionary with all data from the outputs:
                                
                                name:         String
                                              Name of output in the environment.
                                
                                tank_type:    String
                                              Tank type specified in the environment.
        
        '''
        
        print 'Post Render Hook!'
        self.app=app
        self.outputs=outputs
        
        print 'app:'
        print self.app
        #print self.app.sgtk.templates["maya_shot_work"]
        
        print 'outputs:'
        for output in self.outputs:
                  
        
            filePath=nuke.root()['name'].value() 
         
            name = output["jobname"]   
            priority = output["priority"]
            start=output["start"] 
            end=output["end"] 
            inputFilepath=output["work_file"]
            pluginArgs=['']
            submitArgs=['Comment=Shotgun Publish submit']
            shotgunContext=self.parent.context
    
    
            #getting fields for version
            shot_temp=self.parent.sgtk.templates["nuke_shot_work"]
            shotgunFields=shot_temp.get_fields(filePath)
            
            #getting output path
            area_temp=self.parent.sgtk.templates['nuke_shot_render_area']
            outputPath=area_temp.apply_fields(shotgunFields).replace('\\','/')
            
            #getting output fields
            render_temp=self.parent.sgtk.templates['nuke_shot_render_exr']
            
            outputFiles=render_temp.apply_fields(shotgunFields)
            outputFields=render_temp.get_fields(outputFiles)
              
            #clunky code to replace seq format with ?
            cmd=''
            maxCount=int(outputFiles.split('%')[-1].split('.')[0].replace('d',''))
            for count in xrange(0,maxCount):
                
                cmd+='?'
            
            path=outputFiles.split('%')[0][0:-1]
            ext=outputFiles.split('%')[-1].split('.')[-1]
            
            outputFile='.'.join([path,cmd,ext]).replace('\\','/')
            
            outputFiles=[outputFile]
            
            #getting login for user and replacing with user in shotgunContext
            shotgunUser=sgtk.util.get_current_user(self.parent.sgtk)
              
            #creating the folders for rendering
            for outputfile in outputFiles:
                
                dirpath=os.path.dirname(outputfile)
                
                if not os.path.exists(dirpath):
                    os.makedirs(dirpath)
            
            #submit to deadline
            cdu.submit('nuke', name, start, end, inputFilepath, outputPath, outputFiles, pluginArgs, submitArgs,
                       shotgunContext=shotgunContext, shotgunFields=shotgunFields,shotgunUser=shotgunUser,
                       limit=output['limit'],priority=output['priority'])    