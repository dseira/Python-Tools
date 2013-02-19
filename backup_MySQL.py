#!/usr/bin/env python
# -*- coding: utf-8 -*-

__applicationName__     = "backup.py"
__blurb__               = """Make a backup from MySQL tables"""
__author__              = "David Seira davidseira@gmail.com"
__version__             = "1.2"
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

"""
TODO: 
- Filter input options
- Extract the MySQL DBs with MySQL python module
- Check the consistency of the database after the backup
"""

import os
import re
import optparse
from subprocess import Popen, PIPE
from datetime import datetime
import time
import shutil
import tarfile
import logging

USER        = ""                          #MySQL user
PASS        = ""                          #MySQL pass
HOSTNAME    = "127.0.0.1"                 #MySQL hostname
DB          = []                          #Total DBs
DEBUG       = True                        #Debug mode
COMPRESS    = None                        #Compression program
FILES       = ""                          #Files created
DEST_DIR    = "/tmp/backup"               #Destination backup directory
LOGFILE     = "/tmp/backup/backup.log"    #logfile
LOGGER      = None                        #Creating a logger instance
        
def getTime():
    """
    Return the datetime now
    """
    return str(datetime.now().year).zfill(4) + str(datetime.now().month).zfill(2) \
    + str(datetime.now().day).zfill(2) + "_" + str(datetime.now().hour).zfill(2) \
    + str(datetime.now().minute).zfill(2) + str(datetime.now().second).zfill(2)
   
    
def isPath(file):
    """
    Return if the path exists (removing the file).
    """
    ret = True
    path = "/"
    aux = file.split("/")
    for i in range(1,len(aux)-1):
        path = str(path) + str(aux[i]) + "/"
    
    if not os.path.exists(path):
        ret = False
        
    return ret
    
    
def usage():
    """Function for show the usage.
    
    Return the usage information for the program.
    """
    print("\nBackup MySQL\n\n\
         -u, --user\tMySQL User*\n\
         -p, --pass\tMySQL Pass*\n\
         --hostname\tMySQL Hostname\n\
         --databases\tDatabases to backup, separate with commas*\n\
         --dest\t\tDestination backup directory (/tmp/backup by default)\n\
         -d, --debug\tPrint debug info\n\
         -l, --logfile\tLogging file (/tmp/backup/backup.log by default)\n\n\
         Options with * are mandatory\n\n\
         Example: backup.py -u root -p 1234 --hostname 192.168.1.1 --databases radius,mysql,db1\n")
    exit(3)
    

def processLineArgument():
    """Process the line argument.
    
    Process the line argument, extract the differents options and save into a global variables.
    """
    
    global USER, PASS, DB, DEBUG, DEST_DIR, HOSTNAME, LOGFILE
    parser = optparse.OptionParser()
    parser.add_option('-u','--user',help='MySQL User',dest='user')
    parser.add_option('-p','--pass',help='MySQL Pass',dest='password')
    parser.add_option('','--hostname',help='MySQL Host',dest='hostname')
    parser.add_option('','--databases',help='MySQL Databases',dest='db')
    parser.add_option('','--dest',help='Destination backup dir',dest='dest')
    parser.add_option('-l','--logfile',help='Logfile of the output',dest='logfile')
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
    if opts.hostname is not None:   HOSTNAME = opts.hostname
    if opts.dest is not None:
        if os.path.exists(opts.dest):
            DEST_DIR = opts.dest
        else:
            if DEBUG:   print "[" + getTime() + "] Warning: " + opts.dest + " doesn't exist, using default /tmp/backup"
    else:
        if DEBUG:
            print "[" + getTime() + "] Info: using default /tmp/backup"
            
    if opts.logfile is not None:
        if isPath(opts.logfile):
            LOGFILE = opts.logfile
        else:
            if DEBUG:   print "[" + getTime() + "] Warning: Using default /tmp/backup/backup.log"
    else:
        if DEBUG:   print "[" + getTime() + "] INFO: Using default /tmp/backup/backup.log"
        
  
def backupDB(db):
    """
    Backup DBs with mysqldump.
    """
    global FILES
    ret = True    
    if DEBUG:   print "[" + getTime() + "] Backing Up DB #" + str(db) + "#..."
    LOGGER.info("Backing Up DB #" + str(db) + "#...")
    p = Popen("/usr/bin/mysqldump -u" + USER + " -p" + PASS + " -h " + HOSTNAME \
    + " " + str(db) +     " > /tmp/" + str(db) + ".sql ", shell=True, stdout=PIPE, \
    stderr=PIPE)
    error = p.stderr.read()
    if error != "":
        if DEBUG:   print "[" + getTime() + "] Error: " + error[:-1]
        LOGGER.error(error[:-1])
        os.remove("/tmp/" + db + ".sql")
        ret = False
    else:
        FILES += db + ".sql.zip " #Adding the verified DB

    return ret
       
  
