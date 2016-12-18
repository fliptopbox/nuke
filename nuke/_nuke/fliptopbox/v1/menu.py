import nuke
import os

import fliptopbox.src.toolengine as toolengine
import fliptopbox.src.toolhelper as helper


logo = os.path.normpath(os.path.join(os.path.dirname(__file__), "fliptopbox", "img", "icon_512.png"))

te_menu = nuke.menu("Nodes").addMenu("fliptopbox", icon=logo)

te_menu.addCommand("reload", helper.reload_tools_menu, "Alt+R")
te_menu.addSeparator()

tool_total = helper.load_tools()

if tool_total:
    te_menu.addSeparator()

te_menu.addCommand("add_toolset", toolengine.add_toolset)
te_menu.addCommand("settings", toolengine.show_settings)
te_menu.addCommand("info", toolengine.show_info)

print("tool_total %s" % tool_total)