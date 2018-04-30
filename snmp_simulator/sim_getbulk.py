from pysnmp.hlapi import *

for (errorIndication,
     errorStatus,
     errorIndex,
     varBinds) in bulkCmd(SnmpEngine(),
        CommunityData('pppp'),
        UdpTransportTarget(('10.0.0.254', 161)),
        ContextData(),
        0, 25,  # fetch up to 25 OIDs one-shot
        ObjectType(ObjectIdentity('1.0.8802.1.1.2.1.3.7.1.4')),
        lookupMib=False,
        lexicographicMode=False):
    if errorIndication or errorStatus:
        print(errorIndication or errorStatus)
        break
    elif errorStatus:
        print('%s at %s' % (errorStatus.prettyPrint(),
                            errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
        break
    else:
        for varBind in varBinds:
            print(' = '.join([x.prettyPrint() for x in varBind]))