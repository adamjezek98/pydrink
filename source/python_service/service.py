import web_server
import pydrink
import database
import threading
from inspect import currentframe, getframeinfo
import glob

def debug_print(arg):
    frameinfo = getframeinfo(currentframe())
    print(frameinfo.filename, ":", frameinfo.lineno, arg)


class PyDrinkService(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

        self.db = database.Database("database.db")

        self.ws = web_server.Webserver("0.0.0.0", 80, "database.db")
        self.pd = pydrink.PyDrink(glob.glob('/dev/ttyUSB*')[0])
        self.ws.server.RequestHandlerClass.pd = self.pd
        self.ws.server.RequestHandlerClass.pd.start()
        self.ws.start()
        debug_print("")


Pds = PyDrinkService()
