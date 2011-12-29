import win32com.client

def dorecv(hs):
    fields=[]
    records=[]

    hs.freepack()
    ret = hs.Receive()
    if 0==ret:
        if 0==hs.errorno:
            for i in range(hs.Fieldcount):
                fields.append(hs.GetFieldName(i))

            while 1:
                if hs.Eof != 0:
                    break

                tmp = {}
                for f in fields:
                    tmp[f] = hs.Fieldbyname(f)
                records.append(tmp)
                hs.Moveby(1)
            return records
        else:
            return hs.errorno, hs.errormsg
    else:
        return hs.errorno, hs.errormsg

def dosend(hs, func, params):
    hs.SetHead(0, func)
    hs.SetRange(len(params), 1)

    for k in params:
        hs.AddField(k)

    for k in params:
        hs.AddValue(params[k])
    return hs.Send()

hs = win32com.client.Dispatch("HsCommX.Comm")
#hs.SetConnect()
#print 'connect', hs.Connect()
print 'create', hs.CreateX(123)
print 'connect', hs.ConnectX(1, '172.18.20.143', 7110, 0, '', 0)

# login test
loginparam = {
'version':'1',
'l_op_code':'8009',
'vc_op_password':'0',
'op_entrust_way':'4',
'project_id':'123321',
'op_station':'00226814A2AB;172.30.4.98',
'account_content':'85001135',
'password':'121314'
}

print dosend(hs, 200, loginparam)
print dorecv(hs)

# login test
loginparam = {
'l_op_code':'8009',
'vc_op_password':'0',
'vc_station_address':'00226814A2AB;172.30.4.98',
'vc_host_name':'gcn',
'l_action_in':'1'
}

print dosend(hs, 6200, loginparam)
print dorecv(hs)

# buy test
buyparam={
'version':'1',
'l_op_code':'8009',
'vc_op_password':'0',
'op_entrust_way':'4',
'op_station':'00226814A2AB;172.30.4.98',
'fund_account':'85001135',
'password':'121314',
'exchange_type':'1',
'stock_account':'',
'stock_code':'600000',
'entrust_amount':'100',
'entrust_price':'8.80',
'entrust_prop':'0',
'entrust_bs':'1',
'c_bs':''
        }

print dosend(hs, 302, buyparam)
print dorecv(hs)

print 'disconnect', hs.DisConnect()

# NOTE: buy, batchbuy, cancel, query orders
# marketinfo, secuinfo, login
# stockquote, capitalquery, stockquery

# NOTE: assumption: unspecified params can be send as empty string ''
# some field should be send, even it's empty, e.g. stock_account in 302
