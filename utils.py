
import os
import math
import wave
import struct

def db_to_float(db, using_amplitude=True):
    return 10 ** (db / 20.0) if using_amplitude else 10 ** (db / 10.0)

def ratio_to_db(ratio, using_amplitude=True):
    return 20 * math.log10(ratio) if using_amplitude else 10 * math.log10(ratio)
