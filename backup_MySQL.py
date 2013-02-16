#!/usr/bin/env python
# -*- coding: utf-8 -*-

__applicationName__     = "backup_MySQL.py"
__blurb__               = """Make a backup from MySQL databases"""
__author__              = "David Seira davidseira@gmail.com"
__version__             = "1.0"
__date__                = "13/02/2013"
__licenseName__         = "GPL v3"
__license__             = """This program is free software: you can redistribute it and/or modify
                        it under the terms of the GNU General Public License as published by
                        the Free Software Foundation, either version 3 of the License, or
                        (at your option) any later version.

                        This program is distributed in the hope that it will be useful,
                        but WITHOUT ANY WARRANTY; without even the implied warranty of
                        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
                        GNU General Public License for more details.

                        You should have received a copy of the GNU General Public License
                        along with this program.  If not, see <http://www.gnu.org/licenses/>.
                        """

import os
import re
import optparse
from subprocess import Popen, PIPE
from datetime import datetime
import time
import shutil

USER        = ""            #MySQL user
PASS        = ""            #MySQL pass
DB          = []            #Total DBs
DEBUG       = True          #Debug mode
COMPRESS    = None          #Compression program
FILES       = ""            #Files created
DEST_DIR    = "/tmp/backup" #Destination backup directory


def getTime():
    """
    Return the datetime now
    """
    return str(datetime.now().year).zfill(4) + str(datetime.now().month).zfill(2) \
    + str(datetime.now().day).zfill(2) + "_" + str(datetime.now().hour).zfill(2) \
    + str(datetime.now().minute).zfill(2) + str(datetime.now().second).zfill(2)
    
    
def usage():
    """Function for show the usage.
    
    Return the usage information for the program.
    """
    print("\nBackup MySQL\n\n\
         -u, --user\tMySQL User*\n\
         -p, --pass\tMySQL Pass*\n\
        --databases\tDatabases to backup, separate with commas*\n\
        --dest\tDestination backup directory (/tmp by default)\n\
         -d, --debug\tPrint debug info\n\n\
         Options with * are mandatory\n\n\
         Example: backup.py -u root -p 1234 --databases radius,mysql,db1\n")
    exit(3)
    

def processLineArgument():
    """Process the line argument.
    
    Process the line argument, extract the differents options and save into a global variables.
    """
    
    global USER, PASS, DB, DEBUG, DEST_DIR
    parser = optparse.OptionParser()
    parser.add_option('-u','--user',help='MySQL User',dest='user')
    parser.add_option('-p','--pass',help='MySQL Pass',dest='password')
    parser.add_option('','--databases',help='MySQL Databases',dest='db')
    parser.add_option('','--dest',help='Destination backup dir',dest='dest')
    parser.add_option('-d','--debug',help='Print debug info',dest='debug',\
    default=False,action='store_true')
    
    (opts,args) = parser.parse_args()

    #Mandatory options
    if opts.user is None or opts.password is None or opts.db is None:
       usage()

    USER = opts.user
    PASS = opts.password
    DB = opts.db.split(",")
    if opts.debug is not None:  DEBUG = opts.debug
    if opts.dest is not None and os.path.exists(opts.dest): DEST_DIR = opts.dest
    
  
def backupDB(db):
    """
    Backup DBs with mysqldump.
    """
    global FILES
    ret = True    
    if DEBUG:   print "[" + getTime() + "] Backing Up DB #" + str(db) + "#..."
    p = Popen("/usr/bin/mysqldump -u" + USER + " -p" + PASS + " " + str(db) + \
    " > /tmp/" + str(db) + ".sql ", shell=True, stdout=PIPE, stderr=PIPE)
    error = p.stderr.read()
    if error != "":
        if DEBUG:   print "[" + getTime() + "] Error: " + error[:-1]
        os.remove("/tmp/" + db + ".sql")
        ret = False
    else:
        if COMPRESS == "/bin/bzip2":
            FILES += db + ".sql.bz2 " #Adding the verified DB
        elif COMPRESS == "/bin/gzip":
            FILES += db + ".sql.gz " #Adding the verified DB
            
    return ret
       

