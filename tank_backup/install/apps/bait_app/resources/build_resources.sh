#!/usr/bin/env bash
# 
# Copyright (c) 2008 Shotgun Software, Inc
# ----------------------------------------------------

echo "building user interfaces..."
pyside-uic --from-imports dialog.ui > ../python/bait_app/ui/dialog.py

echo "building resources..."
pyside-rcc resources.qrc > ../python/bait_app/ui/resources_rc.py
