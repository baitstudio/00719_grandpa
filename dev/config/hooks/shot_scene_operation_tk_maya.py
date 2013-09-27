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
                
                #setting fps to 25---
                cmds.currentUnit(time='pal')
                
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
           
        cmds.file(newFile=True, force=True)
        
        animCaches= su.getLatestShotFile(tk, ctx, publishedType = 'Alembic Animation') 
        
        abc_template=tk.templates['cache_alembic']
             
        #for cache in animCaches:
        input_path=animCaches[0]['path']['local_path_windows']
        fields=abc_template.get_fields(input_path)   
        for f in animCaches:
            abcFile = f['path']['local_path_windows']
            print ('cache path: ' + abcFile)
            grp = pm.group( em=True, name=f['name'] )
            mu.alembicImport(abcFile, 'parent', parent=grp)   
        
        camNodes=None
        camData=su.getLatestShotFile(tk, ctx, publishedType='Maya Camera')
        
        if camData!=None:
            camNodes=mu.referenceAsset(camData[0]['path']['local_path_windows'],namespace='camera')
        else:
            cmds.warning('Could not find any asset cameras to reference!')    
        
        '''
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
        '''      
            
            
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
        assets=su.getLatestShotAssets(tk, ctx, publishedType='Maya Rig')
        
        if len(assets)>0:
            for asset in assets:
                print asset
                if asset['assetName'] != 'Grandpa':
                    if asset['assetName'] == 'Main Outfit' or asset['assetName'] == 'Captain Dumbletwit':
                        namespace = 'Grandpa'
                        mu.referenceAsset(asset['path']['local_path_windows'], namespace = namespace)
                    else:
                        mu.referenceAsset(asset['path']['local_path_windows'])
        else:
            cmds.warning('Could not find any assets to reference! Please link the assets in shotgun.')
        
        #reference latest set
        environments = su.getLatestShotAssets(tk, ctx, publishedType='Maya Model', category='Environments')

        if len(environments)>0:
            for set in environments:
                mu.referenceAsset(set['path']['local_path_windows'], namespace = 'set')
        else:
            cmds.warning('Could not find any sets to reference! Please link the assets in shotgun.')

        #query asset cameras, if none exists get shot cameras instead
        camNodes=None
        
        
        camData=su.getLatestShotFile(tk, ctx, publishedType='Maya Camera')      
             
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
            maya_work=tk.templates['shot_work_area']        
            fields=ctx.as_template_fields(maya_work)

            low_plate=tk.templates['low_res_proxy_plate_path']
            plateDir=low_plate.parent.apply_fields(fields)               
            
            qt_plate=tk.templates['quicktime_proxy_plate_path']
            qtplateDir=qt_plate.parent.apply_fields(fields)        
            
            if len(os.listdir(qtplateDir)) > 0:
                firstMovie=os.listdir(qtplateDir)[0]           
                moviePath=qtplateDir+'/'+firstMovie
            elif len(os.listdir(plateDir)) > 0:  
                firstImage=os.listdir(plateDir)[0]          
                imagePath=plateDir+'/'+firstImage
            else:
                print 'Backplate couldn\'t be found'
            #create imagePlane
            try:
                if len(os.listdir(qtplateDir)) > 0:
                    IP = pm.PyNode(mu.imagePlane(cam, moviePath, fileType='movie'))
                else:  
                    IP = pm.PyNode(mu.imagePlane(cam, imagePath))
            except:
                pass
            
            #mu.imagePlane(cam, imagePath)
            IP.depth.set(2000)
            IP.fit.set(0)
            IP.width.set(960)
            IP.height.set(540)
            IP.sizeY.set(0.797)
            IP.sizeX.set(1.417)

        else:
            cmds.warning('Could not find any cameras to reference!')
        
        #set Lambert transparency
        pm.setAttr('lambert1.transparency', 0.5, 0.5, 0.5, type="double3")
        
        
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

        pm.loadPlugin('mtoa.mll',quiet=True)
        pm.loadPlugin('AbcExport.mll', quiet=True)  
        pm.loadPlugin('AbcImport.mll', quiet=True)         


        #Open Arnold Renders Settings template   
        arnoldSetup="M:/00719_grandpa/assets/Environments/arnoldTemplate/publish/arnoldTemplate.rend.v004.ma"
        
        #print str(arnoldSetup)
        shutil.copyfile(arnoldSetup, dst) 
              
        pm.system.openFile(dst, force=True)    
              
        print ('getting latest shot assets')
        #reference light setup scene 
        lightSetup=su.getLatestShotAssets(tk, ctx, publishedType='Maya Lighting')
        print lightSetup
        
        shadowLayer = pm.PyNode('setExtras')
        beautyLayer = pm.PyNode('beauty')
        workLayer = pm.PyNode('defaultRenderLayer')
        
        for asset in lightSetup: 
            print ('loading reference: ' + (asset['path']['local_path_windows']))      
            setNodes = mu.referenceAsset(asset['path']['local_path_windows'])

        workLayer.setCurrent()
            
        #referencing latest camera file 
        print ('getting latest cameras')
        camData=su.getLatestShotFile(tk, ctx, publishedType='Maya Camera')        
        
        maya_work=tk.templates['shot_work_area']        
        fields=ctx.as_template_fields(maya_work)
        
        low_plate=tk.templates['low_res_proxy_plate_path']
        plateDir=low_plate.parent.apply_fields(fields)
        
        qt_plate=tk.templates['quicktime_proxy_plate_path']
        qtplateDir=qt_plate.parent.apply_fields(fields)
        
        if len(os.listdir(qtplateDir)) > 0:
            firstMovie=os.listdir(qtplateDir)[0]       
            print ('moviePlate: ' + firstMovie)     
            moviePath=qtplateDir+'/'+firstMovie
        
        if len(os.listdir(plateDir)) > 0:  
            firstImage=os.listdir(plateDir)[0]    
            print ('imagePlate: ' + firstImage)        
            imagePath=plateDir+'/'+firstImage
        
        full_plate=tk.templates['full_res_proxy_plate_path']
        fullPlateDir=full_plate.parent.apply_fields(fields)
               
        try:
            firstImage=os.listdir(fullPlateDir)[0] 
            imagePath=fullPlateDir+'/'+firstImage
            pm.PyNode('backplate').fileTextureName.set(imagePath)    
        except:
            pass
               
        
        #Checks if shot camera exists. If not tries to find asset camera related to the shot.
        print ('referencing camera')
        try:
            for cam in camData:
                print ('camera is: ' + cam['path']['local_path_windows'])
                camNodes=mu.referenceAsset(cam['path']['local_path_windows'])
            
            print ('connecting camera to projection')      
             
            for node in camNodes:      
                if pm.nodeType(node) == 'camera':
                    cam=pm.PyNode(node)
                    print cam
                    projection = pm.PyNode('projection')
                    cam.message >> projection.linkedCamera                                      
                    #try for image planes---
                    try: 
                        IP = pm.PyNode(mu.imagePlane(cam, imagePath))
                        #mu.imagePlane(cam, imagePath)
                        IP.depth.set(2000)
                        IP.fit.set(0)
                        IP.width.set(960)
                        IP.height.set(540)
                        IP.sizeY.set(0.797)
                        IP.sizeX.set(1.417)
                    except:
                        print ('Backplate not found!!!')                             
                                                                                                  
        except:
            print ('Camera Trouble!!!')

              
        #assign backplate to shadowcatcher material

        
                   
        

        #import alembic files and reference shaded assets
        shotAssets=su.getLatestShotAssets(tk, ctx, publishedType='Maya Shaded Model') 
        
        animCaches=[] 
        animCaches= su.getLatestShotFile(tk, ctx, publishedType='Alembic Animation') 
        
        simCaches=[] 
        simCaches= su.getLatestShotFile(tk, ctx, publishedType='Alembic Simulation') 
        
        cachedAssets=[]
        for cache in animCaches:
            cachedAssets.append(cache['name'])
            
        simmedAssets=[]
        for cache in simCaches:
            simmedAssets.append(cache['name'])
        
        
        abc_template=tk.templates['cache_alembic']
        
            
        #for cache in animCaches:
        try:
            input_path=animCaches[0]['path']['local_path_windows']
            fields=abc_template.get_fields(input_path)   
            for f in animCaches:
                print ('cache path: ' + f['path']['local_path_windows'])
                print f['name']     
            print fields
        except:
            print ('Cache file not found!!!')
        
        importedCaches= []
        failedNodes= []
        #grp = pm.group( em=True, name='cache' )
        for asset in shotAssets:
            try:           
                print ('loading reference for' + asset['assetName']) 
                refNodes = mu.referenceAsset(asset['path']['local_path_windows'], namespace=(asset['assetName'] + 'Shaded'))
                print (asset['assetName'] + ' referenced')
                #make temporary namespace 
                nspaceAnim = (asset['assetName'] + 'Anim')
                pm.namespace( add=nspaceAnim)
                pm.namespace( set=nspaceAnim )
                #import alembic cache for current asset
                if asset['assetName'] in cachedAssets:
                    print ('Loading alembic cache for ' + asset['assetName'])
                    for cache in animCaches:
                        if cache['name'] == asset['assetName']:
                            print ('Abc File: ' + cache['path']['local_path_windows'])
                            #mu.alembicImport(cache['path']['local_path_windows'], 'parent', parent=grp)
                            abcNodes = mu.referenceAsset(cache['path']['local_path_windows'], namespace=nspaceAnim)
                            importedCaches.append(cache['path']['local_path_windows'])
                            print 'done'
                        else:
                            print cache['name']
                else:
                    print ('Cache not found: ' + asset['assetName'])
                   
                nspaceSim = (asset['assetName'] + 'Sim')
                pm.namespace( add=nspaceSim)
                pm.namespace( set=nspaceSim )
                #import alembic cache for current asset
                if asset['assetName'] in simmedAssets:
                    print ('Loading alembic cache for ' + asset['assetName'])
                    for cache in simCaches:
                        if cache['name'] == asset['assetName']:
                            print ('Abc File: ' + cache['path']['local_path_windows'])
                            #mu.alembicImport(cache['path']['local_path_windows'], 'parent', parent=grp)
                            abcNodes = mu.referenceAsset(cache['path']['local_path_windows'], namespace=nspaceSim)
                            importedCaches.append(cache['path']['local_path_windows'])
                            print 'done'
                        else:
                            print cache['name']
                
            except:
                print ('Something went wrong with ' + asset['assetName'])
            
            transformNodes = []
            print ('transfering shaders for: ' + asset['assetName'])
            for node in refNodes:
                #collect all transform nodes
                if pm.nodeType(node)=='transform':
                    transformNodes.append(pm.PyNode(node))         
                try:
                    if pm.nodeType(node) == 'transform' and pm.PyNode(node).hasAttr('asset'): 
                        source = pm.PyNode(node)
                        shadingEngine = source.getShape().connections()
                        SG = str(shadingEngine[0].shortName())
                        target = pm.PyNode(source.swapNamespace(nspaceAnim)).getShape() 
                        pm.sets(SG, e=True, forceElement=target)                                                
                        target.aiOpaque.set(source.getShape().aiOpaque.get())
                        target.aiSubdivType.set(source.getShape().aiSubdivType.get())
                        target.aiSubdivIterations.set(source.getShape().aiSubdivIterations.get()) 
                        target.aiTraceSets.set('cast') 
                        try:
                            if source.swapNamespace(nspaceSim).hasAttr('sim'):
                                targetSim = pm.PyNode(source.swapNamespace(nspaceSim)).getShape()   
                                pm.sets(SG, e=True, forceElement=targetSim)                                                
                                targetSim.aiOpaque.set(source.getShape().aiOpaque.get())
                                targetSim.aiSubdivType.set(source.getShape().aiSubdivType.get())
                                targetSim.aiSubdivIterations.set(source.getShape().aiSubdivIterations.get()) 
                                targetSim.aiTraceSets.set('cast')   
                                source.visibility.set(0)
                            else:
                                source.swapNamespace(nspaceSim).visibility.set(0)
                        except:
                            pass    
                                          
                except:
                    failedNodes.append(str(pm.PyNode(node).shortName()))
                    pass 
                                                    
            #print('These objects couldn\'t be resolved: ' + str(failedNodes))   
            
            #hide referenced asset
            transformNodes[0].visibility.set(0)

            pm.namespace( set=':' )

        #copy objects from master layer to shadow layer
        renderNodes = pm.editRenderLayerMembers(workLayer, query=True, fullNames=True)
        renderPyNodes =[]
        for node in renderNodes:
            renderPyNodes.append(pm.PyNode(node))
        
        try:
            pm.editRenderLayerMembers(shadowLayer, renderNodes)
            pm.editRenderLayerMembers(beautyLayer, renderNodes)
        except:
            print 'couldn\' copy objects to shadow layer'
          
        #make sure we are in the Default render layer    
        workLayer.setCurrent() 
        print 'Setting main render attributes'
        #set parameters on members 
        for node in renderPyNodes:
            if  node.nodeType() == 'transform':
                try:
                    mesh = node.getShape()
                except:
                    pass    
            if  node.nodeType() == 'transform' and node.hasAttr('asset') :            
                mesh.primaryVisibility.set(1)
                mesh.aiTraceSets.set('cast')  
            elif node.nodeType() == 'transform' and mesh!=None:
                if mesh.nodeType() == 'mesh':
                    mesh.primaryVisibility.set(1)
                    mesh.castsShadows.set(1)
                    mesh.aiSelfShadows.set(1)
                    mesh.aiOpaque.set(1)
                    mesh.aiTraceSets.set('shadow')  
                    ProjectionSG = 'projection_matSG'
                    pm.sets(ProjectionSG, e=True, forceElement=mesh)         
        
        #switch to Beauty render layer        
        beautyLayer.setCurrent()    
        print 'Setting overrides for Beauty Layer'
        # Apply layer overrides for shadows catchers and assets    
        for node in renderPyNodes:
            if  node.nodeType() == 'transform':
                try:
                    mesh = node.getShape()
                except:
                    pass  
            if  pm.nodeType(node) == 'transform' and node.hasAttr('asset'):            
                mesh.primaryVisibility.set(1)
            elif node.nodeType() == 'transform' and node.getShape()!=None:
                if mesh.nodeType() == 'mesh':
                    mel.eval('editRenderLayerAdjustment "%s.primaryVisibility";' % mesh)
                    mesh.primaryVisibility.set(0)
            else:
                pass
                
        #switch to Shadow render layer        
        shadowLayer.setCurrent() 
        print 'Setting overrides for Shadow Layer'   
        # Apply layer overrides for shadows catchers and assets    
        for node in renderPyNodes:
            if  node.nodeType() == 'transform':
                try:
                    mesh = node.getShape()
                except:
                    pass  
            if  pm.nodeType(node) == 'transform' and node.hasAttr('asset'):
                mel.eval('editRenderLayerAdjustment "%s.primaryVisibility";' % mesh)
                mesh.primaryVisibility.set(0)
            elif node.nodeType() == 'transform' and node.getShape()!=None:
                if mesh.nodeType() == 'mesh':
                    mel.eval('editRenderLayerAdjustment "%s.primaryVisibility";' % mesh)
                    mesh.primaryVisibility.set(1)                 
                    # NAME OF SHADOW CATCHER IS HARDCODED HERE FOR NOW#                    
                    ShadowCatcherSG = 'ShadowCatcher_matSG'
                    pm.sets(ShadowCatcherSG, e=True, forceElement=mesh)
            else:
                pass

        workLayer.setCurrent() 

        
        pm.confirmDialog( title='Report', message=('New scene was created. These objects couldn\'t have shaders applied: )' + str(failedNodes)), button=['Ok', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No' )
        