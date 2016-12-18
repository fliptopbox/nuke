import os
import json
import config
import nuke
import toolengine

# controls for main module
def reload_tools_menu(notify=True):
    print "reload_tools_menu"
    all_tools_before = get_all_tools()

    load_tools()
    all_tools_after = get_all_tools()

    diff_list = [tool for tool in all_tools_after if tool not in all_tools_before]
    diff_msg = "\n".join(diff_list)

    if notify and diff_msg:
        nuke.message("%s new tools found\n\n%s" % (len(diff_list), diff_msg))

def get_all_tools():
    all_tools = []

    for item in nuke.menu("Nodes").findItem(config.NS).items():
        if item.name().isupper():
            tool_menu = nuke.menu("Nodes").findItem("%s/%s" % (config.NS, item.name()))
            try:
                for tool in tool_menu.items():
                    all_tools.append("%s/%s" % (tool_menu.name(), tool.name()))
            except:
                continue

    return all_tools

def load_tools(notify=True):
    print "load_tools"
    settings = load_settings()
    # print get_tools_categories(settings['tools_root'])

    return build_tools_menu(settings['tools_root'])

def load_settings():

    settings_file = config.PATH_SETTINGS_FILE

    if not os.path.isdir(os.path.dirname(settings_file)):
        os.makedirs(os.path.dirname(settings_file))

    if not os.path.isfile(settings_file):
        with open(settings_file, "w") as f:
            f.write('{"tools_root": ""}')

    return json.load(open(settings_file, 'r'))

def get_tools_categories(tools_root):

    tools_categories = []
    if not os.path.isdir(tools_root):
        return tools_categories

    for item in os.listdir(tools_root):
        item_full_path = os.path.join(tools_root, item)
        if os.path.isdir(item_full_path) and item != config.TOOLS_TEMP and item not in config.TOOLSDIR_IGNORE:
            tools_categories.append(item)

    return tools_categories

def build_tools_menu(tools_root):

    if not os.path.isdir(tools_root):
        if tools_root == '':
            print "no folder set"
        else:
            print "Tool folder doesn\'t exist"
        return -1

    te_menu = nuke.menu("Nodes").findItem(config.NS)
    tool_categories = get_tools_categories(tools_root)
    tool_count = 0

    for category in tool_categories:

        category_menu = te_menu.addMenu(category.upper())
        items_full_path = os.path.join(tools_root, category)

        # Add a short cut command
        category_menu.addCommand("Add tool here ...", lambda category_menu=category.upper(): toolengine.add_toolset(category_menu), icon='')
        for tool in os.listdir(items_full_path):
            if os.path.splitext(tool)[-1] == '.nk':
                tool_count += 1
                toolset_path = os.path.join(items_full_path, tool)
                category_menu.addCommand(tool.replace('.nk', ''), lambda toolset_path=toolset_path: insert_toolset(toolset_path, delete=False), icon='')

    temp_menu = te_menu.addMenu(config.TOOLS_TEMP.upper())
    temp_dir = os.path.join(tools_root, config.TOOLS_TEMP)

    temp_menu.addCommand("Add tool here ...", lambda category_menu=config.TOOLS_TEMP.upper(): toolengine.add_toolset(category_menu), icon='')
    if not os.path.isdir(temp_dir):
        os.makedirs(temp_dir)

    for tool in os.listdir(temp_dir):
        if os.path.splitext(tool)[-1] == '.nk':
            tool_count += 1
            toolset_path = os.path.join(tools_root, config.TOOLS_TEMP, tool)
            temp_menu.addCommand(tool.replace('.nk', ''), lambda toolset_path=toolset_path: insert_toolset(toolset_path, delete=True), icon='')

    # nuke.message('tool_count' + tool_count)
    return 3

def insert_toolset(toolpath, delete=False):

    if not os.path.isfile(toolpath):
        nuke.message("The tool cannot be found")
        return

    nuke.nodePaste(toolpath)

    if delete:
        print "delete this tool", toolpath
        os.remove(toolpath)

        toolset_name = os.path.splitext(os.path.basename(toolpath))[0]
        nuke.menu("Nodes").findItem("%s/%s" % (config.NS, config.TOOLS_TEMP.upper())).removeItem(toolset_name)


