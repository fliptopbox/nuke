#!/usr/bin/python

import sys
import base64
import re


dct = [
    'index.html',
    'style.css',
    'zepto.min.js',
    'main.js'
]

# gernarate the packed executable
mkproxy = open('assets/make-proxy-build.py', 'r').read()

build = re.compile('(build = ([0-9]+))', re.M).search(mkproxy).group(2)
build = int(build) + 1

# bump the build version
mkproxy = re.compile('build = ([0-9]+)').sub(str('build = %s' % (build) ), mkproxy, 1)
open('assets/make-proxy-build.py', 'w').write(mkproxy)

# gernate the base64 strings
for filename in dct:
    # unpack and write the asset to the asset folder
    
    print "%s" % (filename)
    text = open('assets/'+ filename, 'r').read()
    b64txt = base64.b64encode(text)

    # replace the b64 tokkens
    mkproxy = re.sub('\{\{'+filename+'\}\}', b64txt, mkproxy)

open('make-proxy.py', 'w').write(mkproxy)

