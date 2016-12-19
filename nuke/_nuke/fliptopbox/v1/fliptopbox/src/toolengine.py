import os
import nuke
import json
import config
import toolhelper
# creates main panels

def add_toolset(category_default=None):
    print "add_toolset"
    sel = nuke.selectedNodes()

    if len(sel) == 0:
        return nuke.message('Please select some nodes')

    p = nuke.Panel("Add panel")
    p.setWidth(400)
    p.addSingleLineInput("Name", "")
    if category_default:
        category_default = str(category_default).upper()
    else:
        category_default = "---please_choose---"

    categories = toolhelper.get_tools_categories(toolhelper.load_settings()["tools_root"])
    categories.insert(0, category_default)
    categories.append(config.TOOLS_TEMP.upper())
    p.addEnumerationPulldown("Category:", " ".join(categories))

    if p.show():
        if p.value("Name:") != "":
            toolset_full_path = os.path.join(toolhelper.load_settings()["tools_root"], p.value("Category:"), "%s.nk" % (p.value("Name")))

            if os.path.isfile(toolset_full_path):
                if not nuke.ask("The toolset %s exists\nDo you want to replace the existing tool?" % (toolset_full_path)):
                    return

            nuke.nodeCopy(toolset_full_path)
            nuke.message("Cool, %s/%s has been added to the toolset." % (p.value("Category:"), p.value("Name")))
            toolhelper.reload_tools_menu(notify=False)

        else:
            nuke.message("Please choose a category")
    else:
        nuke.message("Please enter a toolset name")


def show_settings():
    print "show_settings"
    settings = toolhelper.load_settings()

    p = nuke.Panel("Settings")
    p.setWidth(400)
    p.addFilenameSearch("tools root:", settings['tools_root'] or "")

    if p.show():
        print "input value(tools root)", p.value("tools root:")
        settings['tools_root'] = p.value("tools root:")

        with open(config.PATH_SETTINGS_FILE, 'w') as sf:
            json.dump(settings, sf)

        toolhelper.reload_tools_menu(notify=False)

def show_info():
    print "show_info"
    info_file = os.path.normpath(os.path.join(os.path.dirname(__file__), "../", "data", "info.json"))

    if not os.path.isfile(info_file):
        print "infor file does not exist"
        return

    with open(info_file) as f:
        info_data = json.load(f)

    logo = os.path.normpath(os.path.join(os.path.dirname(__file__), "../", "img", "icon_64.png"))
    nuke.message('<img src="%s" style="float:right" alt="%s"><h1>%s v%s</h1>\n\n%s' % (logo, config.NS, config.NS, info_data['version'], info_data["info"]))
