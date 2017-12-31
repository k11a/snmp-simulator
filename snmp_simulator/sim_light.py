import logging
import re
import time

from pysnmp.entity import engine, config
from pysnmp.entity.rfc3413 import cmdrsp, context
from pysnmp.carrier.asynsock.dgram import udp
from pysnmp.proto.api import v2c
from pysnmp.proto import rfc1902


TYPE_MAP = {
    'STRING': v2c.OctetString,
    'INTEGER': v2c.Integer32,
    'IpAddress': v2c.IpAddress,
    'Timeticks': v2c.TimeTicks,
    'Counter32': v2c.Counter32,
    'Counter64': v2c.Counter64,
    'OID': v2c.ObjectIdentifier,
    'Gauge32': v2c.Gauge32,
    'Hex-STRING': v2c.OctetString,
    'Network Address': v2c.OctetString,
}


def createVariable(SuperClass, getValue, *args):
    class Var(SuperClass):
        def getValue(self, name, idx):
            oid_value, oid_type_str = getValue(name, idx)
            if oid_type_str == 'Hex-STRING':
                oid_value_kwarg = dict(hexValue=oid_value.replace(' ', ''))
            else:
                oid_value_kwarg = dict(value=oid_value)
            return self.getSyntax().clone(TYPE_MAP[oid_type_str](**oid_value_kwarg))
    return Var(*args)


class SNMPAgent(object):
    def __init__(self, host, port, rcommunity):
        self.snmpEngine = engine.SnmpEngine()
        config.addSocketTransport(self.snmpEngine, udp.domainName, udp.UdpTransport().openServerMode((host, port)))
        config.addV1System(self.snmpEngine, 'my-area', rcommunity)
        config.addVacmUser(self.snmpEngine, 2, 'my-area', 'noAuthNoPriv', (1, 3, 6) )
#        config.addV3User(self.snmpEngine, 'test')
#        config.addVacmUser(self.snmpEngine, 3, 'test', 'noAuthNoPriv', (1, 3, 6))
        self.snmpContext = context.SnmpContext(self.snmpEngine)
        self.mibBuilder = self.snmpContext.getMibInstrum().getMibBuilder()
        self.MibScalar, self.MibScalarInstance = self.mibBuilder.importSymbols('SNMPv2-SMI', 'MibScalar', 'MibScalarInstance')
        cmdrsp.GetCommandResponder(self.snmpEngine, self.snmpContext)
        cmdrsp.NextCommandResponder(self.snmpEngine, self.snmpContext)
        cmdrsp.BulkCommandResponder(self.snmpEngine, self.snmpContext)

    def add_oid(self, oid, oid_type_str, getValue):
        oid_num = rfc1902.ObjectName(oid).asTuple()
        oid_type = TYPE_MAP[oid_type_str]
        self.mibBuilder.exportSymbols(
            '__MY_MIB',
            self.MibScalar(oid_num[:-1], oid_type),
            createVariable(self.MibScalarInstance, getValue, oid_num[:-1], (oid_num[-1],), oid_type)
        )

    def serve_forever(self):
        self.snmpEngine.transportDispatcher.jobStarted(1)

        try:
            self.snmpEngine.transportDispatcher.runDispatcher()
        except KeyboardInterrupt:
            self.snmpEngine.transportDispatcher.closeDispatcher()


