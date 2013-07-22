import os
import sys

#tools path
sys.path.append('K:/CodeRepo')

import tank
import maya.cmds as cmds
import maya.mel as mel
import pymel.core as pm

import Maya.utils as mu
import Maya.sim as ms
import Shotgun.utils as su

class SetupNewScene(tank.Hook):
    
    def execute(self,**kwargs):
        
        #query engine
        if self.parent.engine.name == "tk-maya":
            
            #query context
            tk=self.parent.tank
            ctx=self.parent.context
            maya_work=tk.templates['shot_work_area']
            
            fields=ctx.as_template_fields(maya_work)
            
            #animation setup
            if fields['Step']=='Anim':
                self.maya_anim_setup()
                            
            #simulation setup
            elif fields['Step']=='Sim':
                self.maya_sim_setup()
                
             #lighting setup
            elif fields['Step']=='Light':
                self.maya_light_setup()
    
    
    def maya_sim_setup(self):
        
        pm.confirmDialog( title='Confirm', message='Are you sure you want to create a new scene?', button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )
        
        print 'setting up maya Sim scene'
              
        #referencing latest cloth setup
        assets=su.getLatestShotAssets(self,'cloth')
        clothFile = assets[0]['path']['local_path_windows']
        print clothFile
        #setup reference plate
        tk=self.parent.tank
        
        ctx=self.parent.context
        maya_work=tk.templates['shot_work_area']
        
        fields=ctx.as_template_fields(maya_work)
        assets = ['grandpa', 'start_null']
        
        cmds.file(newFile=True, force=True)
        pm.importFile(clothFile)
        #loading alembic plugin
        pm.loadPlugin('AbcImport.mll')
        
        for asset in assets:
            fields['Asset']=asset
            
            cache_alembic=tk.templates['cache_alembic']
            abcFile = cache_alembic.apply_fields(fields)
            
            ncache=tk.templates['maya_nCache']
            ncachePath=ncache.apply_fields(fields)
            
            if asset=='grandpa':
                abcNodes = "shoes l_eye r_eye topTeeth bottomTeeth body"
            else:
                abcNodes = "start_null"
       
            #import alembic
            print abcFile
            pm.AbcImport(abcFile, mode="import", ct=abcNodes, ftr=True, crt=True, sts=True)

       
        #query time data
        startTime=cmds.playbackOptions(q=True,animationStartTime=True)
        endTime=cmds.playbackOptions(q=True,animationEndTime=True)
        
        pm.currentTime(startTime)
        pm.currentTime(startTime + 1)
        pm.currentTime(startTime)
        
        pm.PyNode('nucleus*').startFrame.set(startTime)
        

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
            cacheNode = pm.cacheFile(f=cacheFiles[i], cnm=str(shape), ia='%s.inp[0]' % switch ,attachFile=True, dir=ncachePath)
            pm.setAttr( '%s.playFromCache' % switch, 1 )
            i += 1

        
    def maya_anim_setup(self):
        
        pm.confirmDialog( title='Confirm', message='Are you sure you want to create a new scene?', button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )
        
        #pm.newFile(f=1, typ='mayaAscii')
        
        cmds.file(newFile=True, force=True)
        '''
        #referencing latest rigs
        assets=su.getLatestShotAssets(self,'rig',specific='Grandpa')
        
        if len(assets)>0:
        
            for asset in assets:
                
                mu.referenceAsset(asset['path']['local_path_windows'])
        else:
            cmds.warning('Could not find any assets to reference! Please link the assets in shotgun.')
        '''
        #referencing latest camera track
        camData=su.getLatestShotAssets(self,'cam',specific=None)
        
        #query asset cameras, if none exists get shot cameras instead
        camNodes=None
        if len(camData)<1:
            camData=su.getLatestShotFile(self,'cam', 'FUUUUUUUUUUUUCK')
            
            if camData!=None:
                camNodes=mu.referenceAsset(camData['path']['local_path_windows'])
            else:
                cmds.warning('Could not find any asset cameras to reference!')
        else:
            camNodes=mu.referenceAsset(camData['path']['local_path_windows'])
        
        #getting camera node
        if camNodes!=None:
            for node in camNodes:
                
                if cmds.nodeType(node)=='camera':
                    cam=node
            
            #setup reference plate
            tk=self.parent.tank
            
            ctx=self.parent.context
            maya_work=tk.templates['shot_work_area']        
            fields=ctx.as_template_fields(maya_work)
            
            
            low_plate=tk.templates['low_resolution_plate']
            plateDir=low_plate.parent.apply_fields(fields)
            
            firstFile=os.listdir(plateDir)[0]
            
            imagePath=plateDir+'/'+firstFile
            mu.imagePlane(cam, imagePath)
        else:
            cmds.warning('Could not find any cameras to reference!')
        
    def maya_light_setup(self):       
        
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
        
        pm.confirmDialog( title='Confirm', message='Are you sure you want to create a new scene?', button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )
        
        pm.newFile(f=1, typ='mayaAscii')
        
        print ('Communicating with shotgun, please wait!')
                        
        tk=self.parent.tank      
        ctx=self.parent.context
        
        try:
            pm.loadPlugin('mtoa.mll')           
        except:
            pass
       
        
        #Open Arnold Renders Settings template
        arnoldSetup=su.getLatestShotAssets(self,'rend')
        print str(arnoldSetup)
                
        for file in arnoldSetup:
            pm.system.openFile(file['path']['local_path_windows'], force=True)
 
        temp_file=tk.templates['light_setup_temp']
        fields_temp=ctx.as_template_fields(temp_file)
        tempPath = temp_file.apply_fields(fields_temp)
        pm.system.saveAs(tempPath)
        
        #reference light setup scene 
        lightSetup=su.getLatestShotAssets(self,'light')
        
        for asset in lightSetup: 
            print ('loading reference: ' + asset['path']['local_path_windows'])         
            setNodes = mu.referenceAsset(asset['path']['local_path_windows'])
            
            for node in setNodes:
                print ('node is: ' + node)
                if pm.nodeType(node) == 'mesh':
                    mesh = pm.PyNode(node)
                    print ('mesh is: ' + mesh)       
                    mesh.aiSelfShadows.set(0)
                    mesh.aiOpaque.set(0)   
                    # NAME OF SHADOW CATCHER IS HARDCODED HERE FOR NOW#                    
                    ShadowCatcherSG = 'ShadowCatcher_matSG'
                    pm.sets(ShadowCatcherSG, e=True, forceElement=mesh)
        
        #referencing latest camera file 
        camData=su.getLatestShotFile(self, 'cam')        
        print ('loading cameras') 
        
        if len(camData)<1:
                camData=su.getLatestShotFile(self, 'cam')
                
                camNodes=mu.referenceAsset(camData['path']['local_path_windows'])
        else:
                camNodes=mu.referenceAsset(camData['path']['local_path_windows'])
                
        #connect camera to projection        
        for node in camNodes:       
            if pm.nodeType(node) == 'camera':
                cam=pm.PyNode(node)
                print cam
                projection = pm.PyNode('projection')
                cam.message >> projection.linkedCamera
                
        #assign backplate to shadowcatcher material
            tk=self.parent.tank
            
            ctx=self.parent.context
            maya_work=tk.templates['shot_work_area']        
            fields=ctx.as_template_fields(maya_work)
                       
            low_plate=tk.templates['low_resolution_plate']
            plateDir=low_plate.parent.apply_fields(fields)
            
            firstFile=os.listdir(plateDir)[0]
            
            imagePath=plateDir+'/'+firstFile
            pm.PyNode('backplate').fileTextureName.set(imagePath)    
 
               
        #set Arnold DOF attribute on the camera        
        cam.aiEnableDOF.set(1)
        
       #import alembic files and reference shaded assets
        shotAssets=su.getLatestShotAssets(self,'shaded') 
        cache_alembic=tk.templates['cache_alembic']
        fields=ctx.as_template_fields(cache_alembic)
        
        failedNodes= []
        for asset in shotAssets:
            
            print ('loading reference for' + asset['assetName']) 
            refNodes = mu.referenceAsset(asset['path']['local_path_windows'])
            fields['Asset']=asset['assetName']
            abcFile = cache_alembic.apply_fields(fields)
            #make temporary namespace
            pm.namespace(add='temp')
            pm.namespace(set='temp')
            #import alembic cache for current asset
            grp = pm.group( em=True, name=asset['assetName'] )
            print ('loading alembic cache for' + asset['assetName'])
            mu.alembicImport(abcFile, 'parent', parent=grp)
            print ('transfering shaders for' + asset['assetName'])
            
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
        
        
        #set rendertime subdivision on all meshes to catclark, 2 iterations
        meshes = pm.ls(type='mesh')
        
        shadowLayer = pm.PyNode('shadowLayer')
        masterLayer = pm.PyNode('defaultRenderLayer')
        
        #copy objects from master layer to shadow layer
        renderNodes = pm.editRenderLayerMembers(masterLayer, query=True )
        try:
            pm.editRenderLayerMembers(shadowLayer, renderNodes)
        except:
            print 'ups'
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
                    print (node + 'is probably not a mesh')
        
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
                    print (node + 'is probably not a mesh')
                #mesh.aiSelfShadows.set(0)
                #mesh.aiOpaque.set(0)
        
        pm.confirmDialog( title='Report', message=('New scene was created. These objects couldn\'t have shaders applied: )' + str(failedNodes)), button=['Ok', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No' )
    