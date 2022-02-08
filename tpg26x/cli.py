import os
import sys
import time

import click

from .tpg26x import (
    MeasurementStatus,
    Tpg26x,
)


@click.command()
@click.argument("port")
@click.option(
    "--interval",
    "-i",
    default=0.5,
    type=float,
)
@click.option(
    "--output",
    "-o",
    default="-",
)
def main(
    port: str,
    interval: float = 0.5,
    output: str = "-",
) -> None:
    tpg26x = Tpg26x(port)

    if output == "-":
        stream = sys.stdout
    else:
        stream = open(output, "wt", newline="")
    stream.writeline = lambda s: stream.write(f"{s}{os.linesep}")

    try:
        while True:
            status, pressure = tpg26x.read_gauge1()
            time_measured = time.time()

            if status == MeasurementStatus.OK:
                stream.writeline(
                    f"Time: {time_measured}, Pressure: {pressure} mbar"
                )
            else:
                stream.writeline(f"Measurement failed. status: {status.value}")

            time.sleep(interval)
    except KeyboardInterrupt:
        pass
    finally:
        stream.flush()
        stream.close()
