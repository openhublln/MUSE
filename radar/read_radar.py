import logging
import signal
import struct
import os
from datetime import datetime
from kdm7 import KMD7

logger = logging.getLogger("kmd7")

RADC_MASK = 0x01  
RFFT_MASK = 0x02  
PDAT_MASK = 0x04  
TDAT_MASK = 0x08 
DONE_MASK = 0x20

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="K-MD7 example")
    parser.add_argument("output_dir", type=str, help="Path to save measurements to HDF5 file")
    parser.add_argument("--port", required=True, help="Serial port (e.g. /dev/ttyUSB0 or COM3)")
    parser.add_argument("--baudcode", required=False, type=int, default=4, help="INIT baud code (0=115200)")
    args = parser.parse_args()
    
    with KMD7(args.port, baud=115200, timeout=5.0) as k:
        signal.signal(signal.SIGINT, k.signal_handler)
        vers = k.init(baud_setting_code=args.baudcode)
        logger.info("Module version: %s", vers)                
        
        # Set radar parameters
        k.send_rbfr_command(0)
        k.send_rspi_command(1)
        k.send_rrai_command(0)
        k.send_thof_command(12)
        k.send_trft_command(0)
        k.send_mira_command(5)
        k.send_mara_command(100)
        k.send_mian_command(-30)
        k.send_maan_command(30)
        k.send_misp_command(10)
        k.send_masp_command(100)
        k.send_dedi_command(2)
        k.send_packet("GRPS")    
                            
        
        mask =  TDAT_MASK | PDAT_MASK | RFFT_MASK | RADC_MASK | DONE_MASK
        k.enable_streaming(mask)
        frame_buffer = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        try :
            for header, payload in k.stream_loop():
                if header == "RPST":
                    params = k.parse_grps_parameters(payload)
                    print(params)  
                if header == "PDAT":
                    parsed = k.parse_pdat_payload(payload)
                    if parsed:
                        frame_buffer.extend(parsed)
                    logger.info("PDAT streaming: %s", parsed)
                if header == "TDAT":
                    parsed = k.parse_tdat_payload(payload)
                    if parsed:
                        frame_buffer.extend(parsed)
                    logger.info("TDAT streaming: %s", parsed)
                if header == "RFFT":
                    parsed = k.parse_rfft_payload(payload)
                    if parsed:
                        frame_buffer.extend(parsed)
                    #logger.info("RFFT streaming: %s", parsed)
                if header == "RADC":
                    parsed = k.parse_radc_payload(payload)
                    if parsed:
                        frame_buffer.extend(parsed)
                    #logger.info("RADC streaming: %s", parsed)
                if header == "DONE":
                    frame_num = struct.unpack("<I", payload)[0] if payload else None
                    for data in frame_buffer:
                        data['frame_number'] = frame_num
                    logger.info("DONE frame %s", frame_num)
                    if len(frame_buffer) > 0:
                        k.save_measurements(frame_buffer, os.path.join(args.output_dir, f"{timestamp}.hdf5"))
                    frame_buffer = []
                else:
                    logger.info("STREAM RX %s len=%d", header, len(payload) if payload else 0)
                
        except Exception as e:
            logger.error("Error during streaming: %s", e)
            k.disable_streaming()