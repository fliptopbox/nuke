import xml.etree.ElementTree as ET
import threading, re, struct, time

#Create the svg to roto class
class SvgRoto(threading.Thread):
    def __init__(self, file, maxShapes=300, renderHidden=False):
        threading.Thread.__init__(self)
        #the file name
        self.file = file
        #list of all of the shapes
        self.shapes = []
        #maximum number of shapes
        self.maxShapes = maxShapes
        #render hidden SVG groups
        self.renderHidden = renderHidden
        #load the SVG file
        self._loadSVG()
        #parse the SVG file
        self._parseSVG(self.svg)

    #update nuke progress and kill it if the bar is at 100%
    def _updateProgress(self, progress, message=None):
        if message:
            self.progressBar.setMessage(message)
            self.progressBar.setProgress(progress)
        if progress == 100:
            del(self.progressBar)

    #execute in main thread
    def execute(self, func, *kwargs):
        nuke.executeInMainThread(func, kwargs)

    #execute in main thread with results
    def rexecute(self, func, *kwargs):
        return nuke.executeInMainThreadWithResult(func, kwargs)

    #apparently not needed as Nuke seems to accept float values for vertex positions, but will keep it here just in case something changes in the future
    def float2Hex(self, val):
        #return hex(struct.unpack('<I', struct.pack('f', val))[0]).replace('0x','x')
        return str(val)

    #draw the vector shapes
    def draw(self):
        #width and height of the SVG canvas
        h = self.format.height()
        w = self.format.width()

        #create the RotoPaint node
        self._createRotoNode()

        #strings containing parts of the nodes for version 6 and for version 7 and above
        if nuke.NUKE_VERSION_MAJOR > 6:
            curvesStringTemplate = 'AddMode 0 0 0 0 {{v x3f99999a}\n  {f 0}\n  {n\n   {layer Root\n    {f 0}\n    {t ROOT_POS_X ROOT_POS_Y}\n    {a}\n    SHAPE_STRINGS}}}}'
            shapeStringTemplate = '{curvegroup SHAPE_NAME 512 bezier\n     {{cc\n       {f 8192}\n       {px x41880000\nSHAPE_POINTS}}     idem}\n     {tx 0 SHAPE_POS_X SHAPE_POS_Y}\n     {a vis 1 r RED g GREEN b BLUE a ALPHA str 1 ss 0}}'
        else:
            curvesStringTemplate = 'AddMode 0 1 0 7 Bezier1 AnimTree: "" {\n Version: 1.2\n Flag: 0\n RootNode: 1\n Node: {\n  NodeName: "Root" {\n   Flag: 512\n   NodeType: 1\n   Transform: 0 0 S 0 0 S 0 0 S 0 0 S 0 1 S 0 1 S 0 0 S 0 ROOT_POS_X S 0 ROOT_POS_Y \n   NumOfAttributes: 11\n   "vis" S 0 1 "opc" S 0 1 "mbo" S 0 1 "mb" S 0 1 "mbs" S 0 0.5 "fo" S 0 1 "fx" S 0 0 "fy" S 0 0 "ff" S 0 1 "ft" S 0 0 "pt" S 0 0 \n  }\n  NumOfChildren: NUM_SHAPES\n  SHAPE_STRINGS\n }\n}'

            shapeStringTemplate = 'Node: {\n   NodeName: "SHAPE_NAME" {\n    Flag: 576\n    NodeType: 3\n    CurveGroup: "" {\n     Transform: 0 0 S 1 1 0 S 1 1 0 S 1 1 0 S 1 1 1 S 1 1 1 S 1 1 0 S 1 1 SHAPE_POS_X S 1 1 SHAPE_POS_Y \n     Flag: 0\n     NumOfCubicCurves: 2\n     CubicCurve: "" {\n      Type: 0 Flag: 8192 Dim: 2\n      NumOfPoints: SHAPE_NUM_POINTS\n      SHAPE_POINTS \n     }\n     CubicCurve: "" {\n      Type: 0 Flag: 8192 Dim: 2\n      NumOfPoints: SHAPE_NUM_POINTS\n      FSHAPE_POINTS \n     }\n     NumOfAttributes: 44\n     "vis" S 0 1 "r" S 0 RED "g" S 0 GREEN "b" S 0 BLUE "a" S 0 ALPHA "ro" S 0 0 "go" S 0 0 "bo" S 0 0 "ao" S 0 0 "opc" S 0 1 "bm" S 0 0 "inv" S 0 0 "mbo" S 0 0 "mb" S 0 1 "mbs" S 0 0.5 "mbsot" S 0 0 "mbso" S 0 0 "fo" S 0 1 "fx" S 0 0 "fy" S 0 0 "ff" S 0 1 "ft" S 0 0 "src" S 0 0 "stx" S 0 0 "sty" S 0 0 "str" S 0 0 "sr" S 0 0 "ssx" S 0 1 "ssy" S 0 1 "ss" S 0 0 "spx" S 0 1024 "spy" S 0 778 "stot" S 0 0 "sto" S 0 0 "sv" S 0 0 "sf" S 0 1 "sb" S 0 1 "nv" S 0 1 "view1" S 0 1 "ltn" S 0 1 "ltm" S 0 1 "ltt" S 0 0 "tt" S 0 4 "pt" S 0 0 \n    }\n   }\n   NumOfChildren: 0\n  }'

        shapeStrings = ''
        curvesString = curvesStringTemplate
        cnt=0

        #iterate through the shapes and create the node
        for shapeData in self.shapes:
            shapeString = shapeStringTemplate
            shapePoints = ''
            fshapePoints = ''

            #calculate the bounding box to get the center for the pivot
            maxX = max(t[0] for t in shapeData['path'][0])
            minX = min(t[0] for t in shapeData['path'][0])
            centerX = minX+(maxX - minX)/2
            maxY = max(t[1] for t in shapeData['path'][0])
            minY = min(t[1] for t in shapeData['path'][0])
            centerY = h-(minY+(maxY - minY)/2)

            #iterate through all the positions (points and tangents) and create the shape part of the node
            for i in range(len(shapeData['path'][0])):
                shapeData['path'][0][i] = (self.float2Hex(shapeData['path'][0][i][0]), self.float2Hex(h-shapeData['path'][0][i][1]))
                shapeData['path'][1][i] = (self.float2Hex(shapeData['path'][1][i][0]), self.float2Hex(-shapeData['path'][1][i][1]))
                shapeData['path'][2][i] = (self.float2Hex(shapeData['path'][2][i][0]), self.float2Hex(-shapeData['path'][2][i][1]))
                if nuke.NUKE_VERSION_MAJOR > 6:
                    shapePoints += '\n        {' + shapeData['path'][1][i][0] +' '+ shapeData['path'][1][i][1] + '}\n        {' + shapeData['path'][0][i][0] +' '+ shapeData['path'][0][i][1] + '}\n        {' + shapeData['path'][2][i][0] +' '+ shapeData['path'][2][i][1] + '}'
                else:
                    shapePoints += '0 S 1 1 ' + shapeData['path'][1][i][0] +' S 1 1 '+ shapeData['path'][1][i][1] + ' 0 0 S 1 1 ' + shapeData['path'][0][i][0] +' S 1 1 '+ shapeData['path'][0][i][1] + ' 0 0 S 1 1 ' + shapeData['path'][2][i][0] +' S 1 1 '+ shapeData['path'][2][i][1] + ' 0 '

                    fshapePoints += '0 S 1 1 ' + shapeData['path'][1][i][0] +' S 1 1 '+ shapeData['path'][1][i][1] + ' 0 0 S 1 1 0 S 1 1 0 0 0 S 1 1 ' + shapeData['path'][2][i][0] +' S 1 1 '+ shapeData['path'][2][i][1] + ' 0 '

            #replace all the strings (this could be replaced to use format instead of replace)
            shapeString = shapeString.replace('SHAPE_NUM_POINTS', str(len(shapeData['path'][0])*3))
            shapeString = shapeString.replace('FSHAPE_POINTS', fshapePoints)
            shapeString = shapeString.replace('SHAPE_POINTS', shapePoints)
            shapeString = shapeString.replace('RED', self.float2Hex(shapeData['color'][0]))
            shapeString = shapeString.replace('GREEN', self.float2Hex(shapeData['color'][1]))
            shapeString = shapeString.replace('BLUE', self.float2Hex(shapeData['color'][2]))
            shapeString = shapeString.replace('ALPHA', self.float2Hex(shapeData['color'][3]))
            shapeString = shapeString.replace('SHAPE_NAME', 'Shape'+str(cnt))
            shapeString = shapeString.replace('SHAPE_POS_X', str(centerX))
            shapeString = shapeString.replace('SHAPE_POS_Y', str(centerY))
            shapeStrings = shapeString + shapeStrings
            cnt += 1

        #replace the root node position and append the shapes
        curvesString = curvesString.replace('ROOT_POS_X', str(w/2.0)).replace('ROOT_POS_Y', str(h/2.0))
        curvesString = curvesString.replace('SHAPE_STRINGS', shapeStrings)
        curvesString = curvesString.replace('NUM_SHAPES', str(len(self.shapes)))

        #update the progress bar
        self._updateProgress(99, 'Creating Shapes')
        #create the node
        self.curves.fromScript(curvesString)

    #set the svg format (will take into account only pixel dimensions not relative ones like pt or em)
    def _setFormat(self):
        format = None
        #first try finding the width/height attributes
        try:
            w, h = [int(round(float(self.svg.attrib['width'].replace('px', '')))), int(round(float(self.svg.attrib['height'].replace('px', ''))))]
        except Exception, err:
            #if that fails, try with the viewBox
            try:
                view = [float(dimm) for dimm in self.svg.attrib['viewBox'].replace('px', '').split(' ')]
                w, h = [int(round(view[2]-view[0])), int(round(view[3]-view[1]))]
            #if that fails, put the nuke root format as format dimensions
            except:
                w, h = [nuke.Root().format().width(), nuke.Root().format().height()]
        #create the format if it doesn't exist
        for f in nuke.formats():
            if f.width() == w and f.height() == h:
                format = f
                break
        if not format:
            format = nuke.addFormat( str(w)+' '+str(h)+' 1.0 '+ str(w) + 'x' + str(h) )
        self.format = format

    #load the SVG xml file
    def _loadSVG(self):
        xml = ET.parse(self.file)
        root = xml.getroot()
        self.xml = xml
        self.svg = root
        #set the svg format
        self._setFormat()

    #create the roto node
    def _createRotoNode(self):
        self.node = nuke.createNode('RotoPaint')
        self.curves = self.node['curves']
        self.node['format'].setValue(self.format)

    #convert hex color values to rgb
    def _hex2rgb(self, value):
        try:
            value = value.lstrip('#')
            lv = len(value)
            if lv == 3:
                value = ''.join([c*2 for c in list(value)])
            lv = len(value)
            return tuple(int(value[i:i + lv // 3], 16)/255.0 for i in range(0, lv, lv // 3))
        except:
            return (1,1,1)

    #parse the SVG square shape
    def _parseSVGSquare(self, node):
        w = float(node.attrib['width'])
        h = float(node.attrib['height'])
        x = float(node.attrib['x']) if 'x' in node.keys() else 0
        y = float(node.attrib['y']) if 'y' in node.keys() else x
        rx = float(node.attrib['rx']) if 'rx' in node.keys() else None
        ry = float(node.attrib['ry']) if 'ry' in node.keys() else rx
        if not rx:
            rx = ry
        #draw the SVG square shape
        shape = self.squareShape(w, h, x, y, rx, ry)
        #append results to the shapes list
        self.shapes.append({'path':shape, 'color':self._getSVGNodeColor(node)})

    #parse the SVG circle shape
    def _parseSVGCircle(self, node):
        w = float(node.attrib['r'])
        x = float(node.attrib['cx']) if 'cx' in node.keys() else 0
        y = float(node.attrib['cy']) if 'cy' in node.keys() else x
        #draw the SVG circle shape
        shape = self.ellipseShape(w, w, x=x,y=y)
        #append results to the shapes list
        self.shapes.append({'path':shape, 'color':self._getSVGNodeColor(node)})

    #parse the SVG ellipse shape
    def _parseSVGEllipse(self, node):
        w = float(node.attrib['rx'])
        h = float(node.attrib['ry'])
        x = float(node.attrib['cx']) if 'cx' in node.keys() else 0
        y = float(node.attrib['cy']) if 'cy' in node.keys() else x
        #draw the SVG ellipse shape
        shape = self.ellipseShape(w, h, x=x,y=y)
        #append results to the shapes list
        self.shapes.append({'path':shape, 'color':self._getSVGNodeColor(node)})

    #parse the SVG polygon shape
    def _parseSVGPolygon(self, node):
        path = self._tokenizeSVGCoords(node.attrib['points'])
        pos = []
        ltan = []
        rtan = []
        for i in range(len(path)):
            if i%2 == 0:
                pos.append((path[i], path[i+1]))
                ltan.append((0,0))
                rtan.append((0,0))
        #append results to the shapes list
        self.shapes.append({'path':[pos, ltan, rtan], 'color':self._getSVGNodeColor(node)})

    #parse the path coordiantes and return a list of broken into commands and values
    def _tokenizeSVGCoords(self, pathstring):
        commands = 'MmZzLlHhVvCcSsQqTtAa'
        commandsList = set(commands)
        commandsRe = re.compile("(["+commands+"])")
        valueRe = re.compile("[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?")
        path = []
        for item in commandsRe.split(pathstring):
            if item in commandsList:
                path.append(item)
            for value in valueRe.findall(item):
                path.append(float(value))
        return path

    #parse the SVG path shape
    def _parseSVGPath(self, node):
        #parse the path tokens, the arc token is not parsed, as it would take too much time to create the arc path command in nuke and it rarely used
        #however if you want to do it feel free to write that piece of code :)
        path = self._tokenizeSVGCoords(node.attrib['d'])
        p0 = p1 = (0,0)
        pos = []
        ltan = []
        rtan = []
        startPath = True
        for i in range(len(path)):
            if isinstance('m', basestring):
                if path[i] in ['M', 'm']:
                    #start a path
                    if startPath:
                        startPath = False
                        alpha = False
                    else:
                        alpha = True
                    if path[i].istitle():
                        p0 = (path[i+1], path[i+2])
                    else:
                        p0 = (p0[0]+path[i+1], p0[1]+path[i+2])
                    pos.append(p0)
                    ltan.append((0,0))
                    rtan.append((0,0))

                elif path[i] in ['L', 'l']:
                    if path[i].istitle():
                        p2 = (path[i+1], path[i+2])
                    else:
                        p2 = (p0[0]+path[i+1], p0[1]+path[i+2])
                    pos.append(p2)
                    ltan.append((0,0))
                    rtan.append((0,0))
                    p0 = p2

                elif path[i] in ['H', 'h']:
                    if path[i].istitle():
                        p2 = (path[i+1], p0[1])
                    else:
                        p2 = (p0[0]+path[i+1], p0[1])
                    pos.append(p2)
                    ltan.append((0,0))
                    rtan.append((0,0))
                    p0 = p2

                elif path[i] in ['V', 'v']:
                    if path[i].istitle():
                        p2 = (p0[0], path[i+1])
                    else:
                        p2 = (p0[0], p0[1]+path[i+1])
                    pos.append(p2)
                    ltan.append((0,0))
                    rtan.append((0,0))
                    p0 = p2

                elif path[i] in ['C', 'c']:
                    if path[i].istitle():
                        t1 = (path[i+1]-p0[0], path[i+2]-p0[1])
                        p2 = (path[i+5], path[i+6])
                        t2 = (path[i+3]-p2[0], path[i+4]-p2[1])
                    else:
                        t1 = (path[i+1], path[i+2])
                        p2 = (p0[0]+path[i+5], p0[1]+path[i+6])
                        t2 = (path[i+3]-path[i+5], path[i+4]-path[i+6])
                    pos.append(p2)
                    ltan.append(t2)
                    rtan[-1] = t1
                    rtan.append((0,0))
                    p0 = p2

                elif path[i] in ['S', 's']:
                    if path[i].istitle():
                        t1 = (-t2[0], -t2[1])
                        p2 = (path[i+3], path[i+4])
                        t2 = (path[i+1]-p2[0], path[i+2]-p2[1])
                    else:
                        t1 = (-t2[0], -t2[1])
                        p2 = (p0[0]+path[i+3], p0[1]+path[i+4])
                        t2 = (path[i+1]-path[i+3], path[i+2]-path[i+4])
                    pos.append(p2)
                    ltan.append(t2)
                    rtan[-1] = t1
                    rtan.append((0,0))
                    p0 = p2

                elif path[i] in ['Q', 'q']:
                    if path[i].istitle():
                        p1 = (path[i+1], path[i+2])
                        p2 = (path[i+3], path[i+4])
                    else:
                        p1 = (p0[0]+path[i+1], p0[1]+path[i+2])
                        p2 = (p0[0]+path[i+3], p0[1]+path[i+4])

                    t1x  = p0[0] + 0.666 *(p1[0]-p0[0])
                    t1y  = p0[1] + 0.666 *(p1[1]-p0[1])
                    t2x  = p2[0] + 0.666 *(p1[0]-p2[0])
                    t2y  = p2[1] + 0.666 *(p1[1]-p2[1])
                    t1 = (t1x-p0[0], t1y-p0[1])
                    t2 = (t2x-p2[0],t2y-p2[1])

                    pos.append(p2)
                    ltan.append(t2)
                    rtan[-1] = t1
                    rtan.append((0,0))
                    p0 = p2

                elif path[i] in ['T', 't']:

                    if path[i].istitle():
                        p2 = (path[i+1], path[i+2])
                    else:
                        p2 = (p0[0]+path[i+1], p0[1]+path[i+2])

                    t1 = (-t2[0], -t2[1])
                    t2 = (-t2[1], t2[0])

                    pos.append(p2)
                    ltan.append(t2)
                    rtan[-1] = t1
                    rtan.append((0,0))
                    p0 = p2

                elif path[i] in ['z','Z'] or i == len(path)-1:
                    self.shapes.append({'path':[pos,ltan,rtan], 'color':self._getSVGNodeColor(node, alpha=alpha)})
                    pos = []
                    ltan = []
                    rtan = []
                    if i == len(path)-1:
                        break

    #get ellipse nuke coords
    def ellipseShape(self, w,h, x=0,y=0):
        pos = [(x,-h+y), (-w+x, y), (x,h+y), (w+x,y)]
        ltan = [(w*0.55,0), (0,-h*0.55), (-w*0.55,0), (0,h*0.55)]
        rtan = [(-w*0.55,0), (0,h*0.55), (w*0.55,0), (0,-h*0.55)]
        return [pos, ltan, rtan]

    #get square nuke coords
    def squareShape(self, w,h, x=0,y=0, xr=0,yr=0):
        if xr !=0 and yr ==0:
            yr = xr
        elif xr==0 and yr != 0:
            xr = yr

        if xr!=0 or yr!=0:
            pos = [(x,y+yr), (x, y+h-yr), (x+xr,y+h),(x+w-xr,y+h), (x+w,y+h-yr), (x+w, y+yr), (x+w-xr, y), (x+xr, y)]
            ltan = [(0, -yr/2), (0,0), (-xr/2, 0), (0,0), (0,yr/2), (0,0), (xr/2,0), (0,0)]
            rtan = [(0,0), (0,yr/2), (0,0), (xr/2, 0), (0,0), (0,-yr/2), (0,0), (-xr/2,0)]
        else:
            pos = [(x,y), (x, y+h), (x+w,y+h), (x+w, y)]
            ltan = [(0,0), (0,0), (0,0), (0,0), (0,0), (0,0), (0,0), (0,0)]
            rtan = [(0,0), (0,0), (0,0), (0,0), (0,0), (0,0), (0,0), (0,0)]
        return [pos, ltan, rtan]

    #get svg node color, includes a list of web colors, alpha is defined based on the subpath, subpaths will have alpha to allow for holes, however the Nuke node will just make the whole through the alpha not just through the selected shape, so it will not work exactly like in the SVG file.
    def _getSVGNodeColor(self, node, alpha = False):
        webcolors = {'aliceblue':'#f0f8ff','antiquewhite':'#faebd7','aqua':'#00ffff','aquamarine':'#7fffd4','azure':'#f0ffff','beige':'#f5f5dc','bisque':'#ffe4c4','black':'#000000','blanchedalmond':'#ffebcd','blue':'#0000ff','blueviolet':'#8a2be2','brown':'#a52a2a','burlywood':'#deb887','cadetblue':'#5f9ea0','chartreuse':'#7fff00','chocolate':'#d2691e','coral':'#ff7f50','cornflowerblue':'#6495ed','cornsilk':'#fff8dc','crimson':'#dc143c','cyan':'#00ffff','darkblue':'#00008b','darkcyan':'#008b8b','darkgoldenrod':'#b8860b','darkgray':'#a9a9a9','darkgreen':'#006400','darkkhaki':'#bdb76b','darkmagenta':'#8b008b','darkolivegreen':'#556b2f','darkorange':'#ff8c00','darkorchid':'#9932cc','darkred':'#8b0000','darksalmon':'#e9967a','darkseagreen':'#8fbc8f','darkslateblue':'#483d8b','darkslategray':'#2f4f4f','darkturquoise':'#00ced1','darkviolet':'#9400d3','deeppink':'#ff1493','deepskyblue':'#00bfff','dimgray':'#696969','dodgerblue':'#1e90ff','firebrick':'#b22222','floralwhite':'#fffaf0','forestgreen':'#228b22','fuchsia':'#ff00ff','gainsboro':'#dcdcdc','ghostwhite':'#f8f8ff','gold':'#ffd700','goldenrod':'#daa520','gray':'#808080','green':'#008000','greenyellow':'#adff2f','honeydew':'#f0fff0','hotpink':'#ff69b4','indianred':'#cd5c5c','indigo':'#4b0082','ivory':'#fffff0','khaki':'#f0e68c','lavender':'#e6e6fa','lavenderblush':'#fff0f5','lawngreen':'#7cfc00','lemonchiffon':'#fffacd','lightblue':'#add8e6','lightcoral':'#f08080','lightcyan':'#e0ffff','lightgoldenrodyellow':'#fafad2','lightgray':'#d3d3d3','lightgreen':'#90ee90','lightpink':'#ffb6c1','lightsalmon':'#ffa07a','lightseagreen':'#20b2aa','lightskyblue':'#87cefa','lightslategray':'#778899','lightsteelblue':'#b0c4de','lightyellow':'#ffffe0','lime':'#00ff00','limegreen':'#32cd32','linen':'#faf0e6','magenta':'#ff00ff','maroon':'#800000','mediumaquamarine':'#66cdaa','mediumblue':'#0000cd','mediumorchid':'#ba55d3','mediumpurple':'#9370db','mediumseagreen':'#3cb371','mediumslateblue':'#7b68ee','mediumspringgreen':'#00fa9a','mediumturquoise':'#48d1cc','mediumvioletred':'#c71585','midnightblue':'#191970','mintcream':'#f5fffa','mistyrose':'#ffe4e1','moccasin':'#ffe4b5','navajowhite':'#ffdead','navy':'#000080','oldlace':'#fdf5e6','olive':'#808000','olivedrab':'#6b8e23','orange':'#ffa500','orangered':'#ff4500','orchid':'#da70d6','palegoldenrod':'#eee8aa','palegreen':'#98fb98','paleturquoise':'#afeeee','palevioletred':'#db7093','papayawhip':'#ffefd5','peachpuff':'#ffdab9','peru':'#cd853f','pink':'#ffc0cb','plum':'#dda0dd','powderblue':'#b0e0e6','purple':'#800080','red':'#ff0000','rosybrown':'#bc8f8f','royalblue':'#4169e1','saddlebrown':'#8b4513','salmon':'#fa8072','sandybrown':'#f4a460','seagreen':'#2e8b57','seashell':'#fff5ee','sienna':'#a0522d','silver':'#c0c0c0','skyblue':'#87ceeb','slateblue':'#6a5acd','slategray':'#708090','snow':'#fffafa','springgreen':'#00ff7f','steelblue':'#4682b4','tan':'#d2b48c','teal':'#008080','thistle':'#d8bfd8','tomato':'#ff6347','turquoise':'#40e0d0','violet':'#ee82ee','wheat':'#f5deb3','white':'#ffffff','whitesmoke':'#f5f5f5','yellow':'#ffff00','yellowgreen':'#9acd32','none':'#ffffff'}
        val = '#000000'
        if 'style' in node.keys():
            styles = dict([(style.split(':')[0].strip(), style.split(':')[1].strip()) for style in filter(None, node.attrib['style'].split(';'))])
            if 'fill' in styles.keys():
                val = styles['fill']
        elif 'fill' in node.keys():
            val = node.attrib['fill']
        if val.lower() in webcolors.keys():
            val = webcolors[val.lower()]

        r,g,b = self._hex2rgb(val)
        if alpha:
            a = 0.0
        else:
            a = 1.0
        return [r, g, b, a]

    #set the color on the node
    def setColor(self, shape, color):
        try:
            red, green, blue, alpha = color
            shape.getAttributes().set('r', red)
            shape.getAttributes().set('g', green)
            shape.getAttributes().set('b', blue)
            shape.getAttributes().set('a', alpha)
        except Exception, err:
            print err

    #start parsing the SVG file
    def _parseSVG(self, root):
        for node in root:
            alpha = False
            if node.tag.split('}')[1] == 'g':
                if 'display' in node.keys():
                    if not node.attrib['display'] == 'none' or self.renderHidden:
                        self._parseSVG(node)
                else:
                    self._parseSVG(node)

            elif node.tag.split('}')[1] == 'rect':
                self._parseSVGSquare(node)

            elif node.tag.split('}')[1] == 'circle':
                shape = self._parseSVGCircle(node)

            elif node.tag.split('}')[1] == 'ellipse':
                shape = self._parseSVGEllipse(node)

            elif node.tag.split('}')[1] == 'polygon':
                shape = self._parseSVGPolygon(node)

            elif node.tag.split('}')[1] == 'path':
                shape = self._parseSVGPath(node)

    #run the script in a new thread
    def run(self):
        self.progressBar = nuke.ProgressTask('SVG RotoPaint')
        self._updateProgress(1, 'SVG RotoPaint - Parsing the file')
        self.rexecute( self.draw, )
        self._updateProgress(100, 'Finished')

file = nuke.getFilename('Load Svg to RotoPaint', '*.svg')
if file:
    SvgRoto(file).run()