"""
Copyright (c) 2013 Shotgun Software, Inc
----------------------------------------------------

"""
import os
import shutil
import sys

import maya.cmds as cmds
import maya.mel as mel
import pymel.core as pm

import sgtk
import tank
from tank import Hook
from tank import TankError

sys.path.append('K:/')
import CodeRepo.Deadline.utils as cdu
reload(cdu)

class PublishHook(Hook):
    """
    Single hook that implements publish functionality for secondary tasks
    """    
    def execute(self, tasks, work_template, comment, thumbnail_path, sg_task, primary_publish_path, progress_cb, **kwargs):
        """
        Main hook entry point
        :tasks:         List of secondary tasks to be published.  Each task is a 
                        dictionary containing the following keys:
                        {
                            item:   Dictionary
                                    This is the item returned by the scan hook 
                                    {   
                                        name:           String
                                        description:    String
                                        type:           String
                                        other_params:   Dictionary
                                    }
                                   
                            output: Dictionary
                                    This is the output as defined in the configuration - the 
                                    primary output will always be named 'primary' 
                                    {
                                        name:             String
                                        publish_template: template
                                        tank_type:        String
                                    }
                        }
                        
        :work_template: template
                        This is the template defined in the config that
                        represents the current work file
               
        :comment:       String
                        The comment provided for the publish
                        
        :thumbnail:     Path string
                        The default thumbnail provided for the publish
                        
        :sg_task:       Dictionary (shotgun entity description)
                        The shotgun task to use for the publish    
                        
        :primary_publish_path: Path string
                        This is the path of the primary published file as returned
                        by the primary publish hook
                        
        :progress_cb:   Function
                        A progress callback to log progress during pre-publish.  Call:
                        
                            progress_cb(percentage, msg)
                             
                        to report progress to the UI
        
        :returns:       A list of any tasks that had problems that need to be reported 
                        in the UI.  Each item in the list should be a dictionary containing 
                        the following keys:
                        {
                            task:   Dictionary
                                    This is the task that was passed into the hook and
                                    should not be modified
                                    {
                                        item:...
                                        output:...
                                    }
                                    
                            errors: List
                                    A list of error messages (strings) to report    
                        }
        """
        results = []
        
        # publish all tasks:
        for task in tasks:
            item = task["item"]
            output = task["output"]
            
            errors = []
        
            # report progress:
            progress_cb(0, "Publishing", task)
        
            # publish alembic_cache output
            if output["name"] == "alembic_cache":
                try:
                   self._publish_alembic_cache_for_item(item, output, work_template, primary_publish_path, 
                                                        sg_task, comment, thumbnail_path, progress_cb)
                except Exception, e:
                   errors.append("Publish failed - %s" % e)
                   
            elif output["name"] == "review":
                try:
                   self._publish_playblast_for_item(item, output, work_template, primary_publish_path, 
                                                        sg_task, comment, thumbnail_path, progress_cb)
                except Exception, e:
                   errors.append("Publish failed - %s" % e)
                   
            elif output["name"] == "deadline":
                try:
                   self._publish_render(item, output, work_template, primary_publish_path, 
                                        sg_task, comment, thumbnail_path, progress_cb)
                except Exception, e:
                   errors.append("Publish failed - %s" % e)
            else:
                # don't know how to publish this output types!
                errors.append("Don't know how to publish this item!") 

            # if there is anything to report then add to result
            if len(errors) > 0:
                # add result:
                results.append({"task":task, "errors":errors})
             
            progress_cb(100)
             
        return results

    def _publish_render(self, item, output, work_template, primary_publish_path, sg_task, comment, thumbnail_path, progress_cb):
        
        filePath=cmds.file(q=True,sn=True)
    
        name=os.path.basename(filePath)
        start=int(cmds.getAttr('defaultRenderGlobals.startFrame'))
        end=int(cmds.getAttr('defaultRenderGlobals.endFrame'))
        inputFilepath=filePath
        pluginArgs=['']
        submitArgs=['Comment=Shotgun Publish submit']
        shotgunContext=self.parent.context
        
        #getting fields for version
        shot_temp=self.parent.sgtk.templates["maya_shot_work"]
        shotgunFields=shot_temp.get_fields(filePath)
        
        #getting output path
        area_temp=self.parent.sgtk.templates['maya_shot_render_area']
        outputPath=area_temp.apply_fields(shotgunFields).replace('\\','/')
        
        #getting output fields
        render_temp=self.parent.sgtk.templates['maya_shot_render']
        outputFiles=render_temp.apply_fields(shotgunFields)
        outputFields=render_temp.get_fields(outputFiles)
        
        #replacing name with file name
        outputFields['name']='.'.join(filePath.split('/')[-1].split('.')[0:-2])
        
        #generate outputFiles
        shotgunFiles=render_temp.apply_fields(outputFields)
        
        outputFiles=[]
        publishFiles=[]
        for layer in cmds.ls(type='renderLayer'):
            
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
        
        #submit to deadline
        cdu.submit('maya', name, start, end, inputFilepath, outputPath, outputFiles, pluginArgs, submitArgs,
                   shotgunContext=shotgunContext, shotgunFields=shotgunFields,shotgunUser=shotgunUser,mayaGUI=True)
        
        # Finally, register this publish with Shotgun
        tank_type='CG Render'
        name=item["name"]
        
        for outputfile in publishFiles:
            self._register_publish(outputfile,
                                   name,
                                   sg_task,
                                   shotgunFields['version'],
                                   tank_type,
                                   comment,
                                   thumbnail_path,
                                   [primary_publish_path])

    def _publish_alembic_cache_for_item(self, item, output, work_template, primary_publish_path, sg_task, comment, thumbnail_path, progress_cb):
        """
        Export an Alembic cache for the specified item and publish it
        to Shotgun.
        """
        group_name = item["name"].strip("|")
        tank_type = output["tank_type"]
        publish_template = output["publish_template"]        

        # get the current scene path and extract fields from it
        # using the work template:
        scene_path = os.path.abspath(cmds.file(query=True, sn=True))
        fields = work_template.get_fields(scene_path)
        publish_version = fields["version"]

        # update fields with the group name:
        fields["Asset"] = group_name
        
        name = os.path.basename(cmds.file(query=True, sn=True))
        fields["name"] = name.split('.')[0] 
        
        # create the publish path by applying the fields 
        # with the publish template:
        publish_path = publish_template.apply_fields(fields)
        print publish_path
       
        # node loop 
        nodesString=''   
        item["other_params"] 
        for node in item["other_params"]:
            nodesString+='-root '+node+' '
             
        #export with assets attribute
        attrstring='-a asset'
        
        # build and execute the Alembic export command for this item:
        frame_start = int(cmds.playbackOptions(q=True, min=True))
        frame_end = int(cmds.playbackOptions(q=True, max=True))
        #abc_export_cmd = "AbcExport -j \"-frameRange %s %s %s -stripNamespaces -uvWrite -worldSpace -wholeFrameGeo -writeVisibility %s-file %s\"" % (frame_start,frame_end,attrstring,nodesString,publish_path)
       
        try:
            #self.parent.log_debug("Executing command: %s" % abc_export_cmd)
            #mel.eval(abc_export_cmd)
            print 'exporting ABC'
            pm.AbcExport(j='-frameRange %s %s %s -stripNamespaces -uvWrite -worldSpace -wholeFrameGeo -writeVisibility %s-file %s' % (frame_start,frame_end,attrstring,nodesString,publish_path))
        except Exception, e:
            raise TankError("Failed to export Alembic Cache: %s" % e)

        # Finally, register this publish with Shotgun
        self._register_publish(publish_path, 
                               group_name, 
                               sg_task, 
                               publish_version, 
                               tank_type,
                               comment,
                               thumbnail_path, 
                               [primary_publish_path])


    def _publish_playblast_for_item(self, item, output, work_template, primary_publish_path, sg_task, comment, thumbnail_path, progress_cb):
        """
        Export playblast video for the specified item and publish it
        to Shotgun.
        """
        camera_name = item["name"].strip("|")
        tank_type = output["tank_type"]
        publish_template = output["publish_template"]        

        # get the current scene path and extract fields from it
        # using the work template:
        scene_path = os.path.abspath(cmds.file(query=True, sn=True))
        fields = work_template.get_fields(scene_path)
        publish_version = fields["version"]
     
        name = os.path.basename(cmds.file(query=True, sn=True))
        fields["name"] = name.split('.')[0] 
        
        # create the publish path by applying the fields 
        # with the publish template:
        playblast_path = publish_template.apply_fields(fields)
        
        
        # build and execute the Alembic export command for this item:
        height = 360
        width = 640
        #abc_export_cmd = "AbcExport -j \"-frameRange 1 100 -stripNamespaces -uvWrite -worldSpace -wholeFrameGeo -writeVisibility %s -file %s\"" % (nodesString,publish_path)    
        try:
            mov = cmds.playblast(f=playblast_path,format='qt',forceOverwrite=True,offScreen=True,percent=100,compression='H.264',quality=100,width=width,height=height,viewer=False)
        except Exception, e:
            raise TankError("Failed to export Playblast: %s" % e)
        
        # Finally, register this publish with Shotgun
        self._register_version(fields, 
                               playblast_path,
                               mov)
        
        
    def _register_publish(self, path, name, sg_task, publish_version, tank_type, comment, thumbnail_path, dependency_paths=None):
        """
        Helper method to register publish using the 
        specified publish info.
        """
        # construct args:
        args = {
            "tk": self.parent.tank,
            "context": self.parent.context,
            "comment": comment,
            "path": path,
            "name": name,
            "version_number": publish_version,
            "thumbnail_path": thumbnail_path,
            "task": sg_task,
            "dependency_paths": dependency_paths,
            "published_file_type":tank_type,
        }

        # register publish;
        sg_data = tank.util.register_publish(**args)

        return sg_data

    def _register_version(self,fields,playblast_path,mov):
        """
        Helper method to register publish using the 
        specified publish info.
        """

        sg_version_name='v'+str(fields['version']).zfill(3)
        
        startTime=cmds.playbackOptions(q=True,minTime=True)
        endTime=cmds.playbackOptions(q=True,maxTime=True)
        
        args = {
            "code": sg_version_name,
            "project": self.parent.context.project,
            "entity": self.parent.context.entity,
            "sg_task": self.parent.context.task,
            "created_by": self.parent.context.user,
            "user": self.parent.context.user,
            "sg_path_to_movie": playblast_path,
            "sg_first_frame": int(startTime),
            "sg_last_frame": int(endTime),
            "frame_count": int((endTime - startTime) + 1),
            "frame_range": "%d-%d" % (startTime,endTime),
        }

        # register publish;
        sg_data = self.parent.shotgun.create("Version", args)
        
        #self.parent.shotgun.upload_thumbnail("Version", sg_data["id"], thumbnail)
        
        self.parent.shotgun.upload("Version",sg_data['id'],mov,field_name='sg_uploaded_movie')

        return sg_data