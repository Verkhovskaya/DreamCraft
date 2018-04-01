import os
from bottle import route, request, static_file, run, post
import time
import zipfile
from main import make_pdf
import shutil

header = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>DreamCraft</title>
    <link rel="stylesheet" href="/get_stylesheet">
</head>
<body>
<a href="http://dreamcraft.live"> 
    <div id="div1">
        <h1> Dream&diams;Craft </h1>
        <h2> Bringing simplicity to design</h2>
    </div>
</a>
"""

ender = """
</body>
</html>
"""

@route('/')
def root():
    return header + """
    <div id="div2">
        <form action="/start">
            <input type="submit" value="Start" />
        </form>
    </div>
    """ + ender

@route('/start')
def start():
    return header + """
    <div id="div2">
        <form action="/upload" method="post" enctype="multipart/form-data">
          Select a file: <input type="file" name="upload" />
          <input type="submit" value="Start upload" />
          <input id="user_id" name="user_id" type="hidden" value=""" + str(int(time.time() % 1000)) + """>
        </form>
    </div>
    """ + ender

@route('/upload', method='POST')
def do_upload():
    user_id = request.forms.get('user_id')
    log = open("/root/pymclevel/log.txt", "a")
    log.write("Got a file from " + str(user_id) + "\n")
    print("Got a file from " + str(user_id) + "\n")
    log.close()

    upload = request.files.get('upload')
    name, ext = os.path.splitext(upload.filename)
    print(name, ext)
    if ext not in (u'.zip'):
        return "File extension not allowed."

    save_path = "/root/pymclevel/data/" + str(user_id)
    if not os.path.exists(save_path):
        os.makedirs(save_path)
        print "Made directory at " + save_path

    file_path = "{path}/{file}".format(path=save_path, file= "as_zip.zip")
    upload.save(file_path)

    zip_ref = zipfile.ZipFile(file_path, 'r')
    zip_ref.extractall(file_path[:-4])
    zip_ref.close()
    print()
    os.rename(file_path[:-4]+"/"+name, save_path + "/map")

    return header + """
    <div id="div2">
    <form action="/dimensions" method="post">
          <input id="user_id" name="user_id" type="hidden" value=""" + user_id + """>
            <p> x1: <input name="x1" type="number" /> </p>
            <p> y1: <input name="y1" type="number" /> </p>
            <p> z1: <input name="z1" type="number" /> </p>
            <p> x2: <input name="x2" type="number" /> </p>
            <p> y2: <input name="y2" type="number" /> </p>
            <p> z2: <input name="z2" type="number" /> </p>
            <input value="Go!" type="submit" />
    </form>
    </div>
    """ + ender


@route('/get_layout/<user_id>')
def greet(user_id):
    return static_file("layout.pdf", root="/root/pymclevel/data/" + str(user_id))

@route('/get_stylesheet')
def stylesheet():
    return static_file("stylesheet.css", root="/root/pymclevel")

@post('/dimensions')
def select_dimensions():
    user_id = request.forms.get('user_id')
    x1 = int(request.forms.get('x1'))
    x2 = int(request.forms.get('x2'))
    y1 = int(request.forms.get('y1'))
    y2 = int(request.forms.get('y2'))
    z1 = int(request.forms.get('z1'))
    z2 = int(request.forms.get('z2'))

    log = open("/root/pymclevel/log.txt", "a")
    log.write("Got dimensions from " + str(user_id) + ". They are: " + str([x1, y1, z1, x2, y2, z2]) + "\n")
    print("Got dimensions from " + str(user_id) + ". They are: " + str([x1, y1, z1, x2, y2, z2]) + "\n")
    log.close()

    make_pdf(user_id, x1, y1, z1, x2, y2, z2)
    #shutil.rmtree("/root/pymclevel/data/" + str(user_id) + "/map", ignore_errors=False, onerror=None)

    text = header + '<div id="div2"> <h2> Your layout: </h2> <embed src="/get_layout/' + str(user_id) + '" height="350px" width="800px"/> </div>\n'
    text += '<div id="div2"> <h2> Enter this into AutoCAD: </h2>\n'
    text += '<textarea rows = "15" cols="60"> ' + open("/root/pymclevel/data/" + str(user_id) + "/commands.scr").read() + " </textarea> </div> </p>"
    text += ender
    return text

@route('/start_image')
def start_image():
    return static_file('puppy.jpg', root="/root/pymclevel")

@route('/background_image')
def background_image():
    return static_file('background_image.jpg', root="/root/pymclevel")

@route('/root_image')
def root_image():
    return static_file('puppy.jpg', root="/root/pymclevel")


run(host='167.99.7.144', port=80, debug=True)
