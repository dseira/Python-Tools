#!/usr/bin/env python
# -*- coding: utf-8 -*-

__applicationName__     = "backup-mysql.py"
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


# Standard imports
import argparse
from datetime import datetime
import glob
import logging
from multiprocessing import Pool, Manager
import os
import shutil
import socket
from subprocess import Popen, PIPE
import sys
import tarfile
import time

# Other imports
try:
    from lockfile import FileLock
except ImportError, e:
    print "Error: " + e.message + ". Aborting."
    sys.exit(3)


HOSTNAME        = ""
USER            = ""
PASSWORD        = ""
COMPRESS        = None    # Compression program
log             = None
PIDFILE         = "/var/run/backup_mysql.pid"
FILES           = Manager().list()    # Files created. Shared memory for the multiprocessing.


def getTime():
    """
    Return the datetime now
    """
    return str(datetime.now().year).zfill(4) + str(datetime.now().month).zfill(2) \
    + str(datetime.now().day).zfill(2) + "_" + str(datetime.now().hour).zfill(2) \
    + str(datetime.now().minute).zfill(2) + str(datetime.now().second).zfill(2) \
    + "_" + str(datetime.now().microsecond).zfill(6)
   
    
def validIPv4(ipv4):
    """
    Validate that the IP is an IPv4 valid address

    @param ipv4: IP to check
    @return: True or False.
    """
    try:
        socket.inet_aton(ipv4)
        return True
    except socket.error:
        return False


def cleanPidfile():
    """
    Clean the pidfile when normal exit or error is produced
    """
    if os.path.exists(PIDFILE):
        log.info("Cleanning the pidfile " + PIDFILE)
        os.remove(PIDFILE)


def createPidfile(pidfile):
    """
    Create a pidfile of the processes.
    @param pidfile: Pidfile of the processes to save.
    """
    log.info("Creating pidfile " + str(pidfile))
    f = open(PIDFILE, "a")
    f.write(str(pidfile) + "\n")
    f.close()


def initProcess():
    """
    Initial process for handling the pidfile
    """
    #Locking the Pidfile concurrency
    lock = FileLock(PIDFILE)
    with lock:
        createPidfile(os.getpid())


def backupDB(db):
    """
    Backup DBs with mysqldump.
    """
    global FILES
    ret = True

    log.info("Backing Up DB #" + str(db) + "#")
    p = Popen("/usr/bin/mysqldump -u" + USER + " -p" + PASSWORD + " -h " + HOSTNAME + " " + str(db) + " > /tmp/"
              + str(db) + ".sql ", shell=True, stdout=PIPE, stderr=PIPE)
    error = p.stderr.read()
    if error != "":
        log.error(error[:-1])
        os.remove("/tmp/" + db + ".sql")
        ret = False
    else:
        FILES.append(db + ".sql.zip")  # Adding the verified DB

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
        log.info("Zipping #" + str(db) + "#")
        zf = zipfile.ZipFile(str(db) + ".sql.zip", "w", compression=zipfile.ZIP_DEFLATED)
        try:
            zf.write(str(db) + ".sql", compress_type=compression)
        except OSError, e:
            log.error(e)
            os.remove(str(db) + ".sql.zip")
            ret = False
        finally:
            zf.close()
        
    else:
        log.error("There isn't file /tmp/" + str(db) + ".sql")
        ret = False
        
    os.chdir(actual_dir)
    return ret


def checkDependencies():
    """
    Check the dependencies like bzip2, gzip, mysqldump, etc...
    """
    global COMPRESS
    ret = True
            
    # Check compression programs
    if os.path.exists("/bin/bzip2"):
        COMPRESS = "bz2"
        log.info("Using bzip2")
    elif os.path.exists("/bin/gzip"):
        COMPRESS = "gz"
        log.info("Using gzip")
    else:
        log.error("You must install either gzip or bzip2")
        ret = False
    
    # Checking mysqldump
    if os.path.exists("/usr/bin/mysqldump") is False:
        log.error("You must install mysqldump")
        ret = False
    else:
        log.info("msyqldump is installed")
            
    return ret


def makeTar(hostname, destination):
    """
    Make the tar file with all of the DBs
    """

    if len(FILES) > 0:
        current_dir = os.getcwd()
        os.chdir('/tmp')

        filename = "backup_db_" + hostname + "_" + getTime() + ".tar." + str(COMPRESS)
        log.info("Saving tar backup in " + filename)

        tar = tarfile.open(filename, "w|" + str(COMPRESS))
        try:
            for i in FILES:
                tar.add(i)
        except OSError, e:
            log.error(e)
        finally:
            tar.close()
        
        # Moving the tar file to the destination directory
        if not os.path.exists(destination + "/" + filename):
            shutil.move(filename, destination)

        os.chdir(current_dir)
    else:
        log.error("No files to tar")


def cleanUp():
    """
    Cleaning the old files.
    """
    log.info("Cleaning temporary files")
    ret = True
    current_dir = os.getcwd()
    os.chdir('/tmp')
    try:
        for i in FILES:
            os.remove(i)  # removing db.sql.zip
            os.remove(i.split(".zip")[0])  # removing db.sql
        cleanPidfile()

    except OSError, e:
        log.error(e)
        ret = False

    finally:
        os.chdir(current_dir)
        
    return ret
    

