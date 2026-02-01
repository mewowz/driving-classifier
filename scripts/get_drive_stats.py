import obd
import time
import csv
import math
import statistics
import pint
from collections import deque

DRIVE_FILE = "drive_" + str(int(time.time())) + ".csv"


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

def parse_opts():
    import argparse
    from pathlib import Path
    global DRIVE_FILE
    parser = argparse.ArgumentParser(
            prog="Get OBDII PID values",
            description="Polls OBDII PIDs for an ELM327 OBDII scanner",
    )
    parser.add_argument(
            "-o", "--output-file", nargs=1,
    )

    args = parser.parse_args()
    if isinstance(args.output_file, str):
        p = Path(args.output_file)
        if p.exists():
            raise FileExistsError(f"Cannot create file '{str(p)}' - File Exists")
        try:
            p.touch()
        except PermissionError:
            # TODO: handle this error later
            raise

        DRIVE_FILE = p

def poll_obd(obd_conn):
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
    data = [
            RPM.time, RPM.value.magnitude,
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
    return data

# I'm considering making a pull request so that the OBD object
# can reconnect after it loses/can't get a connection
def connect(self, portstr=None, baudrate=None, protocol=None,
            check_voltage=True, start_low_power=False):
    # This needs some error checking to make sure that the object isn't already
    # connected to a device
    self.__connect(portstr, baudrate, protocol,
                   check_voltate, start_low_power)
    self.__load_commands()

obd.OBD.connect = connect

if __name__ == "__main__":
    parse_opts()
    obd_conn = obd.OBD("/dev/ttyUSB0", baudrate=115200) # TODO: add a cmdline option for the OBD device string & baudrate
    timeout = 1
    while not obd_conn.is_connected():
        print("Could not connect to OBD device. Sleeping...")
        time.sleep(timeout)
        obd_conn.connect("/dev/ttyUSB0", baudrate=115200)

    with open(DRIVE_FILE, 'w', newline='') as outfile:
        writer = csv.writer(outfile, delimiter=',',)
        while True:
            data = poll_obd(obd_conn)
            print(data)
            writer.writerow(data)
