import obd
import time
import csv
import math
import statistics
import pint
from collections import deque

DRIVE_FILE = "drive_" + str(int(time.time())) + ".csv"

obd_conn = obd.OBD("/dev/ttyUSB0", baudrate=115200)

class Mag:
    def __init__(self, mag):
        self.magnitude = mag
class Coolant:
    def __init__(self, value: Mag):
        self.value = value
        self.time = time.time()


COOLANT_OP_TEMP_L = 82.0
COOLANT_OP_TEMP_U = 87.0
COOLANT_WINDOW_SZ = 25
COOLANT_POLL_DELAY = 30
g_coolant_poll_delay_ct = COOLANT_POLL_DELAY
g_coolant_window = deque(maxlen=COOLANT_WINDOW_SZ)
g_coolant_at_op_temp = False

INTAKE_POLL_DELAY = 40
INTAKE_WINDOW_SZ = 30
g_intake_window = deque(maxlen=INTAKE_WINDOW_SZ)
g_intake_poll_delay_ct = INTAKE_POLL_DELAY

g_ureg = pint.UnitRegistry()

def get_coolant_temp():
    global g_coolant_poll_delay_ct
    global g_coolant_window
    global obd_conn
    global g_ureg
    global g_coolant_at_op_temp
    global obd_conn


    if len(g_coolant_window) < 1:
        coolant_temp = obd_conn.query(obd.commands.COOLANT_TEMP)
        g_coolant_window.append(coolant_temp.value.magnitude)
        return coolant_temp

    # if the last poll was outside of the known operating range,
    # then keep polling it until it gets within the operating range
    if g_coolant_window[-1] < COOLANT_OP_TEMP_L or g_coolant_window[-1] > COOLANT_OP_TEMP_U:
        g_coolant_at_op_temp = False
        coolant_temp = obd_conn.query(obd.commands.COOLANT_TEMP)
        g_coolant_window.append(coolant_temp.value.magnitude)
        return coolant_temp

    g_coolant_at_op_temp = True
    if g_coolant_poll_delay_ct > 0:
        g_coolant_poll_delay_ct -= 1
        r = obd.OBDResponse(obd.commands.COOLANT_TEMP)
        r.value = pint.Quantity(g_coolant_window[-1], g_ureg.celsius)
        return r
    else:
        g_coolant_poll_delay_ct = COOLANT_POLL_DELAY
        coolant_temp = obd_conn.query(obd.commands.COOLANT_TEMP)
        g_coolant_window.append(coolant_temp.value.magnitude)
        return coolant_temp
    

def get_intake_temp():
    global g_coolant_at_op_temp
    global g_intake_window
    global g_intake_poll_delay_ct
    global obd_conn

    if len(g_intake_window) < 1:
        g_intake_window.append(obd_conn.query(obd.commands.INTAKE_TEMP))
        return g_intake_window[-1]

    if not g_coolant_at_op_temp:
        g_intake_window.append(obd_conn.query(obd.commands.INTAKE_TEMP))
        return g_intake_window[-1]
    
    if g_intake_poll_delay_ct > 0:
        g_intake_poll_delay_ct -= 1
        r = obd.OBDResponse(obd.commands.INTAKE_TEMP)
        r.value = g_intake_window[-1].value
        return r
    else:
        g_intake_poll_delay_ct = INTAKE_POLL_DELAY
        g_intake_window.append(obd_conn.query(obd.commands.INTAKE_TEMP))
        return g_intake_window[-1]

    


with open(DRIVE_FILE, 'w', newline='') as outfile:
    writer = csv.writer(outfile, delimiter=',',)
    coolant_window = []
    max_coolant_window_sz = 30
    coolant_tol = 0.03
    poll_coolant = True
    while True:
        t0 = time.time()
        RPM = obd_conn.query(obd.commands.RPM)
        speed = obd_conn.query(obd.commands.SPEED)
        maf = obd_conn.query(obd.commands.MAF)
        throttle_pos = obd_conn.query(obd.commands.THROTTLE_POS)
        engine_load = obd_conn.query(obd.commands.ENGINE_LOAD)
        coolant_temp = get_coolant_temp()
        s_fuel_trim = obd_conn.query(obd.commands.SHORT_FUEL_TRIM_1)
        l_fuel_trim = obd_conn.query(obd.commands.LONG_FUEL_TRIM_1)
        timing_advance = obd_conn.query(obd.commands.TIMING_ADVANCE)
        intake_temp = get_intake_temp()

        data = [RPM.time, RPM.value.magnitude,
                speed.time, speed.value.magnitude,
                maf.time, maf.value.magnitude,
                throttle_pos.time, throttle_pos.value.magnitude,
                engine_load.time, engine_load.value.magnitude,
                coolant_temp.time, coolant_temp.value.magnitude,
                s_fuel_trim.time, s_fuel_trim.value.magnitude,
                l_fuel_trim.time, l_fuel_trim.value.magnitude,
                timing_advance.time, timing_advance.value.magnitude,
                intake_temp.time, intake_temp.value.magnitude
        ]
        print(data)
        writer.writerow(data)
