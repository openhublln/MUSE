from datetime import datetime
import logging
import struct
import time
import h5py
from typing import Iterator, List, Optional, Tuple

import numpy as np
import serial

logger = logging.getLogger("kmd7")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class KMD7Exception(RuntimeError):
    pass

class KMD7:
    DEFAULT_BAUD = 115200
    HEADER_SIZE = 4
    LENGTH_SIZE = 4

    def __init__(self, port: str, baud: int = DEFAULT_BAUD, timeout: float = 1.0):
        """
        :param port: serial port, e.g. '/dev/ttyUSB0' or 'COM3'
        :param baud: initial baud used to open port (radar starts at 115200 by default)
        :param timeout: serial read timeout in seconds
        """
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.ser: Optional[serial.Serial] = None
        self.stop_streaming = False

    def open(self):
        logger.info("Opening serial port %s @ %d", self.port, self.baud)
        self.ser = serial.Serial(
            port=self.port,
            baudrate=self.baud,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_EVEN,
            stopbits=serial.STOPBITS_ONE,
            timeout=self.timeout,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False,
        )
        # flush input/output
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()

    def close(self):
        if self.ser and self.ser.is_open:
            # Necessary to revert baud to default before closing, because when reopened, the radar expects 115200
            if self.baud != self.DEFAULT_BAUD:
                logger.info("Reverting baud to default %d before closing", self.DEFAULT_BAUD)
                self.send_packet("INIT", struct.pack("B", 0))
                time.sleep(0.1)
            try:
                self.ser.close()
                logger.info("Closing serial port %s", self.port)
            except Exception as e:
                logger.warning("Exception while closing serial: %s", e)
        self.ser = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    # --------------------
    # Low level helpers
    # --------------------
    def _read_exact(self, n: int) -> bytes:
        """Read exactly n bytes or raise on timeout/short read."""
        if self.ser is None:
            raise KMD7Exception("Serial port not open")
        data = bytearray()
        deadline = time.time() + self.timeout
        while len(data) < n:
            chunk = self.ser.read(n - len(data))
            if chunk:
                data.extend(chunk)
            else:
                # no data returned; check timeout
                if time.time() > deadline:
                    break
        if len(data) != n:
            raise KMD7Exception(f"Timeout or short read: expected {n} got {len(data)} bytes")
        return bytes(data)

    def send_packet(self, header: str, payload: bytes = b""):
        """
        Compose and send a packet: 4 ASCII header + uint32 Little Endian length + payload.
        """
        if self.ser is None:
            raise KMD7Exception("Serial port not open")
        if len(header) != 4:
            raise ValueError("Header must be 4 ASCII characters")
        packet = header.encode("ascii")
        packet += struct.pack("<I", len(payload))
        packet += payload
        logger.debug("TX %s len=%d", header, len(payload))
        self.ser.write(packet)
        self.ser.flush()

    def read_packet(self, expect_timeout: Optional[float] = None) -> Tuple[str, bytes]:
        """
        Read one packet from the K-MD7: header (4 ASCII), payload length (uint32 Little Endian), payload.
        Returns (header, payload_bytes).
        """
        if self.ser is None:
            raise KMD7Exception("Serial port not open")
        old_timeout = self.ser.timeout
        if expect_timeout is not None:
            self.ser.timeout = expect_timeout

        try:
            hdr_bytes = self._read_exact(self.HEADER_SIZE)
            header = hdr_bytes.decode("ascii")
            len_bytes = self._read_exact(self.LENGTH_SIZE)
            payload_len = struct.unpack("<I", len_bytes)[0]
            payload = b""
            if payload_len > 0:
                payload = self._read_exact(payload_len)
            logger.debug("RX %s len=%d", header, payload_len)
            return header, payload
        finally:
            if expect_timeout is not None:
                self.ser.timeout = old_timeout

    # --------------------
    # High-level commands
    # --------------------
    def init(self, baud_setting_code: int = 0):
        """
        Send INIT command to start communication and optionally change baud.
        baud_setting_code: see datasheet: 0=115200,1=460800,2=921600,3=2000000,4=3000000
        After INIT is acknowledged with RESP and VERS, the module will change its baud to the chosen setting.
        IMPORTANT: if you pass a non-zero baud_setting_code, you must re-open the serial port at the new baud.
        """
        if not (0 <= baud_setting_code <= 4):
            raise ValueError("baud_setting_code must be 0..4")
        
        self.send_packet("INIT", struct.pack("B", baud_setting_code))
        h, p = self.read_packet()
        if h != "RESP":
            raise KMD7Exception(f"Expected RESP after INIT, got {h}")
        errcode = p[0] if p else None
        if errcode != 0:
            raise KMD7Exception(f"INIT RESP error code: {errcode}")

        h, p = self.read_packet()
        if h != "VERS":
            raise KMD7Exception(f"Expected VERS after INIT, got {h}")
        vers = p.rstrip(b"\x00").decode("ascii", errors="ignore")
        logger.info("Firmware VERS: %s", vers)

        # if different baud requested, map code to actual baud and reopen
        code_to_baud = {0: 115200, 1: 460800, 2: 921600, 3: 2000000, 4: 3000000}
        new_baud = code_to_baud.get(baud_setting_code, 115200)
        if new_baud != self.baud:
            logger.info("Reopening serial at new baud %d", new_baud)
            self.close()
            self.baud = new_baud
            time.sleep(0.05)
            self.open()

        return vers

    def goodbye(self):
        """Stop streaming and say goodbye."""
        for _ in range(3):
            try:
                self.ser.reset_input_buffer()
                self.send_packet("RDOT", struct.pack("B", 0))
                time.sleep(0.1)
            except Exception:
                pass
            
        time.sleep(0.2)
        for i in range(3):
            try:
                self.ser.reset_input_buffer()
                self.send_packet("GBYE", b"")
                h, p = self.read_packet(expect_timeout=0.5)
                if h == "RESP":
                    logger.info("GBYE acknowledged")
                    return p[0] if p else None
            except Exception as e:
                logger.warning("GBYE attempt %d failed: %s", i+1, e)
                time.sleep(0.2)
        
        logger.warning("Could not confirm GBYE response, forcing shutdown.")
        return None

    def enable_streaming(self, enable_mask: int):
        """
        RDOT with enable_mask bitfield as in datasheet:
        bits => [ .. DONE .. TDAT PDAT RFFT RADC ]
        Example: enable TDAT only: 0b00001000 (8)
        """
        self.send_packet("RDOT", struct.pack("B", enable_mask))
        h, p = self.read_packet()
        if h != "RESP":
            raise KMD7Exception("Expected RESP after RDOT")
        if p and p[0] != 0:
            raise KMD7Exception(f"RDOT RESP error: {p[0]}")
        logger.info("Streaming enabled (mask=%02x)", enable_mask)

    def disable_streaming(self):
        self.stop_streaming = True

    def stream_loop(self) -> Iterator[Tuple[str, bytes]]:
        """
        Generator that yields (header, payload) for incoming packets in streaming mode.
        Use `for header, payload in k.stream_loop(): ...`
        Note: this will block until a packet arrives or read times out and raise.
        """
        while not self.stop_streaming:
            try:
                h, p = self.read_packet()
                yield h, p
            except (KMD7Exception, serial.SerialException) as e:
                if self.stop_streaming:
                    logger.info("Streaming stopped gracefully")
                    break
                else:
                    raise
    
    def save_measurements(self, measurements: list, output_file:str):
        with h5py.File(output_file, 'a') as f:
            timestamp = datetime.now().isoformat()
            grp = f.create_group(timestamp)
            
            tdat_count = 0
            pdat_count = 0
            rfft_count = 0
            radc_count = 0  
            
            for data in measurements:
                target_grp = None
                if data["type"] == "tdat":
                    target_grp = grp.create_group(f"tdat_{tdat_count}")
                    target_grp.attrs["distance_m"] = data["distance_m"]
                    target_grp.attrs["speed_kmh"] = data["speed_kmh"]
                    target_grp.attrs["angle_deg"] = data["angle_deg"]
                    target_grp.attrs["magnitude_db"] = data["magnitude_db"]
                    target_grp.attrs["track_id"] = data["track_id"]
                    tdat_count += 1
                elif data["type"] == "pdat":
                    target_grp = grp.create_group(f"pdat_{pdat_count}")
                    target_grp.attrs["distance_m"] = data["distance_m"]
                    target_grp.attrs["speed_kmh"] = data["speed_kmh"]
                    target_grp.attrs["angle_deg"] = data["angle_deg"]
                    target_grp.attrs["magnitude_db"] = data["magnitude_db"]
                    pdat_count += 1
                elif data["type"] == "rfft":
                    target_grp = grp.create_group(f"rfft_{rfft_count}")
                    target_grp.create_dataset("spectrum_db", data=np.array(data["spectrum_db"]))
                    target_grp.create_dataset("threshold_db", data=np.array(data["threshold_db"]))
                    rfft_count += 1
                elif data["type"] == "radc":
                    target_grp = grp.create_group(f"radc_{radc_count}")
                    target_grp.create_dataset("if1_freq_a_i", data=np.array(data["if1_freq_a_i"]))
                    target_grp.create_dataset("if1_freq_a_q", data=np.array(data["if1_freq_a_q"]))
                    target_grp.create_dataset("if2_freq_a_i", data=np.array(data["if2_freq_a_i"]))
                    target_grp.create_dataset("if2_freq_a_q", data=np.array(data["if2_freq_a_q"]))
                    target_grp.create_dataset("if1_freq_b_i", data=np.array(data["if1_freq_b_i"]))
                    target_grp.create_dataset("if1_freq_b_q", data=np.array(data["if1_freq_b_q"]))
                    radc_count += 1
                target_grp.attrs["frame_number"] = data["frame_number"]

    # --------------------
    # Payload parsers
    # --------------------
    def parse_tdat_payload(self, payload: bytes) -> List[dict]:
        """
        TDAT: up to 8 targets, each 9 bytes:
        Distance [cm] UINT16
        Speed [km/h x100] INT16
        Angle [deg x100] INT16
        Magnitude [dB x100] UINT16
        Tracking channel ID UINT8
        """
        res = []
        rec_len = 9
        for offset in range(0, len(payload), rec_len):
            block = payload[offset:offset + rec_len]
            if len(block) < rec_len:
                break
            dist, spd, ang, mag, tid = struct.unpack("<Hh h H B", block)
            res.append({
                "type": "tdat",
                "distance_m": dist / 100.0,
                "speed_kmh": spd / 100.0,
                "angle_deg": ang / 100.0,
                "magnitude_db": mag / 100.0,
                "track_id": tid,
            })
        return res

    def parse_pdat_payload(self, payload: bytes) -> List[dict]:
        """
        PDAT: raw targets, up to 24 targets, 8 bytes each:
        Distance [cm] UINT16
        Speed [km/h x100] INT16
        Angle [deg x100] INT16
        Magnitude [dB x100] UINT16
        """
        res = []
        rec_len = 8
        for offset in range(0, len(payload), rec_len):
            block = payload[offset:offset + rec_len]
            if len(block) < rec_len:
                break
            dist, spd, ang, mag = struct.unpack("<Hh h H", block)
            res.append({
                "type": "pdat",
                "distance_m": dist / 100.0,
                "speed_kmh": spd / 100.0,
                "angle_deg": ang / 100.0,
                "magnitude_db": mag / 100.0,
            })
        return res

    def parse_rfft_payload(self, payload: bytes) -> dict:
        """
        RFFT: 2048 bytes: 512 spectrum points [dB x 100] UINT16 (1024 bytes)
               512 threshold points [dB x 100] UINT16 (1024 bytes)
        Returns dict with two lists (floats)
        """
        if len(payload) != 2048:
            raise KMD7Exception(f"Unexpected RFFT len {len(payload)} (expected 2048)")
        spec = struct.unpack("<512H", payload[:1024])
        thr = struct.unpack("<512H", payload[1024:])
        spec_db = [v / 100.0 for v in spec]
        thr_db = [v / 100.0 for v in thr]
        return [{"type": "rfft", "spectrum_db": spec_db, "threshold_db": thr_db}]

    def parse_radc_payload(self, payload: bytes) -> dict:
        """
        RADC: Raw ADC data from radar, 6144 bytes total
        - IF1 Frequency A: 1024 UINT16 values (2048 bytes)
        - IF2 Frequency A: 1024 UINT16 values (2048 bytes)
        - IF1 Frequency B: 1024 UINT16 values (2048 bytes)
        
        Returns dict with three tuples of raw ADC values.
        """
        if len(payload) != 6144:
            raise KMD7Exception(f"Unexpected RADC len {len(payload)} (expected 6144)")
        
        if1_freq_a_data = struct.unpack("<1024H", payload[0:2048])
        if1_freq_a_i = if1_freq_a_data[:512]
        if1_freq_a_q = if1_freq_a_data[512:]
        
        if2_freq_a_data = struct.unpack("<1024H", payload[2048:4096])
        if2_freq_a_i = if2_freq_a_data[:512]
        if2_freq_a_q = if2_freq_a_data[512:]
        
        if1_freq_b_data = struct.unpack("<1024H", payload[4096:6144])
        if1_freq_b_i = if1_freq_b_data[:512]
        if1_freq_b_q = if1_freq_b_data[512:]
        
        return [{
        "type": "radc",
        "if1_freq_a_i": if1_freq_a_i,
        "if1_freq_a_q": if1_freq_a_q,
        "if2_freq_a_i": if2_freq_a_i,
        "if2_freq_a_q": if2_freq_a_q,
        "if1_freq_b_i": if1_freq_b_i,
        "if1_freq_b_q": if1_freq_b_q,
        }]
        
    
    def parse_grps_parameters(self, payload: bytes) -> dict:
        """
        GRPS response parsing (if needed)
        """
        # Implementation depends on GRPS response structure
        if len(payload) != 31:
            raise KMD7Exception(f"Unexpected GRPS len {len(payload)} (expected 31)")
        
        fw_raw = payload[:19]
        fw_string = fw_raw.split(b"\x00", 1)[0].decode("ascii", errors="ignore")
        (
            freq_channel, 
            speed_setting, 
            range_setting,
            treshold_offset,
            tracking_filter,
            min_detection_zone_dist,
            max_detection_zone_dist,
            min_detection_zone_angle,
            max_detection_zone_angle,
            min_detection_speed_filter,
            max_detection_speed_filter,
            detection_direction_filter
        ) = struct.unpack("<BBBBBBBbbBBB", payload[19:31])
        
        return {
        "frequency_channel": freq_channel,
        "speed_setting": speed_setting,
        "range_setting": range_setting,
        "threshold_offset_db": treshold_offset,
        "tracking_filter": tracking_filter,
        "min_detection_distance_pct": min_detection_zone_dist,
        "max_detection_distance_pct": max_detection_zone_dist,
        "min_detection_angle_deg": min_detection_zone_angle,
        "max_detection_angle_deg": max_detection_zone_angle,
        "min_detection_speed_pct": min_detection_speed_filter,
        "max_detection_speed_pct": max_detection_speed_filter,
        "direction_filter": detection_direction_filter,
        "firmware_version": fw_string,
        }
    
    # Command setters
    def send_rspi_command(self, speed_setting: int):
        """
        Set speed setting :
        speed_setting = 0 -> 50 km/h
        speed_setting = 1 -> 100 km/h
        speed_setting = 2 -> 200 km/h
        """
        self.send_packet("RSPI", struct.pack("B", speed_setting))
        self.get_response("RSPI", speed_setting)
    
    def send_rbfr_command(self, freq_channel: int):
        """
        Set frequency channel to prevent interferences if multiple sensors are used in the same application.
        freq_channel = 0 -> Low
        freq_channel = 1 -> Medium
        freq_channel = 2 -> High
        """
        self.send_packet("RBFR", struct.pack("B", freq_channel))
        self.get_response("RBFR", freq_channel)
    
    def send_rrai_command(self, range_setting: int):
        """
        Set range setting: 
        range_setting = 0 -> 100 m
        range_setting = 1 -> 200 m
        range_setting = 2 -> 300 m
        """
        self.send_packet("RRAI", struct.pack("B", range_setting))
        self.get_response("RRAI", range_setting)
    
    def send_thof_command(self, threshold_offset: int):
        """
        Change threshold offset: 0-60dB
        """
        self.send_packet("THOF", struct.pack("B", threshold_offset))
        self.get_response("THOF", threshold_offset)
        
    def send_trft_command(self, tracking_filter_type: int):
        """
        Set tracking filter type: 
        tracking_filter_type = 0 -> Standard
        tracking_filter_type = 1 -> Fast detection
        tracking_filter_type = 2 -> Long visibility
        """
        self.send_packet("TRFT", struct.pack("B", tracking_filter_type))
        self.get_response("TRFT", tracking_filter_type)
    
    def send_mira_command(self, min_distance: int):
        """
        Change minimum detection zone distance 0-100% of range setting
        """
        self.send_packet("MIRA", struct.pack("B", min_distance))
        self.get_response("MIRA", min_distance)
    
    def send_mara_command(self, max_distance: int):
        """
        Change maximum detection zone distance 0-100% of range setting
        """
        self.send_packet("MARA", struct.pack("B", max_distance))
        self.get_response("MARA", max_distance)
    
    def send_mian_command(self, min_angle: int):
        """
        Change minimum detection zone angle -30 to +30 degrees
        """
        self.send_packet("MIAN", struct.pack("b", min_angle))
        self.get_response("MIAN", min_angle)
    
    def send_maan_command(self, max_angle: int):
        """
        Change maximum detection zone angle -30 to +30 degrees
        """
        self.send_packet("MAAN", struct.pack("b", max_angle))
        self.get_response("MAAN", max_angle)
    
    def send_misp_command(self, min_speed: int):
        """
        Set minimum detection speed filter 0-100% of speed setting
        """
        self.send_packet("MISP", struct.pack("B", min_speed))
        self.get_response("MISP", min_speed)
    
    def send_masp_command(self, max_speed: int):
        """
        Set maximum detection speed filter 0-100% of speed setting
        """
        self.send_packet("MASP", struct.pack("B", max_speed))
        self.get_response("MASP", max_speed)
        
    def send_dedi_command(self, direction_filter: int):
        """
        Change detection direction filter:
        0 -> Receding 
        1 -> Approaching
        2 -> Both
        """
        self.send_packet("DEDI", struct.pack("B", direction_filter))
        self.get_response("DEDI", direction_filter)
        
        
    def get_response(self, command, value):
        h, p = self.read_packet()
        if h != "RESP":
            raise KMD7Exception(f"Expected RESP after {command}")
        if p and p[0] != 0:
            raise KMD7Exception(f"{command} RESP error: {p[0]}")
        logger.info(f"{command} command %d sent successfully", value)
        
    def signal_handler(self, sig, frame):
        self.disable_streaming()
        logger.info("Stopped streaming. Sending GBYE and closing.")
        self.goodbye()