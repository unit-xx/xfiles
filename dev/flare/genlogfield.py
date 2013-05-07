import UserApiStruct as ustruct

candidates = [ustruct.CThostFtdcInputOrderField, 
        ustruct.CThostFtdcOrderField,
        ustruct.CThostFtdcTradeField,
        ustruct.CThostFtdcOrderActionField
        ]

lf = []
for c in candidates:
    lf.extend(c().__dict__.keys())

lf = list(set(lf))
lf.sort()
for f in lf:
    print "'"+f+"'"
