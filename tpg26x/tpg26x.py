import enum
import io
import typing as t

from serial import Serial


class Mnemonics(bytes, enum.Enum):

    ADC = b"ADC"
    """A/D converter test"""

    BAU = b"BAU"
    """Baud rate (transmission rate)"""

    COM = b"COM"
    """Continuous mode"""

    CAL = b"CAL"
    """Calibration factor"""

    DCD = b"DCD"
    """Display control digits (display resolution)"""

    DGS = b"DGS"
    """Degas"""

    DIC = b"DIC"
    """Display control (display changeover)"""

    DIS = b"DIS"
    """Display test"""

    EEP = b"EEP"
    """EEPROM test"""

    EPR = b"EPR"
    """Error status"""

    ERR = b"ERR"
    """Error status"""

    FIL = b"FIL"
    """Filter time constant (measurement value filter)"""

    FSR = b"FSR"
    """Full scale range (measurement range of linear gauges)"""

    IOT = b"IOT"
    """I/O test"""

    LOC = b"LOC"
    """Keylock"""

    OFC = b"OFC"
    """Offset correction (linear gauges)"""

    OFD = b"OFD"
    """Offset display (linear gauges)"""

    PNR = b"PNR"
    """Program number (firmware version)"""

    PR1 = b"PR1"
    """Pressure measurement (measurement data) gauge 1"""

    PR2 = b"PR2"
    """Pressure measurement (measurement data) gauge 2"""

    PRX = b"PRX"
    """Pressure measurement (measurement data) gauge 1 and 2"""

    PUC = b"PUC"
    """Penning underrange control (underrange control)"""

    RAM = b"RAM"
    """RAM test"""

    RES = b"RES"
    """Reset"""

    RST = b"RST"
    """RS232 test"""

    SAV = b"SAV"
    """Save parameters to EEPROM"""

    SC1 = b"SC1"
    """Sensor control 1 (gauge control 1)"""

    SC2 = b"SC2"
    """Sensor control 2 (gauge control 2)"""

    SCT = b"SCT"
    """Sensor channel change (measurement channel change)"""

    SEN = b"SEN"
    """Sensors on/off"""

    SP1 = b"SP1"
    """Setpoint 1 (switching function 1)"""

    SP2 = b"SP2"
    """Setpoint 2 (switching function 2)"""

    SP3 = b"SP3"
    """Setpoint 3 (switching function 3)"""

    SP4 = b"SP4"
    """Setpoint 4 (switching function 4)"""

    SPS = b"SPS"
    """Setpoint status (switching function status)"""

    TID = b"TID"
    """Transmitter identification (gauge identification)"""

    TKB = b"TKB"
    """Keyboard test (operator key test)"""

    TLC = b"TLC"
    """Torr lock"""

    UNI = b"UNI"
    """Pressure unit"""

    WDT = b"WDT"
    """Watchdog control"""


class MeasurementStatus(int, enum.Enum):

    OK = 0
    UNDERRANGE = 1
    OVERRANGE = 2
    SENSOR_ERROR = 3
    SENSOR_OFF = 4
    NO_SENSOR = 5
    IDENTIFICATION_ERROR = 6


def _search_measurement_status(value: int) -> t.Optional[MeasurementStatus]:
    for status in MeasurementStatus:
        if status == value:
            return status
    return None


