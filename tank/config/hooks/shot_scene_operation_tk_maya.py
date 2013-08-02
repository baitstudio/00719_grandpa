import os
import sys
import shutil

import maya.cmds as cmds
import maya.mel as mel
import pymel.core as pm

import sgtk
from sgtk import Hook
from tank import TankError
from tank.platform.qt import QtGui

#tools path
sys.path.append('K:/CodeRepo')

import Maya.utils as mu
reload(mu)
import Shotgun.utils as su
reload(su)

class SceneOperation(Hook):
    """
    Hook called to perform an operation with the 
    current scene
    """
    
    def execute(self, operation, file_path, context, **kwargs):
        """
        Main hook entry point
        
        :operation: String
                    Scene operation to perform
        
        :file_path: String
                    File path to use if the operation
                    requires it (e.g. open)
        
        :context:   Context
                    The context the file operation is being
                    performed in.
                    
        :returns:   Depends on operation:
                    'current_path' - Return the current scene
                                     file path as a String
                    'reset'        - True if scene was reset to an empty 
                                     state, otherwise False
                    all others     - None
        """
        if operation == "current_path":
            # return the current scene path
            return cmds.file(query=True, sceneName=True)
        elif operation == "prepare_new":
            
            confirm=pm.confirmDialog( title='Scene Setup', message='Do you want Shotgun to setup the scene?',
                                      button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )
            
            if confirm=='Yes':
                
                #pre setup---
                #query context
                tk=self.parent.tank
                ctx=context
                maya_work=tk.templates['shot_work_area']
                
                fields=ctx.as_template_fields(maya_work)
                
                #setting context
                self._set_context(ctx)
                
                #setup---
                #animation setup
                if fields['Step']=='Anim':
                    self.anim_setup(fields, tk, ctx)
                                
                #simulation setup
                elif fields['Step']=='Sim':
                    self.sim_setup(fields, tk, ctx)
                    
                #lighting setup
                elif fields['Step']=='Light':
                    self.light_setup(fields, tk, ctx)
                
                #post setup---
                commands = sgtk.platform.current_engine().commands
                
                #setting frame range with sync app
                sync_cmd = commands["Sync Frame Range with Shotgun"]["callback"]
                
                sync_cmd()
                
                #prompting for an initial save as
                save_as_cmd = commands["Shotgun Save As..."]["callback"]
                
                save_as_cmd()
        
        elif operation == "open":
            # do new scene as Maya doesn't like opening 
            # the scene it currently has open!   
            cmds.file(new=True, force=True) 
            cmds.file(file_path, open=True)
        elif operation == "save":
            # save the current scene:
            cmds.file(save=True)
        elif operation == "save_as":
            
            # first rename the scene as file_path:
            cmds.file(rename=file_path)
            
            # Maya can choose the wrong file type so
            # we should set it here explicitely based
            # on the extension
            maya_file_type = None
            if file_path.lower().endswith(".ma"):
                maya_file_type = "mayaAscii"
            elif file_path.lower().endswith(".mb"):
                maya_file_type = "mayaBinary"
            
            # save the scene:
            if maya_file_type:
                cmds.file(save=True, force=True, type=maya_file_type)
            else:
                cmds.file(save=True, force=True)
            
            #updating shotgun status
            print 'updating shotgun status'
            
            taskId=context.task['id']
            sg=self.parent.shotgun
            
            data = {'sg_status_list':'ip' }
            
            sg.update("Task",taskId,data)
                
        elif operation == "reset":
            """
            Reset the scene to an empty state
            """
            while cmds.file(query=True, modified=True):
                # changes have been made to the scene
                res = QtGui.QMessageBox.question(None,
                                                 "Save your scene?",
                                                 "Your scene has unsaved changes. Save before proceeding?",
                                                 QtGui.QMessageBox.Yes|QtGui.QMessageBox.No|QtGui.QMessageBox.Cancel)
            
                if res == QtGui.QMessageBox.Cancel:
                    return False
                elif res == QtGui.QMessageBox.No:
                    break
                else:
                    scene_name = cmds.file(query=True, sn=True)
                    if not scene_name:
                        cmds.SaveSceneAs()
                    else:
                        cmds.file(save=True)
            
            # do new file:    
            cmds.file(newFile=True, force=True)
            return True
    
    def sim_setup(self, fields, tk, ctx):
        
        print 'setting up maya Sim scene'
              
        #referencing latest cloth setup
        assets=su.getLatestShotAssets(self,'cloth')
        clothFile = assets[0]['path']['local_path_windows']
        print clothFile
        #setup reference plate
        
        assets = ['grandpa', 'grandpa_root']
        
        cmds.file(newFile=True, force=True)
        pm.importFile(clothFile)
        #loading alembic plugin
        pm.loadPlugin('AbcImport.mll')
        
        
        shotCaches= su.getLatestShotFile(tk, ctx, publishedType = 'Alembic Cache') 
        print shotCaches
        
        abc_template=tk.templates['cache_alembic']
             
        #for cache in shotCaches:
        input_path=shotCaches[0]['path']['local_path_windows']
        fields=cache_alembic.get_fields(input_path)   
        for f in shotCaches:
            print ('cache path: ' + f['path']['local_path_windows'])
            print f['name']     
        print fields
        
        failedNodes= []
        for asset in shotAssets:
            try:           
                fields['Asset']=asset
                abcFile = cache_alembic.apply_fields(fields)
                #import alembic cache for current asset
                #grp = pm.group( em=True, name=asset['assetName'] )
                print ('loading alembic cache for' + asset['assetName'])
                mu.alembicImport(abcFile, 'parent', parent=grp)
                print ('transfering shaders for' + asset['assetName'])
            except:
                print ('asset wasn')
        
        for asset in assets:
            fields['Asset']=asset
            
            cache_alembic=tk.templates['cache_alembic']
            abcFile = cache_alembic.apply_fields(fields)

            abcNodes=[]
            if asset=='grandpa':
                abcNodes = "shoes l_eye r_eye topTeeth bottomTeeth body"
            else:
                abcNodes = "start_null"
       
            #import alembic
            print abcFile
            pm.AbcImport(abcFile, mode="import", ct=abcNodes, ftr=True, crt=True, sts=True)

        sync_cmd = commands["Sync Frame Range with Shotgun"]["callback"]
                
        sync_cmd()
        
        #query time data
        startTime=cmds.playbackOptions(q=True,animationStartTime=True)
        endTime=cmds.playbackOptions(q=True,animationEndTime=True)
        
        pm.currentTime(startTime)
        pm.currentTime(startTime + 1)
        pm.currentTime(startTime - 25)
        
        pm.PyNode('nucleus*').startFrame.set(startTime-25)
        
        ncache=tk.templates['maya_nCache']
        ncachePath=ncache.apply_fields(fields)

        #find all nCloth objects
        clothObjects = pm.ls(type='nCloth')
        
        #create simulation cache for all nCloth nodes in the scene
        print ('caching theses nCloth objects: ' + str(clothObjects))
        cacheFiles = pm.cacheFile(cnd=clothObjects, st=startTime, et=endTime, dir=ncachePath, dtf=True, fm='OneFile', r=True, ws=True)
        
        #apply created cache to simulated objects
        cacheShapes = pm.ls('outputCloth*')
        i=0
        for shape in cacheShapes:
            switch = mel.eval('createHistorySwitch(\"' + str(shape) + '\",false)')
            pm.cacheFile(f=cacheFiles[i], cnm=str(shape), ia='%s.inp[0]' % switch ,attachFile=True, dir=ncachePath)
            pm.setAttr( '%s.playFromCache' % switch, 1 )
            i += 1

    def _set_context(self, ctx):
        """
        Set context based on selected task
        """
        try:
            current_engine_name = self.parent.engine.name            
            if sgtk.platform.current_engine(): 
                sgtk.platform.current_engine().destroy()
            sgtk.platform.start_engine(current_engine_name, ctx.tank, ctx)
        except Exception, e:
            QtGui.QMessageBox.critical(self, 
                                       "Could not Switch!", 
                                       "Could not change work area and start a new " 
                                       "engine. This can be because the task doesn't "
                                       "have a step. Details: %s" % e)
            return
        
    def anim_setup(self, fields, tk, ctx):
        
        print 'Preparing new animation Scene'
        
        cmds.file(newFile=True, force=True)
        
        #referencing latest rigs
        print 'Finding latest Grandpa Rig'
        assets=su.getLatestShotAssets(self,'rig',specific='Grandpa')
        
        if len(assets)>0:
            for asset in assets:
                mu.referenceAsset(asset['path']['local_path_windows'])
        else:
            cmds.warning('Could not find any assets to reference! Please link the assets in shotgun.')
        

        #query asset cameras, if none exists get shot cameras instead
        camNodes=None

        camData=su.getLatestShotFile(tk, ctx, filetag='cam')
        
        if camData!=None:
            camNodes=mu.referenceAsset(camData[0]['path']['local_path_windows'],namespace='camera')
        else:
            cmds.warning('Could not find any asset cameras to reference!')

        
        #getting camera node
        if camNodes!=None:
            for node in camNodes:
                
                if cmds.nodeType(node)=='camera':
                    cam=node
            
            #setup reference plate
            #tk=self.parent.tank
            
            #ctx=self.parent.context
            maya_work=tk.templates['shot_work_area']        
            fields=ctx.as_template_fields(maya_work)
            
            
            low_plate=tk.templates['low_res_proxy_plate_path']
            plateDir=low_plate.parent.apply_fields(fields)
            
            firstFile=os.listdir(plateDir)[0]
            
            imagePath=plateDir+'/'+firstFile
            mu.imagePlane(cam, imagePath)
        else:
            cmds.warning('Could not find any cameras to reference!')
        
    def light_setup(self, fields, tk, ctx):       
        
        '''
        This script is errorring, but once it runs through everything is setup correctly
        so the errorr has ben put on hold. 
        Error:  Message: There was a problem starting the Tank Engine.
                Please contact tanksupport@shotgunsoftware.com
                Exception: <class 'tank.errors.TankError'> - Key '<Tank StringKey Step>' in template '<Tank TemplatePath asset_work_area_maya: assets/{sg_asset_type}/{Asset}/work/{Step}/>' 
                could not be populated by context 'Asset arnoldTemplate' because the context does not contain a shotgun entity of type 'Step'!
        
        ------------------------------------
        
        Might need extra part at the end, which assigns objects to render layers. We haven't decided whether this needs to be implemented or not. 
       
        '''
        
        #cmds.file(newFile=True, force=True)
        
        print ('Communicating with shotgun, please wait!')
                        
         
        temp_file=tk.templates['light_setup_temp']
        #fields_temp=ctx.as_template_fields(temp_file)
        #tempPath = temp_file.apply_fields(fields_temp)
        
        tk.templates['maya_shot_work']
        
        dst=temp_file.apply_fields(fields)

        
        try:
            pm.loadPlugin('mtoa.mll')           
        except:
            pass

        
        #Open Arnold Renders Settings template
        
        arnoldSetup="M:/00719_grandpa/assets/Environments/arnoldTemplate/publish/arnoldTemplate.rend.v001.ma"
        #print str(arnoldSetup)
        shutil.copyfile(arnoldSetup, dst) 
        
        '''  
        arnoldSetup=su.getLatestShotAssets(self,'rend') 
        for file in arnoldSetup:
            #pm.system.openFile(file['path']['local_path_windows'], force=True)
            shutil.copyfile(file['path']['local_path_windows'], dst)
        ''' 
        
        pm.system.openFile(dst, force=True)    
        
        
        #print ('path is' + tempPath)
        #pm.system.saveAs(tempPath)
        
        
        #scene_path = os.path.abspath(cmds.file(query=True, sn=True))
        #print scene_path

        
        
        
        print ('getting latest shot assets')
        #reference light setup scene 
        lightSetup=su.getLatestShotAssets(self,'light')
        print lightSetup
    
        for asset in lightSetup: 
            print ('loading reference: ' + (asset['path']['local_path_windows']))      
            setNodes = mu.referenceAsset(asset['path']['local_path_windows'])
            
            for node in setNodes:
                #print ('node is: ' + node)
                if pm.nodeType(node) == 'mesh':
                    mesh = pm.PyNode(node)
                    #print ('mesh is: ' + mesh)       
                    mesh.aiSelfShadows.set(0)
                    mesh.aiOpaque.set(0)   
                    # NAME OF SHADOW CATCHER IS HARDCODED HERE FOR NOW#                    
                    ShadowCatcherSG = 'ShadowCatcher_matSG'
                    pm.sets(ShadowCatcherSG, e=True, forceElement=mesh)
                    
        
        #referencing latest camera file 
        print ('getting latest cameras')
        camData=su.getLatestShotFile(tk,ctx, filetag='cam')        
        
        #Checks if shot camera exists. If not tries to find asset camera related to the shot.
        print ('referencing camera')
        for cam in camData:
            print ('camera is: ' + cam['path']['local_path_windows'])
            camNodes=mu.referenceAsset(cam['path']['local_path_windows'])
        
        
                
        #connect camera to projection
        print ('connecting camera to projection')        
        for node in camNodes:       
            if pm.nodeType(node) == 'camera':
                cam=pm.PyNode(node)
                print cam
                projection = pm.PyNode('projection')
                cam.message >> projection.linkedCamera
              
        #assign backplate to shadowcatcher material
            #tk=self.parent.tank
            
            #ctx=self.parent.context
        maya_work=tk.templates['shot_work_area']        
        fields=ctx.as_template_fields(maya_work)
                   
        low_plate=tk.templates['low_res_proxy_plate_path']
        plateDir=low_plate.parent.apply_fields(fields)
        print ('plates: ' + plateDir)
        
        try:
            firstFile=os.listdir(plateDir)[0]
            imagePath=plateDir+'/'+firstFile
            pm.PyNode('backplate').fileTextureName.set(imagePath)    
        except:
            pass
               
        #set Arnold DOF attribute on the camera        
        cam.aiEnableDOF.set(1)

        
        #import alembic files and reference shaded assets
        shotAssets=su.getLatestShotAssets(self,'shaded') 
        print shotAssets
        
        shotCaches= su.getLatestShotFile(tk, ctx, publishedType = 'Alembic Cache') 
        print shotCaches
        
        abc_template=tk.templates['cache_alembic']
             
        #for cache in shotCaches:
        input_path=shotCaches[0]['path']['local_path_windows']
        fields=abc_template.get_fields(input_path)   
        for f in shotCaches:
            print ('cache path: ' + f['path']['local_path_windows'])
            print f['name']     
        print fields
        
        failedNodes= []
        for asset in shotAssets:
            try:           
                print ('loading reference for' + asset['assetName']) 
                refNodes = mu.referenceAsset(asset['path']['local_path_windows'])
                print refNodes
                fields['Asset']=asset['assetName']
                abcFile = abc_template.apply_fields(fields)
                #make temporary namespace
                pm.namespace(add='temp')
                pm.namespace(set='temp')
                #import alembic cache for current asset
                grp = pm.group( em=True, name=asset['assetName'] )
                print ('loading alembic cache for' + asset['assetName'])
                mu.alembicImport(abcFile, 'parent', parent=grp)
                print ('transfering shaders for' + asset['assetName'])
            except:
                print ('asset wasn')
            
            transformNodes = []
            for node in refNodes:
                #collect all transform nodes
                if pm.nodeType(node)=='transform':
                    transformNodes.append(pm.PyNode(node))
                    
                try:
                    if pm.nodeType(node) == 'transform' and pm.PyNode(node).hasAttr('asset'): 
                        source = pm.PyNode(node)
                        shadingEngine = source.getShape().connections()
                        SG = str(shadingEngine[0].shortName())
                        target = pm.PyNode(source.swapNamespace('temp')).getShape()
                        pm.sets(SG, e=True, forceElement=target)                       
                except:
                    failedNodes.append(str(pm.PyNode(node).shortName()))
                    pass 
                                         
            print('These objects couldn\'t be resolved: ' + str(failedNodes))   
            
            #hide referenced asset
            transformNodes[0].visibility.set(0)
            
            #clear the temp namespace  
            pm.namespace( set=':' )
            pm.namespace(mv=('temp', ':'))
            pm.namespace(rm='temp')
        
        shadowLayer = pm.PyNode('shadowLayer')
        masterLayer = pm.PyNode('defaultRenderLayer')
        
        #copy objects from master layer to shadow layer
        renderNodes = pm.editRenderLayerMembers(masterLayer, query=True )
        print
        try:
            pm.editRenderLayerMembers(shadowLayer, renderNodes)
        except:
            print 'couldn\' copy objects to shadow layer'
          
        #make sure we are in the Default render layer    
        masterLayer.setCurrent() 
        #set parameters on members 
        for node in renderNodes:
            if  pm.nodeType(node) == 'transform' and pm.PyNode(node).hasAttr('asset'):
                mesh = pm.PyNode(node).getShape()
                mesh.primaryVisibility.set(1)
                mesh.aiSubdivType.set(1);
                mesh.aiSubdivIterations.set(2);
            elif pm.nodeType(node) == 'transform':
                try:
                    mesh = pm.PyNode(node).getShape()
                    mesh.primaryVisibility.set(0)
                    mesh.aiSelfShadows.set(0)
                    mesh.aiOpaque.set(0)
                except:
                    print ('This node is not a mesh: ' + node)
            else:
                pass
                
                
                
        #switch to Shadow render layer        
        shadowLayer.setCurrent()    
        # Apply layer overrides for shadows catchers and assets    
        for node in renderNodes:
            if  pm.nodeType(node) == 'transform' and pm.PyNode(node).hasAttr('asset'):
                mesh = pm.PyNode(node).getShape()
                mel.eval('editRenderLayerAdjustment "%s.primaryVisibility";' % mesh)
                mesh.primaryVisibility.set(0)
            elif pm.nodeType(node) == 'transform':
                try:
                    mesh = pm.PyNode(node).getShape()
                    mel.eval('editRenderLayerAdjustment "%s.primaryVisibility";' % mesh)
                    mesh.primaryVisibility.set(1)
                except:
                    print ('This node is not a mesh: ' + node)
            else:
                pass
                #mesh.aiSelfShadows.set(0)
                #mesh.aiOpaque.set(0)
        
        pm.confirmDialog( title='Report', message=('New scene was created. These objects couldn\'t have shaders applied: )' + str(failedNodes)), button=['Ok', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No' )
        