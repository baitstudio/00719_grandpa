"""
Copyright (c) 2013 Shotgun Software, Inc
----------------------------------------------------

"""
import os
import maya.cmds as cmds

import tank
from tank import Hook
from tank import TankError

class PrePublishHook(Hook):
    """
    Single hook that implements pre-publish functionality
    """
    def execute(self, tasks, work_template, progress_cb, **kwargs):
        """
        Main hook entry point
        :tasks:         List of tasks to be pre-published.  Each task is be a 
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
               
        :progress_cb:   Function
                        A progress callback to log progress during pre-publish.  Call:
                        
                            progress_cb(percentage, msg)
                             
                        to report progress to the UI
                        
        :returns:       A list of any tasks that were found which have problems that
                        need to be reported in the UI.  Each item in the list should
                        be a dictionary containing the following keys:
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
        
        # validate tasks:
        for task in tasks:
            item = task["item"]
            output = task["output"]
            errors = []
        
            # report progress:
            progress_cb(0, "Validating", task)
            
            for ref in cmds.ls(type='reference'):
                try:
                    cmds.referenceQuery(ref,filename=True)
                except:         
                    cmds.lockNode(ref,l=False)
                    cmds.delete(ref)
            
            # pre-publish alembic_cache output
            if output["name"] == "alembic_cache":
                errors.extend(self._validate_item_for_alembic_cache_publish(item))
            elif output['name'] == "playblast":
                print ("playblast camera" + str(item))
            else:
                # don't know how to publish this output types!
                errors.append("Don't know how to publish this item!")       

            # if there is anything to report then add to result
            if len(errors) > 0:
                # add result:
                results.append({"task":task, "errors":errors})
              
            progress_cb(100)
            
        return results
    
    def _validate_item_for_alembic_cache_publish(self, item):
        """
        Validate that the item is valid to be exported 
        to an alembic cache
        """
        errors = []
        # check that the group still exists:
        '''
        if not cmds.objExists(item["other_params"]):
            errors.append("This group couldn't be found in the scene!")
    
        # and that it still contains meshes:
        elif not cmds.ls(item["name"], dag=True, type="mesh"):
            errors.append("This group doesn't appear to contain any meshes!")
        '''
        # finally return any errors
        return errors
        
    