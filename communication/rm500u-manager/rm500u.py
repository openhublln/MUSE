import re
import time


class SignalStrengthResponse:
    def __init__(self, response):
        self.raw_response = response
        self.__parse_response(response)

    def __parse_response(self, response):
        parameters = re.findall(r"\+CSQ: (\d+),(\d+)", response)
        self.raw_rssi = int(parameters[0][0])
        self.raw_ber = int(parameters[0][1])

        if self.raw_rssi == 99:
            self.rssi = "No signal"
        elif self.raw_rssi == 0:
            self.rssi = "<= -113 dBm"
        elif self.raw_rssi == 1:
            self.rssi = "-111 dBm"
        elif self.raw_rssi > 1 and self.raw_rssi < 31:
            self.rssi = f"{-113 + 2 * self.raw_rssi} dBm"
        elif self.raw_rssi == 31:
            self.rssi = ">= -51 dBm"

        if self.raw_ber == 0:
            self.ber = "0.14%"
        elif self.raw_ber == 1:
            self.ber = "0.28%"
        elif self.raw_ber == 2:
            self.ber = "0.57%"
        elif self.raw_ber == 3:
            self.ber = "1.13%"
        elif self.raw_ber == 4:
            self.ber = "2.26%"
        elif self.raw_ber == 5:
            self.ber = "4.53%"
        elif self.raw_ber == 6:
            self.ber = "9.05%"
        elif self.raw_ber == 7:
            self.ber = "18.10%"
        if self.raw_ber == 99:
            self.ber = "No signal"

    def __str__(self):
        return str(self.__dict__)


def request_signal_strength(serial):
    serial.write(b"AT+CSQ\r\n")
    time.sleep(0.3)
    response = serial.read(64).decode("utf-8")
    return SignalStrengthResponse(response)


def request_temperatures(serial):
    serial.write(b"AT+QTEMP\r\n")
    time.sleep(0.3)
    response = serial.read(160).decode("utf-8")
    # use regex to extract the temperatures
    temperatures = re.findall(r'\+QTEMP: "(\w+-\w+)","(\d+)"', response)
    response = {}
    for temperature in temperatures:
        response[temperature[0]] = temperature[1]
    return response


class ServingCellResponse:
    def __init__(self, response):
        self.raw_response = response
        self.__parse_response(response)

    def __parse_response(self, response):
        parameters = re.findall(r'\+QENG: "servingcell",(.+)', response)
        parameters = parameters[0].replace('"', "").replace("\r", "").split(",")
        self.state = parameters[0]

        if self.state != "SEARCH":
            self.mode = parameters[1]
            if self.mode == "NR5G-SA" or self.mode == "NR5G-NSA":
                self.__parse_NR(parameters[2:])
            if self.mode == "LTE":
                self.__parse_LTE(parameters[2:])
            if self.mode == "WCDMA":
                self.__parse_WCDMA(parameters[2:])

    def __parse_NR(self, response):
        self.duplex_mode = response[0]
        self.MCC = response[1]
        self.MNC = response[2]
        self.cellID = response[3]
        self.PCID = response[4]
        self.TAC = response[5]
        self.ARFCN = response[6]
        self.band = response[7]
        self.NR_DL_bandwidth = response[8]
        self.RSRP = response[9]
        self.RSRQ = response[10]
        self.SINR = response[11]
        self.TX_power = response[12]
        self.srxlev = response[13]
        self.SCS = response[14]

    def __parse_LTE(self, response):
        self.is_tdd = response[0]
        self.MCC = response[1]
        self.MNC = response[2]
        self.cellID = response[3]
        self.PCID = response[4]
        self.EARFCN = response[5]
        self.freq_band_ind = response[6]
        self.UL_bandwidth = response[7]
        self.DL_bandwidth = response[8]
        self.TAC = response[9]
        self.RSRP = response[10]
        self.RSRQ = response[11]
        self.RSSI = response[12]
        self.SINR = response[13]
        self.CQI = response[14]
        self.TX_power = response[15]
        self.srxlev = response[16]

    def __parse_WCDMA(self, response):
        self.MCC = response[0]
        self.MNC = response[1]
        self.LAC = response[2]
        self.cellID = response[3]
        self.UARFCN = response[4]
        self.RAC = response[5]
        self.RSCP = response[6]
        self.ecno = response[7]
        self.phych = response[8]
        self.SF = response[9]
        self.slot = response[10]

    def __str__(self):
        return str(self.__dict__)


def request_servingcell(serial):
    serial.write(b'AT+QENG="servingcell"\r\n')
    time.sleep(0.3)
    response = serial.read(160).decode("utf-8")
    return ServingCellResponse(response)


class UsbnetEthernetStatusResponse:
    def __init__(self, response):
        self.raw_response = response
        if not "ERROR" in self.raw_response:
            self.__parse_response(response)

    def __parse_response(self, response):
        parameters = re.findall(r"\+QNETDEVSTATUS: (.+)", response)
        parameters = parameters[0].replace('"', "").replace("\r", "").split(",")

        self.clIPv4 = parameters[0]
        self.IPv4_netmask = parameters[1]
        self.IPv4_gate = parameters[2]
        self.IPv4_DHCP = parameters[3]
        self.IPv4_pDNS = parameters[4]
        self.IPv4_sDNS = parameters[5]
        self.clIPv6 = parameters[6]
        self.IPv6_netmask = parameters[7]
        self.IPv6_gate = parameters[8]
        self.IPv6_DHCP = parameters[9]
        self.IPv6_pDNS = parameters[10]
        self.IPv6_sDNS = parameters[11]

    def __str__(self):
        return str(self.__dict__)


def request_usbnet_ethernet_status(serial, cid):
    serial.write(f"AT+QNETDEVSTATUS={cid}\r\n".encode("utf-8"))
    time.sleep(0.3)
    response = serial.read(160).decode("utf-8")
    return UsbnetEthernetStatusResponse(response)


def request_data_counter(serial):
    serial.write(b"AT+QGDCNT?\r\n")
    time.sleep(0.3)
    response = serial.read(160).decode("utf-8")
    counter = re.findall(r'\+QGDCNT: (\d+),(\d+)', response)
    return counter[0]


def reset_data_counter(serial):
    serial.write(b"AT+QGDCNT=0\r\n")
    time.sleep(0.3)
    response = serial.read(160).decode("utf-8")
    print(response)


def reset_all_bands(serial):
    serial.write(b'AT+QNWPREFCFG="all_band_reset"')
    time.sleep(3)
    response = serial.read(160).decode("utf-8")
    print(response)