class Tpg26x:

    END_OF_TEXT = b"\x03"
    CR = b"\x0D"
    LF = b"\x0A"
    ENQUIRY = b"\x05"
    ACK = b"\x06"
    NACK = b"\x15"

    NEWLINE = CR + LF

    def __init__(self, port: str, baudrate: int = 9600) -> None:
        self._serial = Serial(port=port, baudrate=baudrate)

        self._log_to: t.List[io.TextIOWrapper] = []

    def _close(self) -> None:
        self._serial.close()
        del self

    @classmethod
    def _format(cls, *args: bytes) -> bytes:
        return b",".join(args) + cls.CR + cls.LF

    def _write(self, *args: bytes) -> int:
        return self._serial.write(self._format(*args))

    def _enquiry(self) -> None:
        self._serial.write(self.ENQUIRY)

    def _readline(self) -> bytes:
        data = self._serial.readline()
        if data[-2:] == self.NEWLINE:
            return data[:-2]
        raise IOError(f"Unrecognizable data was received: {data}")

    @classmethod
    def _handle_ack(cls, data: bytes, mnemonic: Mnemonics) -> None:
        if data == cls.ACK:
            return
        elif data == cls.NACK:
            mnemonic = mnemonic.decode()
            raise IOError(f"Mnemonic {mnemonic} was forbiddened by the TPG26x.")
        else:
            raise IOError(f"Unexpected data was received: {data}")

    @staticmethod
    def _parse_pressure(raw: bytes) -> float:
        # NOTE
        #   check required
        mantissa, exponent = raw.split(b"E")
        mantissa = float(mantissa)
        exponent = int(exponent)
        return mantissa * 10**exponent

    @staticmethod
    def _parse_measurement(raw: bytes) -> t.Tuple[MeasurementStatus, float]:
        status, pressure = raw.split(b",")
        status = _search_measurement_status(int(status))
        pressure = Tpg26x._parse_pressure(pressure)
        return (status, pressure)

    @staticmethod
    def _parse_measurements(raw: bytes) -> t.Tuple[MeasurementStatus, float, float]:
        status, pressure1, pressure2 = raw.split(b",")
        status = _search_measurement_status(int(status))
        pressure1 = Tpg26x._parse_pressure(pressure1)
        pressure2 = Tpg26x._parse_pressure(pressure2)
        return (status, pressure1, pressure2)

    def _read_gauge(self, mnemonic: Mnemonics) -> t.Tuple[MeasurementStatus, float]:
        self._write(mnemonic)
        ack = self._readline()
        self._handle_ack(ack, mnemonic)
        self._enquiry()

        data = self._readline()
        return self._parse_measurement(data)

    def read_gauge1(self) -> t.Tuple[MeasurementStatus, float]:
        return self._read_gauge(Mnemonics.PR1)

    def read_gauge2(self) -> t.Tuple[MeasurementStatus, float]:
        return self._read_gauge(Mnemonics.PR2)

    def read_both(self) -> None:
        self._write(Mnemonics.PRX)
        ack = self._readline()
        self._handle_ack(ack, Mnemonics.PRX)
        self._enquiry()

        data = self._readline()
        return self._parse_measurements(data)

    def log(self) -> None:
        pass

    def _turn_on_off(
        self,
        gauge1: t.Optional[bool] = None,
        gauge2: t.Optional[bool] = None,
    ) -> None:
        if gauge1 is None:
            signal1 = b"0"
        elif gauge1:
            signal1 = b"1"
        else:
            signal1 = b"2"
        if gauge2 is None:
            signal2 = b"0"
        elif gauge2:
            signal2 = b"1"
        else:
            signal2 = b"2"

        self._write(Mnemonics.SEN, signal1, signal2)
        ack = self._readline()
        self._handle_ack(ack, Mnemonics.SEN)

        data = self._readline()
        status1, status2 = data.split(b",")
        if (status1 == signal1) and (status2 == signal2):
            return

        raise IOError(
            "Gauges cannot be turned on or off.\n"
            f"Status: gauge 1 -> {status1}, gauge2 -> {status2}"
        )

    def turn_on_gauge1(self) -> None:
        self._turn_on(True, False)

    def turn_on_gauge2(self) -> None:
        self._turn_on(False, True)

    def turn_on_both(self) -> None:
        self._turn_on(True, True)

    def _turn_off(self, gauge1: bool, gauge2: bool) -> None:
        if gauge1:
            signal1 = b"1"
        else:
            signal1 = b"0"
        if gauge2:
            signal2 = b"1"
        else:
            signal2 = b"0"

        self._write(Mnemonics.SEN, signal1, signal2)

    def turn_off_gauge1(self) -> None:
        self._turn_off(True, False)

    def turn_off_gauge2(self) -> None:
        self._turn_off(False, True)

    def turn_off_both(self) -> None:
        self._turn_off(True, True)
