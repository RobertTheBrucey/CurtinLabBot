#!/usr/bin/python
from configparser import ConfigParser

def config( filename='database.ini', section='postgresql' ):
    parser = ConfigParser()
    parser.read( filename )
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception( 'Section {0} not found in the {1} file'.format(section, filename) )
    return db

def getToken( filename='token.ini', section='token' ):
    parser = ConfigParser()
    parser.read( filename )
    if parser.has_section(section):
        token = parser.items(section)[0][1]
    else:
        raise Exception( 'Section {0} not found in the {1} file'.format(section, filename) )
    return token

def getCreds( filename='curtincreds.ini', section='creds'):
    parser = ConfigParser()
    parser.read( filename )
    if [parser.has_section(section)]:
        username = parser[section]['username']
        password = parser[section]['password']
    else:
        raise Exception( "Section {0} not found in the {1} file".format(section,filename) )
    return (username,password)