def zipDB(db):
    """
    Zip the databases.
    """
    import zipfile
    try:
        import zlib
        compression = zipfile.ZIP_DEFLATED
    except:
        compression = zipfile.ZIP_STORED

    ret = True
    actual_dir = os.getcwd()
    os.chdir('/tmp')
    if os.path.exists(str(db) + ".sql"):
        if DEBUG:   print "[" + getTime() + "] Zipping #" + str(db) + "#..."
        LOGGER.info("Zipping #" + str(db) + "#...")
        zf = zipfile.ZipFile(str(db) + ".sql.zip","w", compression=zipfile.ZIP_DEFLATED)
        try:
            zf.write(str(db) + ".sql", compress_type=compression)
        except OSError, e:
            if DEBUG:   print "[" + getTime() + "] Error: ", e
            LOGGER.error(e)
            os.remove(str(db) + ".sql.zip")
            ret = False
        finally:
            zf.close()
        
    else:
        if DEBUG:   print "[" + getTime() + "] Error: there isn't file /tmp/" \
        + str(db) + ".sql"
        LOGGER.error("There isn't file /tmp/" + str(db) + ".sql")
        ret = False
        
    os.chdir(actual_dir)
    return ret    
          
            
def checkDependencies():
    """
    Check the dependencies like bzip2, gzip, mysqldump, etc...
    """
    global COMPRESS
    ret = True

    #Creating destination folder    
    if os.path.exists(DEST_DIR) is False:
        os.mkdir(DEST_DIR)
            
    #Check compression programs
    if os.path.exists("/bin/bzip2"):
        COMPRESS = "bz2"
    elif os.path.exists("/bin/gzip"):
        COMPRESS = "gz"
    else:
        if DEBUG:   print "[" + getTime() + "] Error: you must install either gzip or bzip2."
        LOGGER.error("You must install either gzip or bzip2")
        ret = False
    
    #Checking mysqldump    
    if os.path.exists("/usr/bin/mysqldump") is False:
        if DEBUG:   print "[" + getTime() + "] Error: you must install mysqldump."
        LOGGER.error("You must install mysqldump")
        ret = False
            
    return ret


def makeTar():
    """
    Make the tar file with all of the DBs
    """    
    ret = True
    if FILES != "":
        actual_dir = os.getcwd()
        os.chdir('/tmp')

        file = "backup_db_" + HOSTNAME + "_" + getTime() + ".tar." + str(COMPRESS)
        tar = tarfile.open(file, "w|" + str(COMPRESS))
        try:
            for i in FILES.split():
                tar.add(i)
        except OSError, e:
            if DEBUG:   print "[" + getTime() + "] Error: ", e
            LOGGER.error(e)
        finally:
            tar.close()
        
        #Moving the tar file to the destination directory
        shutil.move(file,DEST_DIR)
                        
        os.chdir(actual_dir)
    else:
        if DEBUG:   print "[" + getTime() + "] Error: no files to tar"
        LOGGER.error("No files to tar")
        ret = False
        
    return ret    
   
   
def cleanUp():
    """
    Cleaning the old files.
    """
    ret = True
    actual_dir = os.getcwd()
    os.chdir('/tmp')
    try:
        for i in FILES.split():
            os.remove(i)
    except OSError, e:
        if DEBUG:   print "[" + getTime() + "] Error: ", e
        LOGGER.error(e)
        ret = False
    finally:
        os.chdir(actual_dir)
        
    return ret
    
    
def Run():
    """
    Main function to execute the backup of the radius tables.
    """
    global LOGGER
    processLineArgument()
    if checkDependencies() is True:
        
        LOGGER = logging.getLogger('backup')
        hdlr = logging.FileHandler(LOGFILE)
        formatter = logging.Formatter('[%(asctime)s] [%(funcName)s] %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        LOGGER.addHandler(hdlr) 
        LOGGER.setLevel(logging.INFO)
        
        if DEBUG:   print "[" + getTime() + "] Starting Backup MySQL..."
        LOGGER.info("Starting Backup MySQL...")
        if DEBUG:   print "[" + getTime() + "] Starting Zip..."
        LOGGER.info("Starting Zip...")
        for database in DB:
            if backupDB(database):
                zipDB(database)
                
        if DEBUG:   print "[" + getTime() + "] Starting Packing..."
        LOGGER.info("Starting Packing...")
        if makeTar() is True:
            if DEBUG:   print "[" + getTime() + "] Cleaning up Files..."
            LOGGER.info("Cleaning up Files...")
            cleanUp()


#Launching the main execution
if __name__ == "__main__":
    Run()

