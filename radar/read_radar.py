import logging
import signal
import struct
from kdm7 import KMD7

logger = logging.getLogger("kmd7")

RADC_MASK = 0x01  
RFFT_MASK = 0x02  
PDAT_MASK = 0x04  
TDAT_MASK = 0x08 
DONE_MASK = 0x40 

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="K-MD7 example")
    parser.add_argument("--port", required=True, help="Serial port (e.g. /dev/ttyUSB0 or COM3)")
    parser.add_argument("--baudcode", type=int, default=0, help="INIT baud code (0=115200)")
    args = parser.parse_args()
    
    with KMD7(args.port, baud=115200, timeout=5.0) as k:
        signal.signal(signal.SIGINT, k.signal_handler)
        vers = k.init(baud_setting_code=args.baudcode)
        logger.info("Module version: %s", vers)                
        
        # Set radar parameters
        k.send_rbfr_command(0)
        k.send_rspi_command(0)
        k.send_rrai_command(0)
        k.send_thof_command(12)
        k.send_trft_command(0)
        k.send_mira_command(40)
        k.send_mara_command(60)
        k.send_mian_command(-30)
        k.send_maan_command(30)
        k.send_misp_command(40)
        k.send_masp_command(60)
        k.send_dedi_command(2)
        k.send_packet("GRPS")    
                            
        
        mask = PDAT_MASK | DONE_MASK
        k.enable_streaming(mask)

        for header, payload in k.stream_loop():
            if header == "RPST":
                params = k._parse_grps_parameters(payload)
                print(params)  
            if header == "PDAT":
                parsed = k._parse_pdat_payload(payload)
                logger.info("PDAT streaming: %s", parsed)
            if header == "TDAT":
                parsed = k._parse_tdat_payload(payload)
                logger.info("TDAT streaming: %s", parsed)
            if header == "RFFT":
                parsed = k._parse_rfft_payload(payload)
                logger.info("RFFT streaming: %s", parsed)
            if header == "RADC":
                parsed = k._parse_radc_payload(payload)
                logger.info("RADC streaming: %s", parsed)
            elif header == "DONE":
                frame_num = struct.unpack("<I", payload)[0] if payload else None
                logger.debug("DONE frame %s", frame_num)
            else:
                logger.debug("STREAM RX %s len=%d", header, len(payload) if payload else 0)