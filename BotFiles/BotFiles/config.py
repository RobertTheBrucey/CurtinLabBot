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

def getCreds( filename='config.ini', section='creds'):
    parser = ConfigParser()
    parser.read( filename )
    if [parser.has_section(section)]:
        username = parser[section]['username']
        password = parser[section]['password']
    else:
        raise Exception( "Section {0} not found in the {1} file".format(section,filename) )
    return (username,password)

def getLogfile( filename='config.ini', section='logging' ):
    parser = ConfigParser()
    parser.read( filename )
    if parser.has_section(section):
        logfile = parser.items(section)[0][1]
    else:
        raise Exception( 'Section {0} not found in the {1} file'.format(section, filename) )
    return logfile

def getKeyfile( filename='config.ini', section='keyfile' ):
    parser = ConfigParser()
    parser.read( filename )
    if parser.has_section(section):
        keyfile = parser.items(section)[0][1]
    else:
        raise Exception( 'Section {0} not found in the {1} file'.format(section, filename) )
    return keyfile