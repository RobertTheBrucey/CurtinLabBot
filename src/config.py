#!/usr/bin/python
from configparser import ConfigParser

def getToken( filename='config.ini', section='token' ):
    parser = ConfigParser()
    parser.read( filename )
    if parser.has_section(section):
        token = parser.items(section)[0][1]
    else:
        raise Exception( 'Section {0} not found in the {1} file'.format(section, filename) )
    return token