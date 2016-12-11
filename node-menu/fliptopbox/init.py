import nuke

def hi():
    nuke.message('hiya')

def main():
    m = nuke.menu( 'Nodes' )
    myMenu = m.addMenu( 'Fliptopbox', icon='icon_512.png' )
    myMenu.addCommand( 'Hi there ...', hi, '#h')
    print "hello root init ---- :D"


# bootstrap the mutha
print "zzzz"

main()