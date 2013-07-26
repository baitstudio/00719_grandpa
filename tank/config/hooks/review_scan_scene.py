"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------

This hook scans the scene for nuke renders that are suitable for submission to dailies. 

"""

from tank import Hook
import shutil
import os
import nuke

class GetWriteNodes(Hook):
    
    def execute(self, templates_to_look_for, **kwargs):

        # The default implementation goes through all tank write nodes 
        # and all normal write nodes and checks them against the templates
        # defined in the configuration. Any matching templates are returned.

        resolved_nodes = []
        
        #
        #
        # First look for normal write nodes
        #
        for node in nuke.allNodes("Write"):
            path = node.knobs()["file"].value()
            # see if this path matches any template
            norm_path = path.replace("/", os.path.sep)
            # test the templates
            for t in templates_to_look_for:
                if t.validate(norm_path): 
                    # yay - a matching path!
                    d = {}
                    d["template"] = t
                    d["fields"] = t.get_fields(norm_path)
                    d["node"] = node
                    resolved_nodes.append(d)
                    
        #
        #
        # Now look for Tank write nodes
        #
        for node in nuke.allNodes("WriteTank"):
            try:
                path = node.knobs()["cached_path"].value()
            except:
                # fail gracefully - old version of tank write node?
                pass
            else:
                # see if this path matches any template
                norm_path = path.replace("/", os.path.sep)
                
                # test the templates
                for t in templates_to_look_for:
                    if t.validate(norm_path):
                        # yay - a matching path!
                        d = {}
                        d["template"] = t
                        d["fields"] = t.get_fields(norm_path)
                        d["node"] = node
                        resolved_nodes.append(d)

        # we return a list of dictionaries. 
        # Each dictionary has got the following keys:
        #
        # - template: the tank template associated with the match
        # - fields: the resolved field values (you can resolve the path 
        #   by plugging these into the template)
        # - node: the nuke node object associated with the match
        #
        return resolved_nodes
        
