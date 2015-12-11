from setuptools import setup

setup(
    name='snmp-simulator',
    description="A simple SNMP Simulator driven by agent's snmpwalk",
    version='0.6.0',
    author='Dmitry Korobitsin',
    author_email='korobicin@gmail.com',
    url='https://github.com/xeemetric/snmp-simulator',
    packages=['snmp_simulator', 'snmp_simulator.packages'],
    install_requires=['pysnmp==4.2.5'],
    entry_points={
        'console_scripts': [
            'snmp-simulator = snmp_simulator.simulator:main',
        ],
    },
    platforms=['Any'],
    license='BSD',
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python'
    ),
    zip_safe=False,
)
