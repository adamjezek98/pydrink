import threading
import database
import http.server
import pydrink
from random import randint


class Webserver(threading.Thread):
    running = False

    def __init__(self, address, port, file):
        threading.Thread.__init__(self)
        self.server = http.server.HTTPServer((address, port), WebHandler)
        self.server.RequestHandlerClass.dbfile = file


    def run(self):
        self.running = True
        self.mainloop()

    def stop(self):
        self.running = False

    def mainloop(self):
        while self.running:
            self.server.handle_request()


class WebHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        return
    def do_POST(self):
        length = int(self.headers['content-length'])
        #print(self.path)
        data_string = str(self.rfile.read(length), "utf-8")
        #print(data_string)
        result = 'error'
        if self.path.startswith("/progress"):
            result = self.pd.progress

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(bytes(str(result), "utf-8"))

    def get_file(self, name):
        with open(name, "r") as f:
            return "".join(f.readlines())

    def do_GET(self):
        db = database.Database(self.dbfile)
        path = self.path
        print(path)
        response = ""
        content_type = "text/html"
        layout = self.get_file("templates/layout.html")
        if path.startswith("/webfiles/"):
            f = open(path[1:], "rb")
            if path.endswith(".css"):
                content_type = "text/css"
            elif path.endswith(".ttf"):
                content_type = "font/opentype"

            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.end_headers()
            # self.wfile.write(bytes(str(response), "utf-8"))
            self.wfile.write(f.read())
            f.close()
            return
        elif path.startswith("/home"):
            drinks = db.get_drinks()

            response = layout
            response = response.replace("%%layout_content%%", self.get_file("templates/select.html"))
            drink_item = self.get_file("templates/drink-item.html")
            cont = ""
            for drink in drinks:
                cont += drink_item.replace("%%drink_name%%", drink[1]).replace("%%drink_id%%", str(drink[0]))
            response = response.replace("%%drink_items%%", cont)
        elif path.startswith("/makedrink/"):
            drink_id = int(path.split("/")[-1])
            response = layout.replace("%%layout_content%%", self.get_file("templates/makedrink.html"))
            drink_det = db.get_drink_detail(drink_id)
            response = response.replace("%%drink_name%%",drink_det[0]).replace("%%drink_id%%",str(drink_id))
        elif path.startswith("/makingdrink/"):
            drink_id = int(path.split("/")[-1])
            self.pd.prepare_run("makedrink",drink_id)


            response = layout.replace("%%layout_content%%", self.get_file("templates/makingdrink.html"))
            drink_det = db.get_drink_detail(drink_id)
            response = response.replace("%%drink_name%%",drink_det[0]).replace("%%drink_id%%",str(drink_id))

        elif path.startswith("/drinkdone"):
            response = layout.replace("%%layout_content%%", self.get_file("templates/drinkdone.html"))

        elif path.startswith("/drinkerror"):
            response = layout.replace("%%layout_content%%", self.get_file("templates/drinkerror.html"))

        else:
            self.send_response(301)
            self.send_header("Location", "/home")
            self.end_headers()
            return
        # response ="""
        # <script>
        #    document.write(window.screen.availHeight+" "+window.screen.availWidth);
        # </script>"""



        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.end_headers()
        self.wfile.write(bytes(str(response), "utf-8"))