def usage(message=None):
    """Function for show the usage.

    Return the usage information for the program.
    """
    print("\nUsage: backup-mysql.py [OPTION]\n\n\
    Backup the MySQL databases.\n\n\
         -u, --user          MySQL User*\n\
         -p, --pass          MySQL Pass*\n\
         --hostname          MySQL Hostname\n\
         --databases         Databases to backup, separate with spaces*\n\
         -d, --destination   Destination backup directory (/tmp/backup by default)\n\
         -v, --verbose       Verbose mode\n\
         -l, --logfile       Logging file (/tmp/backup/backup.log by default)\n\n\
         Options with * are mandatory\n\n\
         Example: backup-mysql.py -u root -p 1234 --hostname 192.168.1.1 --databases radius mysql db1\n")

    if message:
        print message + "\n"

    sys.exit(3)


def processLineArgument():
    """
    Process the line argument, extract the differents options and save into a global variables.

    @return options: Dictionary with the options extracted from argument line.
    """

    global USER, PASSWORD, HOSTNAME
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', help='MySQL User', dest='user')
    parser.add_argument('-p', '--pass', help='MySQL Pass', dest='password')
    parser.add_argument('--hostname', help='MySQL Host', dest='hostname')
    parser.add_argument('--databases', help='MySQL Databases', dest='db', nargs='*')
    parser.add_argument('-d', '--dest', help='Destination backup dir', dest='dest')
    parser.add_argument('-l', '--logfile', help='Logfile of the output', dest='logfile')
    parser.add_argument('-v', '--verbose', help='Print debug info', dest='verbose', default=False, action='store_true')

    args = parser.parse_args()

    options = {'VERBOSE_DEBUG': args.verbose,
               'LOGFILE': "/tmp/backup-mysql.log",
               'MAX_PROCESSES': 20}

    if args.user is not None and args.password is not None:
        options['USER'] = args.user
        USER = args.user
        options['PASS'] = args.password
        PASSWORD = args.password
    else:
        usage("Need user and password.")

    if args.db is not None:
        options['DB'] = args.db
    else:
        usage("Need a database to backup.")

    if args.hostname is not None and validIPv4(args.hostname):
        options['HOSTNAME'] = args.hostname
        HOSTNAME = args.hostname
    else:
        options['HOSTNAME'] = "127.0.0.1"
        HOSTNAME = args.hostname

    if args.dest is not None and os.path.exists(args.dest):
        options['DESTINATION'] = args.dest
    else:
        usage("Destination must be a valid directory.")

    if args.logfile is not None and os.path.exists(os.path.dirname(args.logfile)):
        options['LOGFILE'] = args.logfile

    return options


def configLogger(options):
    """
    Configure the logger service.
    @param options:
    """
    global log

    # Preparing the logging system
    log = logging.getLogger("logging")
    log.setLevel(logging.INFO)
    log_format = logging.Formatter('[%(asctime)s] [%(funcName)s] %(levelname)s %(message)s')
    try:
        fh = logging.FileHandler(options['LOGFILE'])
        fh.setFormatter(log_format)
        if options['VERBOSE_DEBUG']:
            sh = logging.StreamHandler()
            sh.setFormatter(log_format)
            log.addHandler(sh)
        log.addHandler(fh)
    except IOError, e:
        print e
        sys.exit(3)




def main(options):
    """
    Main function to execute the backup of the tables.
    """
    log.info("Starting Backup MySQL")

    t_ini = time.time()  # initial time mark

    if not checkDependencies():
        sys.exit(3)

    if len(options['DB']) > 1:
        log.info("Enabling multiprocessing")

        # Deleting garbagge files in /var/run/ when there are problems
        if not os.path.exists(os.path.dirname(PIDFILE)):
            os.mkdir(os.path.dirname(PIDFILE))
        pattern = "*.MainThread-*"
        trash = glob.glob(os.path.join(os.path.dirname(PIDFILE), pattern))
        if trash:
            for i in trash:
                os.remove(i)

        # Creating the Pidfile for handle the processes pids
        if os.path.exists(PIDFILE):  # sanitize PIDFILE
            os.remove(PIDFILE)
        createPidfile(os.getpid())

        if len(options['DB']) < options['MAX_PROCESSES']:
            options['MAX_PROCESSES'] = len(options['DB'])



        pool = Pool(processes=options['MAX_PROCESSES'], initializer=initProcess)
        pool.map_async(backupDB, options['DB']).get(9999999)
        pool.close()
        pool.join()

        pool = Pool(processes=options['MAX_PROCESSES'], initializer=initProcess)
        pool.map_async(zipDB, options['DB']).get(9999999)
        pool.close()
        pool.join()

    elif len(options['DB']) == 1:
        if backupDB(options['DB'][0]):
            zipDB(options['DB'][0])

    makeTar(options['HOSTNAME'], options['DESTINATION'])
    cleanUp()

    t_end = time.time()  # end time mark
    log.info("Total time spent: " + str(round(t_end - t_ini, 4)) + " seconds")


#Launching the main execution
if __name__ == "__main__":
    options = processLineArgument()
    configLogger(options)
    main(options)


