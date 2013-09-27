# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Hook that loads items into the current scene. 

This hook supports a number of different platforms and the behaviour on each platform is
different. See code comments for details.


"""
import tank
import os

class AddFileToScene(tank.Hook):
    
    def execute(self, engine_name, file_path, shotgun_data, **kwargs):
        """
        Hook entry point and app-specific code dispatcher
        """
                
        if engine_name == "tk-maya":
            self.add_file_to_maya(file_path, shotgun_data)
            
        elif engine_name == "tk-nuke":
            self.add_file_to_nuke(file_path, shotgun_data)
            
        elif engine_name == "tk-motionbuilder":
            self.add_file_to_motionbuilder(file_path, shotgun_data)
            
        elif engine_name == "tk-3dsmax":
            self.add_file_to_3dsmax(file_path, shotgun_data)
            
        elif engine_name == "tk-photoshop":
            self.add_file_to_photoshop(file_path, shotgun_data)

        else:
            raise Exception("Don't know how to load file into unknown engine %s" % engine_name)
        
    ###############################################################################################
    # app specific implementations
    
    def add_file_to_maya(self, file_path, shotgun_data):
        """
        Load file into Maya.
        
        This implementation creates a standard maya reference file for any item.
        """
        
        import pymel.core as pm
        import maya.cmds as cmds
        
        # get the slashes right
        file_path = file_path.replace(os.path.sep, "/")
        
        fileName=os.path.basename(file_path)

        (name, ext) = os.path.splitext(fileName)
        
        texture_extensions = [".png", ".jpg", ".jpeg", ".exr", ".cin", ".dpx",
                              ".psd", ".tiff", ".tga"]
        
        name=fileName.split('.')[0]
        
        if ext in [".abc"]:
            name = (name + 'Abc')
        
        result = pm.promptDialog(
            title='Namespace',
            message='Choose Namespace',
            text=name,
            button=['OK', 'Cancel'],
            cancelButton='Cancel',
            defaultButton='OK')

        name = pm.promptDialog(query=True, text=True)
        
        if result == 'OK':
        
            if ext in [".ma", ".mb", ".abc"]:
                # maya file - load it as a reference
                pm.system.createReference(file_path, namespace=name)
     
                
            elif ext in texture_extensions:
                # create a file texture read node
                x = cmds.shadingNode('file', asTexture=True)
                cmds.setAttr( "%s.fileTextureName" % x, file_path, type="string" )
    
            else:
                self.parent.log_error("Unsupported file extension for %s! Nothing will be loaded." % file_path)
        
    def add_file_to_nuke(self, file_path, shotgun_data):
        """
        Load item into Nuke.
        
        This implementation will create a read node and associate the given path with 
        the read node's file input.
        """
        
        import nuke
        
        # get the slashes right
        file_path = file_path.replace(os.path.sep, "/")

        (path, ext) = os.path.splitext(file_path)

        valid_extensions = [".png", ".jpg", ".jpeg", ".exr", ".cin", ".dpx", ".tiff", ".mov"]

        if ext in valid_extensions:
            # find the sequence range if it has one:
            seq_range = self._find_sequence_range(file_path)
            
            # create the read node
            if seq_range:
                nuke.nodes.Read(file=file_path, first=seq_range[0], last=seq_range[1])
            else:
                nuke.nodes.Read(file=file_path)
        else:
            self.parent.log_error("Unsupported file extension for %s - no read node will be created." % file_path)        

    def _find_sequence_range(self, path):
        """
        If the path contains a sequence then try to match it
        to a template and use that to extract the sequence range
        based on the files that exist on disk.
        """
        # find a template that matches the path:
        template = None
        try:
            template = self.parent.tank.template_from_path(path)
        except TankError, e:
            self.parent.log_error("Unable to find image sequence range!")
        if not template:
            return
            
        # get the fields and find all matching files:
        fields = template.get_fields(path)
        if not "SEQ" in fields:
            return
        files = self.parent.tank.paths_from_template(template, fields, ["SEQ", "eye"])
        
        # find frame numbers from these files:
        frames = []
        for file in files:
            fields = template.get_fields(file)
            frame = fields.get("SEQ")
            if frame != None:
                frames.append(frame)
        if not frames:
            return
        
        # return the range
        return (min(frames), max(frames))


    def add_file_to_motionbuilder(self, file_path, shotgun_data):
        """
        Load item into motionbuilder.
        
        This will attempt to merge the loaded file with the scene.
        """
        from pyfbsdk import FBApplication

        if not os.path.exists(file_path):
            self.parent.log_error("The file %s does not exist." % file_path)
            return

        # get the slashes right
        file_path = file_path.replace(os.path.sep, "/")
        
        (path, ext) = os.path.splitext(file_path)
        
        if ext != ".fbx":
            self.parent.log_error("Unsupported file extension for %s. Only FBX files are supported." % file_path)
        else:
            app = FBApplication()
            app.FileMerge(file_path)

    def add_file_to_3dsmax(self, file_path, shotgun_data):
        """
        Load item into 3dsmax.
        
        This will attempt to merge the loaded file with the scene.
        """
        from Py3dsMax import mxs
        if not os.path.exists(file_path):
            self.parent.log_error("The file %s does not exist." % file_path)
        else:
            mxs.importFile(file_path)
        
    def add_file_to_photoshop(self, file_path, shotgun_data):
        """
        Load item into Photoshop.        
        """        
        import photoshop        
        f = photoshop.RemoteObject('flash.filesystem::File', file_path)
        photoshop.app.load(f)        
        
