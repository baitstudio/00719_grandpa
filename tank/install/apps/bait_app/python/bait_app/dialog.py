"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------
"""
import tank
import platform
import unicodedata
import os
import sys
import pprint
import threading

from tank.platform.qt import QtCore, QtGui
from .ui.dialog import Ui_Dialog

class AppDialog(QtGui.QWidget):

    
    def __init__(self, app):
        QtGui.QWidget.__init__(self)
        self._app = app

        # set up the UI
        self.ui = Ui_Dialog() 
        self.ui.setupUi(self)
        
        self.ui.setupscene.clicked.connect( self.setup_scene)
        
        # set up event listeners        
        self.ui.name.textEdited.connect( self.on_name_change )

    def setup_scene(self):
        self._app.execute_hook("hook_setup_new_scene")
        
    def on_name_change(self, text):
        self._app.log_debug("On name change!")
    
        # get our template
        template_obj = self._app.get_template("template_example")
        
        # get the current context, rendered for this template
        fields = self._app.context.as_template_fields(template_obj)
        context_str = pprint.pformat(fields)
        
        # now add our name field
        fields["name"] = self.ui.name.text()
        fields_str = pprint.pformat(fields)
        
        # turn the fields into a path
        path = template_obj.apply_fields(fields)
        
        # set UI elements
        self.ui.path.setText(path)
        self.ui.template_preview.setText( template_obj.definition )
        self.ui.context.setText("<pre>%s</pre>" % context_str)
        self.ui.fields.setText("<pre>%s</pre>" % fields_str)
    
