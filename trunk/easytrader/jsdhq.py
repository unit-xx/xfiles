import sys
from ctypes import *

MAX_QUOTA_STATUS_LEN = 2
MAX_DATE_LEN = 9
MAX_EXCHCODE_LEN = 6
MAX_VARI_LEN = 32
MAX_HQTYPE_LEN = 2

class KSFT_QUOTA_PUBDATA_ITEM(Structure):
    _pack_ = 4
    _fields_ = [
            ("contract_id", c_int),
            ("upd_serial", c_int),
            ("upd_date", c_int),
            ("pre_upd_date", c_int),
            ("pre_upd_serial", c_int),
            ("sys_recv_time", c_char * MAX_DATE_LEN),

            ("exchCode", c_char * MAX_EXCHCODE_LEN),
            ("varity_code", c_char * MAX_VARI_LEN),
            ("deliv_date", c_char * MAX_DATE_LEN),
            ("chgStatus", c_char * MAX_QUOTA_STATUS_LEN),

            ("openPrice", c_double),
            ("lastPrice", c_double),
            ("hightestPrice", c_double),
            ("lowestPrice", c_double),
            ("doneVolume", c_int),
            ("chgPrice", c_double),
            ("upperLimitPrice", c_double),
            ("lowerLimitPrice", c_double),
            ("hisHighestPrice", c_double),
            ("hisLowestPrice", c_double),
            ("openInterest", c_int),
            ("preSettlePrice", c_double),
            ("preClosePrice", c_double),
            ("settlePrice", c_double),
            ("turnover", c_double),
            ("preOpenInterest", c_int),
            ("closePrice", c_double),
            ("preDelta", c_double),
            ("currDelta", c_double),

            ("bidPrice1", c_double),
            ("bidVolume1", c_int),
            ("bidPrice2", c_double),
            ("bidVolume2", c_int),
            ("bidPrice3", c_double),
            ("bidVolume3", c_int),
            ("bidPrice4", c_double),
            ("bidVolume4", c_int),
            ("bidPrice5", c_double),
            ("bidVolume5", c_int),

            ("askPrice1", c_double),
            ("askVolume1", c_int),
            ("askPrice2", c_double),
            ("askVolume2", c_int),
            ("askPrice3", c_double),
            ("askVolume3", c_int),
            ("askPrice4", c_double),
            ("askVolume4", c_int),
            ("askPrice5", c_double),
            ("askVolume5", c_int),

            ("cmbtype", c_char * MAX_HQTYPE_LEN),
            ("derive_bidlot", c_int),
            ("derive_asklot", c_int)
            ]

def main(args):
    dll = WinDLL("KsFtQtPub.dll")
    prototype = WINFUNCTYPE(c_bool, c_ushort, c_char_p)
    KSFTHQPUB_Start = prototype(("KSFTHQPUB_Start", dll))

    prototype = WINFUNCTYPE(None)
    KSFTHQPUB_Stop = prototype(("KSFTHQPUB_Stop", dll))

    prototype = WINFUNCTYPE(c_int, c_char_p, c_int, c_int, c_char_p)
    KSFTHQPUB_GetQuota = prototype(("KSFTHQPUB_GetQuota", dll))

    errmsg = create_string_buffer(1024)
    ret = KSFTHQPUB_Start(20518, errmsg)
    if not ret:
        print "Error:", errmsg
        return

    timeout = 2000 # 2sec
    MAX_QUOTA_ITEM_COUNT = 50
    quotaData = (KSFT_QUOTA_PUBDATA_ITEM * MAX_QUOTA_ITEM_COUNT)()
    print type(quotaData)
    while 1:
        qcount = KSFTHQPUB_GetQuota(cast(quotaData, POINTER(KSFT_QUOTA_PUBDATA_ITEM)),
                sizeof(KSFT_QUOTA_PUBDATA_ITEM)*MAX_QUOTA_ITEM_COUNT,
                timeout,
                byref(errmsg))
        if qcount < 0:
            print errmsg
        elif qcount > 0:
            showquota(quotaData, qcount)
        else:
            print "no quota data"

    KSFTHQPUB_Stop()

if __name__ == "__main__":
    main(sys.argv)
