import threading, serial, time, logging
import database as rootdb
from inspect import currentframe, getframeinfo


def debug_print(arg):
    frameinfo = currentframe()
    print(frameinfo.f_back.f_lineno, ":", arg)


class PyDrink(threading.Thread):
    cart_position = 0
    states = {"OK": 1,
              "NOK": 2,
              "TARE_TIMOUT": 3,
              "DRINK_EMPTY": 4,
              }
    progress = 0
    progress_temp = 0
    progress_part = 0
    action = None
    params = None
    error_state = 0

    def __init__(self,port="COM5"):
        threading.Thread.__init__(self)
        self.serial_port = serial.Serial(port, 115200)
        self.ready = True

        self.logger = logging.getLogger('PyDrink')
        self.logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler('PyDrink.log')
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s|%(name)s|%(levelname)s|%(message)s')
        fh.setFormatter(formatter)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(formatter)

        self.logger.addHandler(ch)
        self.logger.addHandler(fh)

    def prepare_run(self, action, params):
        self.action = action
        self.params = params
        self.progress = 0

    def run(self):
        while 1:
            if (self.action == "makedrink"):
                self.make_drink(self.params)
            self.action = None
            time.sleep(0.5)

    def mainloop(self):
        pass

    def send_command(self, command):

        try:
            print("sending",command)
            self.flush_port()
            self.serial_port.write(bytes(command, "utf-8"))
            self.logger.info("Sent command " + command)
            return True
        except:
            self.logger.warning("Unable to send command " + command)
            return False

    def read_reply(self, timeout):
        start_time = time.time()
        while start_time + timeout > time.time():
            if self.serial_port.inWaiting():
                time.sleep(0.1)
                reply = str(self.serial_port.read(self.serial_port.inWaiting()), "utf-8").replace("\r\n", "")
                self.logger.info("reply " + reply)
                reply = reply.replace("DONEDONE", "DONE")
                return reply
        return False

    def flush_port(self):
        self.serial_port.flushOutput()
        self.serial_port.flushInput()

    def close_port(self):
        self.serial_port.close()

    def move_cart_to_pos(self, pos):

        self.logger.info("Moving cart to pos " + str(pos))
        dir = None
        if pos == "home":
            dir = "h"
            self.cart_position = 0
            pos = 0
        elif pos > self.cart_position:
            dir = "1"
        elif pos < self.cart_position:
            dir = "0"
        elif pos == self.cart_position:
            dir = "0"


        time.sleep(0.2)
        self.flush_port()
        command = "m" + dir + str(abs(self.cart_position - pos))
        while 1:
            self.send_command("m" + dir + str(abs(self.cart_position - pos)))
            rep = self.read_reply(2).replace("home","")
            self.logger.info("sending "+command+", received "+rep)
            if rep == command:
                break
        self.cart_position = pos
        res = self.read_reply(45)
        if res == "DONE":
            self.logger.info("Cart moved to " + str(pos))
            return True
        elif not res:
            self.logger.error("Cart not moved")
            return False
        elif "home" in res:
            self.cart_position = 0
            self.logger.warning("Cart moved to home")
            return True

    def get_weight(self):
        self.send_command("s")
        res = self.read_reply(1)
        if res:
            res = res.replace("DONE", "")
            self.logger.info("Scale measure " + str(res))
            try:
                return float(res)
            except:
                return False
        self.logger.error("Scale not responding")
        return False

    def tare_scale(self):
        self.send_command("st")
        res = self.read_reply(5)
        if res == "DONE":
            return True
        return False

    def pour_drink(self, tap, amount):
        db = rootdb.Database("database.db")
        _i = 1
        while not self.move_cart_to_pos(db.get_tap_pos(tap)):
            _i += 1
            if _i > 3:
                return self.states["NOK"]
        self.tare_scale()
        self.send_command("p" + str(tap - 1) + "1")
        self.read_reply(0.5)
        st = time.time()
        parts = 20
        while 1:
            w = self.get_weight()
            while w == False:
                w = self.get_weight()
            print(w)

            if w is False:
                self.send_command("pa")
                return self.states["TARE_TIMOUT"]
            if w >= amount:
                self.send_command("pa")
                return self.states["OK"]
            if st + 5 < time.time():
                self.send_command("pa")
                res = self.read_reply(1)
                return self.states["DRINK_EMPTY"]
            if  False: #w > parts:
                self.send_command("p" + str(tap - 1) + "0")
                self.read_reply(0.5)
                parts += 20
                time.sleep(2.5)
                st = time.time()
                self.send_command("p" + str(tap - 1) + "1")
                self.read_reply(0.5)
            #a = self.map(w, 0, amount, 0, self.progress_part)
            #self.progress = self.progress_temp + a
            #print(self.progress, "\t", self.progress_temp, "\t", a, "\t", self.progress_part)



    def make_drink(self, drink_id):
        self.tare_scale()
        db = rootdb.Database("database.db")
        db.c.execute("SELECT * FROM parts WHERE part_drink = ? ORDER BY part_order ASC", str(drink_id))
        parts = db.c.fetchall()
        self.progress_part = 100 / (len(parts) + 2)
        self.progress = 0
        self.progress_temp = 0
        self.move_cart_to_pos("home")
        self.progress += self.progress_part
        self.progress_temp += self.progress_part
        for part in parts:
            db.c.execute("SELECT tap_id FROM taps WHERE tap_liquid = ? AND tap_empty = 0 LIMIT 1", str(part[3]))
            tap = db.c.fetchone()[0]
            res = self.pour_drink(tap, part[4])
            if res != self.states["OK"]:
                self.error_state = res
                self.progress = -1
                return

            time.sleep(0.5)
            self.progress += self.progress_part
            self.progress_temp += self.progress_part
        time.sleep(1)
        print(self.serial_port.inWaiting())
        self.flush_port()
        print(self.serial_port.inWaiting())
        print("moving cart")
        self.move_cart_to_pos("home")
        print("cart moved")
        self.progress += self.progress_part
        self.progress = 100

    def map(self, x,  in_min,  in_max,  out_min,  out_max):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

