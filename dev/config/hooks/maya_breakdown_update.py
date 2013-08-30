"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------

Hook that contains the logic for updating a reference from one version to another.
Coupled with the scene scanner hook - for each type of reference that the scanner
hook can detect, a piece of upgrade logic should be provided in this file.

"""

from tank import Hook
import maya.cmds as cmds
import pymel.core as pm
import Maya.utils as mu
reload(mu)

class MayaBreakdownUpdate(Hook):
    
    def execute(self, items, **kwargs):

        # items is a list of dicts. Each dict has items node_type, node_name and path

        for i in items:
            node = i["node_name"]
            node_type = i["node_type"]
            new_path = i["path"]
        
            engine = self.parent.engine
            engine.log_debug("%s: Updating reference to version %s" % (node, new_path))
    
            if node_type == "reference":
                # maya reference            
                rn = pm.system.FileReference(node)
                rn.replaceWith(new_path)
                
            elif node_type == "file":
                # file texture node
                file_name = cmds.getAttr("%s.fileTextureName" % node)
                cmds.setAttr("%s.fileTextureName" % node, new_path, type="string")
            
            elif node_type == "AlembicNode":  
                    
                grp = pm.group( em=True, name='cacheNew' )
            
                abcImport = mu.alembicImport(new_path, 'parent', parent=grp)
    
                abcNodes = pm.ls(abcImport) 
                
                for abcNode in abcNodes:
                    abcConnections = pm.PyNode(abcNode).listConnections(connections=True, skipConversionNodes=True)
                    targetGrp = []
                    for connection in abcConnections:
                        if connection[1].hasAttr('asset'):
                            targetGrp = pm.ls((connection[1].getAttr('asset') + ':*'), type='shape')
                            break
                    
                    for connection in abcConnections:
                        sourceConnection = connection[0]
                        if connection[1].hasAttr('asset'):
                            sourceNode = connection[1].getShape()
                            print sourceNode    
                            for target in targetGrp:
                                if target.stripNamespace() == sourceNode.stripNamespace():
                                    print ('source: ' + sourceNode)
                                    print ('target: ' + target) 
                                    sourceConnection // sourceNode.inMesh    
                                    sourceConnection >> target.inMesh   
                    
                    pm.delete(grp)           
                
            else:
                raise Exception("Unknown node type %s" % node_type)