def zipDB(db):
    """
    Zip the databases.
    """
    ret = True
    if os.path.exists("/tmp/" + str(db) + ".sql"):
        if DEBUG:   print "[" + getTime() + "] Zipping #" + str(db) + "#..."
        p = Popen(COMPRESS + " -f /tmp/" + str(db) + ".sql", shell=True, \
        stdout=PIPE, stderr=PIPE)
        error = p.stderr.read()
        if error != "":
            if DEBUG:   print "[" + getTime() + "] Error: " + error[:-1]
            ret = False
        
    else:
        if DEBUG:   print "[" + getTime() + "] Error: there isn't file /tmp/" \
        + str(db) + ".sql"
        ret = False
    return ret
        
    
def checkDependencies():
    """
    Check the dependencies like bzip2, gzip, mysqldump, etc...
    """
    global COMPRESS
    ret = True
    #Check compression programs
    if os.path.exists("/bin/bzip"):
        COMPRESS = "/bin/bzip2"
    elif os.path.exists("/bin/gzip"):
        COMPRESS = "/bin/gzip"
    else:
        if DEBUG:   print "[" + getTime() + "] Error: you must install either gzip or bzip2."
        ret = False
        
    if os.path.exists("/usr/bin/mysqldump") is False:
        if DEBUG:   print "[" + getTime() + "] Error: you must install mysqldump."
        ret = False
        
    return ret
    

def makeTar():
    """
    Make the tar file with all of the DBs
    """
    ret = True
    actual_dir = os.getcwd()
    os.chdir('/tmp')
    if COMPRESS == "/bin/bzip2":
        file = "backup_db_" + getTime() + ".tar.bz2"
        p = Popen("tar jcf " + file + " " + FILES, shell=True, \
        stdout=PIPE, stderr=PIPE)
        error = p.stderr.read()
        if error != "":
            if DEBUG:   print "[" + getTime() + "] Error: " + error[:-1]
            ret = False
        else:
            if  os.path.exists(DEST_DIR) is False:
                os.mkdir(DEST_DIR)
            shutil.move(file,DEST_DIR)
        
    elif COMPRESS == "/bin/gzip":
        file = "backup_db_" + getTime() + ".tar.gz"
        p = Popen("tar zcf " + file + " " + FILES, shell=True, \
        stdout=PIPE, stderr=PIPE)
        error = p.stderr.read()
        if error != "":
            if DEBUG:   print "[" + getTime() + "] Error: " + error[:-1]
            ret = False
        else:
            if os.path.exists(DEST_DIR) is False:
                os.mkdir(DEST_DIR)
            shutil.move(file,DEST_DIR)
    
    os.chdir(actual_dir)
    return ret
    
   
def cleanUp():
    """
    Cleaning the old files.
    """
    ret = True
    actual_dir = os.getcwd()
    os.chdir('/tmp')
    p = Popen("rm " + FILES, shell=True, stdout=PIPE, stderr=PIPE)
    error = p.stderr.read()
    if error != "":
        if DEBUG:   print "[" + getTime() + "] Error: " + error[:-1]
        ret = False
        
    os.chdir(actual_dir)
    return ret
    
    
def Run():
    """
    Main function to execute the backup of the radius tables.
    """
    processLineArgument()
    if checkDependencies() is True:
        if DEBUG:   print "[" + getTime() + "] Starting Backup MySQL..."
        if DEBUG:   print "[" + getTime() + "] Starting Zip..."
        for database in DB:
            if backupDB(database):
                zipDB(database)
        if DEBUG:   print "[" + getTime() + "] Starting Packing..."
        if makeTar() is True:
            if DEBUG:   print "[" + getTime() + "] Cleaning up Files..."
            cleanUp()


#Launching the main execution
if __name__ == "__main__":
    Run()
