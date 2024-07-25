'''
This file contains constants used in the read_radar.py script. All constants are
described in the K-MD2 datasheet or in A. Duflot TFE/ scripts.
'''

# list of commands for transmission with the radar
list_commands = {b"DONE" : "DONE", b"RADC": "RADC", b"RMRD": "RMRD", b"PDAT": "PDAT",\
                b"TDAT": "TDAT", b"RPRM": "RPRM", b"PPRM": "PPRM", b"GBYE": "GBYE"}

# list of init. commands
init_commands = (("INIT", 0, None),
                 ("DSF0", 4, 'RADC'),
                 ("DSF0", 4, 'RDBS'),
                 ("DSF0", 4, 'RDDA'),
                 ("DSF0", 4, 'PLEN'),
                 ("DSF0", 4, 'TLEN'),
                 ("DSF0", 4, 'RMRD'),
                 ("DSF0", 4, 'PDAT'),
                 ("DSF0", 4, 'RPRM'),
                 ("DSF0", 4, 'PPRM'),
                 ("DSF1", 4, 'RADC'),)

# detection of <nbr_letters> consecutive letters in <array> (starting at <offset>)
def detect_pattern(array, nbr_letters, offset=0):
    count = 0
    for i in range(offset, len(array)):
        if array[i] > 64 and array[i] < 91:
            count += 1
        else:
            count = 0

        if count == nbr_letters:
            return bytes(array[i-3:i+1]), i-3
    return None, -1