class Simulator(object):
    def __init__(self, host, port, rcommunity):
        self.start_time = time.time()
        self.oid_dict = {}
        self.snmp_agent = SNMPAgent(host=host, port=port, rcommunity=rcommunity)

    def add_walkfile(self, path):
        log.info('loading SNMP walk file {}'.format(path))
        with open(path) as f:
            try:
                file_text = f.read()
            except:
                log.exception('Failed to open walk file {}'.format(path))
                raise

        file_text = file_text.replace('\r', '')
        file_lines = file_text.split('\n')
        merged_lines = []
        for line in file_lines:
            # if not line.startswith('.1.3.6') and merged_lines:
            #     merged_lines[-1] += '\n' + line
            # else:
                merged_lines.append(line)

        reg_line = re.compile('^\.(.*?)\s*=\s*(.*)$', re.MULTILINE)
        reg_value = re.compile('^([a-zA-Z0-9\-\s]+?):\s*(.*)$')

        for line in merged_lines:
            try:
                reg_line_match = reg_line.match(line)
                oid, rest = reg_line_match.group(1), reg_line_match.group(2)
                reg_value_match = reg_value.match(rest)
                oid_type, oid_value = reg_value_match.group(1), reg_value_match.group(2)

                if oid_type in ('INTEGER', 'Gauge32', 'Gauge64', 'Counter32', 'Counter64'):
                    oid_value = int(oid_value)
                elif oid_type == 'STRING':
                    oid_value = oid_value.strip('"')
                elif oid_type == 'Timeticks':
                    oid_value = int(oid_value[1:].split(')')[0])

                self._add_oid_record({
                    'oid': oid,
                    'name': None,
                    'type': oid_type,
                    'value': oid_value,
                })
            except:
                log.debug('invalid line=%s' % line)
        log.info('loading SNMP walk file {} done!'.format(path))

    def _add_oid_record(self, record):
        self.oid_dict[record['oid']] = record
        self.snmp_agent.add_oid(record['oid'], record['type'], self.get_value)

    def get_value(self, name, oid_):
        oid = '.'.join([str(i) for i in name])
        oid_value, oid_type_str = self.oid_dict.get(oid, {}).get('value', 'Unknown value'), self.oid_dict.get(oid, {}).get('type', 'STRING')
        if oid == '1.3.6.1.2.1.1.3.0':
            oid_value = self.sysuptime()
        log.debug('get %s [%s] %s %s' % (oid, oid_, oid_type_str, oid_value))
        return oid_value, oid_type_str

    def sysuptime(self):
        # MIB2::sysUptime
        return int(time.time() - self.start_time)


def main():
    oid_dict = {}

#    simulator = Simulator(host='127.0.0.1', port='1610', rcommunity='public')

    snmpEngine = engine.SnmpEngine()
    config.addSocketTransport(snmpEngine, udp.domainName, udp.UdpTransport().openServerMode(('127.0.0.1', '1610')))
    config.addV1System(snmpEngine, 'my-area', 'public')
    config.addVacmUser(snmpEngine, 2, 'my-area', 'noAuthNoPriv', (1, 3, 6) )
    snmpContext = context.SnmpContext(snmpEngine)
    mibBuilder = snmpContext.getMibInstrum().getMibBuilder()
    MibScalar, MibScalarInstance = mibBuilder.importSymbols('SNMPv2-SMI', 'MibScalar', 'MibScalarInstance')
    cmdrsp.GetCommandResponder(snmpEngine, self.snmpContext)
    cmdrsp.NextCommandResponder(snmpEngine, self.snmpContext)
    cmdrsp.BulkCommandResponder(snmpEngine, self.snmpContext)

#    simulator.add_walkfile('walk_file')

    oid_dict['1.3.6.1'] =   {
                            'oid': '1.3.6.1',
                            'name': None,
                            'type': 'STRING',
                            'value': 'test string 1',
                            }
    oid_dict['1.3.6.2'] =   {
                            'oid': '1.3.6.2',
                            'name': None,
                            'type': 'STRING',
                            'value': 'test string 2',
                            }
#    self.snmp_agent.add_oid(record['oid'], record['type'], self.get_value)

        oid_num = rfc1902.ObjectName(oid).asTuple()
        oid_type = TYPE_MAP[oid_type_str]
        self.mibBuilder.exportSymbols(
            '__MY_MIB',
            self.MibScalar(oid_num[:-1], oid_type),
            createVariable(self.MibScalarInstance, getValue, oid_num[:-1], (oid_num[-1],), oid_type)
        )

#    simulator.snmp_agent.serve_forever()

        snmpEngine.transportDispatcher.jobStarted(1)
        try:
            snmpEngine.transportDispatcher.runDispatcher()
        except KeyboardInterrupt:
            snmpEngine.transportDispatcher.closeDispatcher()


if __name__ == "__main__":
    main()
