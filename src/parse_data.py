

import csv
import pint
from enum import Enum
from dataclasses import dataclass, field

# CSV line format
# t_rpm, RPM, t_speed, speed, t_maf, maf, t_tps, tps, t_eload, eload, t_ctemp, ctemp, t_sftrim, sftrim, t_lftrim, lftrim, t_tadv, tadv, t_intmp, intmp

# Units
# RPM:          revs/minute
# Speed:        KPH
# MAF:          grams/sec
# TPS:          percent
# Engine Load:  percent
# Coolant temp: celsius
# S Fuel trim:  percent
# L Fuel trim:  percent
# Timing Adv:   degrees
# Intake temp:  celsius

class SensorType(Enum):
    RPM     = 0
    SPEED   = 1
    MAF     = 2
    TPS     = 3
    ELOAD   = 4
    CTEMP   = 5
    SFTRIM  = 6
    LFTRIM  = 7
    TIMADV  = 8
    ITEMP   = 9

SENSOR_MAP = {
    SensorType.RPM      : pint.Unit("rpm"),
    SensorType.SPEED    : pint.Unit("kph"),
    SensorType.MAF      : pint.Unit("gram/second"),
    SensorType.TPS      : pint.Unit("percent"),
    SensorType.ELOAD    : pint.Unit("percent"),
    SensorType.CTEMP    : pint.Unit("celsius"),
    SensorType.SFTRIM   : pint.Unit("percent"),
    SensorType.LFTRIM   : pint.Unit("percent"),
    SensorType.TIMADV   : pint.Unit("degrees"),
    SensorType.ITEMP    : pint.Unit("celsius")
}

KNOWN_COOLANT_OPERATNG_TEMP_L = 81
KNOWN_COOLANT_OPERATNG_TEMP_U = 87


@dataclass(frozen=True)
class SensorReading:
    type:   SensorType
    time:   float
    value:  pint.Quantity


def parse_row(row: list):
    time_and_reading = list(zip(row[::2], row[1::2]))
    parsed = []
    for sensor in SensorType:
        t = time_and_reading[sensor.value][0]
        sensor_reading = pint.Quantity(
                                    float(time_and_reading[sensor.value][1]),
                                    SENSOR_MAP[sensor]
        )
        parsed.append(SensorReading(
                        sensor.value,
                        float(t),
                        sensor_reading
                )
        )
    return parsed


# Load data from CSV
if __name__ == "__main__":
    import sys
    import pandas as pd
    import plotly.express as px
    from pathlib import Path
    if len(sys.argv) < 2:
        raise RuntimeError(f"Provide an argument for the CSV file to be read: python {__file__} <csv file path>")
    elif len(sys.argv) == 2:
        CSV_FILE = Path(sys.argv[-1])
    elif sys.argv[0] == "-c" and len(sys.argv) < 3:
        raise RuntimeError(f"Provide an argument for the CSV file to be read: python -c {__file__} <csv file path>")
    else:
        CSV_FILE = Path(sys.argv[2])

    sensor_data = []

    if not CSV_FILE.is_file():
        raise RuntimeError(f"File '{str(CSV_FILE)}' is not a file")

    with CSV_FILE.open("r", newline="") as logfile:
        reader = csv.reader(logfile, delimiter=",")
        for row in reader:
            sensor_data.append(parse_row(row))

    rpm_starttime = sensor_data[0][0].time
    rpm_dataframe = pd.DataFrame({
            "time": [reading[0].time - rpm_starttime for reading in sensor_data],
            "rpm":  [reading[0].value.magnitude for reading in sensor_data]
    })
    speed_starttime = sensor_data[0][0].time
    speed_dataframe = pd.DataFrame({
            "time": [reading[1].time - speed_starttime for reading in sensor_data],
            "speed": [reading[1].value.magnitude for reading in sensor_data]
    })

    series = [
        (rpm_dataframe, "rpm"),
        (speed_dataframe, "speed")
    ]

    import plotly.graph_objects as go
    #fig = px.line(rpm_dataframe, x="time", y="rpm")
    #fig.update_traces(type="scatter", line_shape="spline")
    fig = go.Figure()
    for df, y_col in series:
        fig.add_trace(go.Scatter(
            x=df["time"],
            y=df[y_col],
            mode="lines+markers",
            line_shape="spline",
            line_smoothing=1.3
        ))
    fig.update_layout(
        hovermode="x unified"
    )

    fig.show()
    

