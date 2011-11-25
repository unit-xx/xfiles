import win32com.client
 
hs = win32com.client.Dispatch("HsCommX.Comm")
#hs.SetConnect()
#print 'connect', hs.Connect()
print 'create', hs.CreateX(123)
print 'connect', hs.ConnectX(1, '172.18.20.141', 7110, 0, '', 0)

# login test
hs.SetHead(0, 200)
hs.Setrange(7, 1)

hs.AddField('version')
hs.AddField('l_op_code')
hs.AddField('vc_op_password')
hs.AddField('op_entrust_way')
hs.AddField('op_station')
hs.AddField('account_content')
hs.AddField('password')

hs.AddValue('1')
hs.AddValue('8009')
hs.AddValue('0')
hs.AddValue('4')
hs.AddValue('00226814A2AB;172.30.4.98')
hs.AddValue('85001135')
hs.AddValue('121314')

print 'send', hs.Send()
print 'errorno', hs.ErrorNo
print 'errormsg', hs.ErrorMsg
print 'freepack', hs.freepack()
print 'recv', hs.Receive()
print 'errorno', hs.ErrorNo
print 'errormsg', hs.ErrorMsg
print 'Fieldcount', hs.Fieldcount

while 1:
    print 'eof', hs.Eof
    if hs.Eof != 0:
        break

    print 'error_no', hs.Fieldbyname('error_no')
    print 'error_info', hs.Fieldbyname('error_info')
    print hs.Fieldbyname('branch_no')
    print hs.Fieldbyname('fund_account')
    print hs.Fieldbyname('client_name')
    print hs.Fieldbyname('money_count')
    print hs.Fieldbyname('money_type')
    print hs.Fieldbyname('exchange_type')
    print hs.Fieldbyname('stock_account')
    print hs.Fieldbyname('client_rights')

    print 'fn', hs.GetFieldName(0)

    hs.Moveby(1)

print
print 'disconnect', hs.DisConnect()
