import enum
from functools import cached_property
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



class GaugeID(int, enum.Enum):

    TPR = b"TPR"
    """Pirani Gauge or Pirani Capacitive gauge"""

    IK9 = b"IK9"
    """Cold Cathode Gauge 10^-9"""

    IKR11 = b"IKR11"
    """Cold Cathode Gauge 10^-11"""

    PKR = b"PKR"
    """FullRange CC Gauge"""

    PBR = b"PBR"
    """FullRange BA Gauge"""

    IMR = b"IMR"
    """Pirani / High Pressure Gauge"""

    CMR = b"CMR"
    """Linear gauge"""

    NO_SENSOR = b"noSEn"
    """"No sensor"""

    NO_IDENTIFIER = b"noid"
    """No identifier"""


def _search_gauge_id(value: bytes) -> t.Optional[GaugeID]:
    for gauge_id in GaugeID:
        if gauge_id == value:
            return gauge_id
    return None


class GaugeType(bytes, enum.Enum):

    GAUGE1 = b"0"
    GAUGE2 = b"1"


class ErrorStatus(bytes, enum.Enum):

    NO_ERROR = b"0000"
    ERROR = b"0000"
    NO_HARDWARE = b"0100"
    INADMISSIBLE_PARAMETER = b"0010"
    SYNTAX_ERROR = b"0001"


def _search_error_status(value: bytes) -> t.Optional[ErrorStatus]:
    for status in ErrorStatus:
        if status == value:
            return status
    return None


class ResetErrorStatus(bytes, enum.Enum):

    NO_ERROR = b"0"
    WATCHDOG_RESPONDED = b"1"
    TASK_FAILED = b"2"
    EPROM_ERROR = b"3"
    RAM_ERROR = b"4"
    EEPROM_ERROR = b"5"
    DISPLAY_ERROR = b"6"
    AD_CONVERTER_ERROR = b"7"
    GAUGE1_ERROR = b"9"
    GAUGE1_IDENTIFICATION_ERROR = b"10"
    GAUGE2_ERROR = b"11"
    GAUGE2_IDENTIFICATION_ERROR = b"12"


def _search_reset_error_status(value: bytes) -> ResetErrorStatus:
    for status in ResetErrorStatus:
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

    def enquiry(self) -> None:
        self._serial.write(self.ENQUIRY)

    def readline(self) -> bytes:
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

    def send_command(self, mnemonic: Mnemonics, *args: bytes) -> None:
        self._write(mnemonic.value, *args)
        ack = self.readline()
        self._handle_ack(ack, mnemonic)

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
        self.send_command(mnemonic)
        self.enquiry()
        data = self.readline()
        return self._parse_measurement(data)

    def read_gauge1(self) -> t.Tuple[MeasurementStatus, float]:
        return self._read_gauge(Mnemonics.PR1)

    def read_gauge2(self) -> t.Tuple[MeasurementStatus, float]:
        return self._read_gauge(Mnemonics.PR2)

    def read_both(self) -> None:
        self.send_command(Mnemonics.PRX)
        self.enquiry()
        data = self.readline()
        return self._parse_measurements(data)

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

        self.send_command(Mnemonics.SEN, signal1, signal2)
        self.enquiry()
        data = self.readline()
        status1, status2 = data.split(b",")

        if (status1 != signal1) or (status2 != signal2):
            raise IOError(
                "Gauges cannot be turned on or off.\n"
                f"Status: gauge 1 -> {status1}, gauge2 -> {status2}"
            )

    def turn_on_gauge1(self) -> None:
        self._turn_on_off(True, None)

    def turn_on_gauge2(self) -> None:
        self._turn_on_off(None, True)

    def turn_on_both(self) -> None:
        self._turn_on(True, True)

    def turn_off_gauge1(self) -> None:
        self._turn_off(False, None)

    def turn_off_gauge2(self) -> None:
        self._turn_off(None, False)

    def turn_off_both(self) -> None:
        self._turn_off(False, False)

    def _get_gauge_ids(self) -> t.Tuple[GaugeID, GaugeID]:
        self.send_command(Mnemonics.TID)
        self.enquiry()
        data = self.readline()
        id_gauge1, id_gauge2 = map(_search_gauge_id, data.split(b","))

        cls = type(self)
        cls.id_gauge1.func = lambda _: id_gauge1
        cls.id_gauge2.func = lambda _: id_gauge2

        return (id_gauge1, id_gauge2)

    @cached_property
    def id_gauge1(self) -> None:
        return self._get_gauge_ids()[0]

    @cached_property
    def id_gauge2(self) -> None:
        return self._get_gauge_ids()[1]

    def _change_channel(self, channel: GaugeType) -> GaugeType:
        if channel not in {b"0", b"1"}:
            raise ValueError(f"'channel' must be 0 or 1 as bytes.")

        self.send_command(Mnemonics.SCT, channel)
        self.enquiry()
        data = self.readline()
        return GaugeType.GAUGE1 if data == b"0" else GaugeType.GAUGE2

    def change_channel_1(self) -> None:
        channel = self._change_channel(GaugeType.GAUGE1)
        if channel != GaugeType.GAUGE1:
            raise IOError("Measurement channel wasn't changed appropriately.")

    def change_channel_2(self) -> None:
        chnnel = self._change_channel(GaugeType.GAUGE2)
        if chnnel != GaugeType.GAUGE2:
            raise IOError("Measurement channel wasn't changed appropriately.")

    def get_error_status(self) -> ErrorStatus:
        self.send_command(Mnemonics.ERR)
        self.enquiry()
        data = self.readline()
        status = _search_error_status(data)
        if status is not None:
            return status
        raise IOError(f"Unexpected binary was received: {data}")

    def reset(self) -> t.List[ResetErrorStatus]:
        self.send_command(Mnemonics.RES, b"1")
        self.enquiry()
        data = self.readline()
        return [_search_reset_error_status(s) for s in data.split(b",")]
