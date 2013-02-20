#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Program to send a mail with or without an attachment
"""

__applicationName__     = "sendmail.py"
__blurb__               = """Send a mail with or without attachment"""
__author__              = "David Seira davidseira@gmail.com"
__version__             = "1.1"
__date__                = "02/01/2013"
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
import smtplib
import sys
import re
import optparse
import string
from datetime import datetime

from email import Encoders
from email.MIMEBase import MIMEBase
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.Utils import formatdate
 
 
#Global configuration variables
FILEPATH 	= None
FROM		= ""
TO		    = ""
HOST		= ""
USER		= ""
PASS		= ""
BODY		= ""
SUBJECT		= ""
DEBUG       = False


def getTime():
    """
    Return the datetime now
    """
    return str(datetime.now().year).zfill(4) + str(datetime.now().month).zfill(2) \
    + str(datetime.now().day).zfill(2) + "_" + str(datetime.now().hour).zfill(2) \
    + str(datetime.now().minute).zfill(2) + str(datetime.now().second).zfill(2) \
    + "." + str(datetime.now().microsecond).zfill(6)
    
    
def sendmail():
    """Main function to send the mail.
    
    Main function to send the mail with or without attachment.
    """
    global BODY
    aux = None
    
    if DEBUG:   print "[ " + getTime() + " ] INFO: Sending email..."
        
    #We HAVE an attachment to send
    if FILEPATH is not None:
        msg = MIMEMultipart()
        msg["From"] = FROM
        msg["To"] = TO
        msg["Subject"] = SUBJECT
        msg['Date']    = formatdate(localtime=True)

        # attach a file
        part = MIMEBase('application', "octet-stream")
        part.set_payload( open(FILEPATH,"rb").read() )
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(FILEPATH))
        msg.attach(part)

        if BODY is not None:
            body = MIMEMultipart('alternative')
            body.attach(MIMEText(BODY))
            msg.attach(body)
	
	aux = msg.as_string()

    #We DON'T HAVE an attachment
    else:
        if BODY is None:
            BODY = ""
        aux = string.join(("From: %s" % FROM, "To: %s" % TO, "Subject: %s" % SUBJECT , "", BODY), "\r\n")

    try:
        server = smtplib.SMTP(HOST)
        server.login(USER,PASS)
 
        failed = server.sendmail(FROM, TO, aux)
        server.close()
        if DEBUG:   print "[ " + getTime() + " ] INFO: Message sent OK."
    except Exception, e:
        if DEBUG:   print "[ " + getTime() + " ] ERROR: ", e


def processLineArgument():
    """Process the line argument.
    
    Process the line argument, extract the differents options and save into a global variables.
    """
    
    global FROM, TO, HOST, USER, PASS, SUBJECT, BODY, FILEPATH, DEBUG
    parser = optparse.OptionParser()
    parser.add_option('-f','--from',help='From address',dest='mailfrom')
    parser.add_option('-t','--to',help='To address',dest='mailto')
    parser.add_option('-s','--subject',help='Subject',dest='subject')
    parser.add_option('-b','--body',help='Message body',dest='body')
    parser.add_option('','--smtphost',help='SMTP host address',dest='smtphost')
    parser.add_option('-u','--user',help='User authentication',dest='user')
    parser.add_option('-p','--pass',help='Pass authentication',dest='password')
    parser.add_option('-F','--file',help='Path file to send as attachment',dest='file')
    parser.add_option('-d','--debug',help='Print debug info',dest='debug',default=False,action='store_true')
    
    (opts,args) = parser.parse_args()

    #Mandatory options
    if (opts.mailfrom is None and FROM == "") or (opts.mailto is None and TO == "") \
    or (opts.subject is None and SUBJECT == "") or (opts.smtphost is None and HOST == "") \
    or (opts.user is None and USER == "") or (opts.password is None and PASS == ""):
       usage()

    if opts.mailfrom:   FROM = opts.mailfrom
    if opts.mailto: TO = opts.mailto
    if opts.subject:    SUBJECT = opts.subject
    if opts.smtphost:   HOST = opts.smtphost
    if opts.user:   USER = opts.user
    if opts.password:   PASS = opts.password
    if opts.body is not None:
        BODY = opts.body
        BODY = BODY.replace("\\n","\n") #parsing the body for the correct interpretation of \n
    if opts.file is not None:    FILEPATH = opts.file
    if opts.debug is not None:  DEBUG = opts.debug



def usage():
    """Function for show the usage.
    
    Return the usage information.
    """
    
    print("\nSendmail\n\n\
         -f, --from\tFrom address*\n\
         -t, --to\tTo address*\n\
         -s, --subject\tSubject*\n\
         -b, --body\tBody\n\
         --smtphost\tSMTP host address*\n\
         -u, --user\tUser authentication*\n\
         -p, --pass\tPass authentication*\n\
         -F, --file\tPath file to send as attachment\n\n\
         -d, --debug\tPrint debug info\n\n\
         Options with * are mandatory here or into the script\n\n\
         You can also add this options editing the global variables of the script.\n\
         Variables are FROM, TO, HOST, USER and PASS.\n")
    exit()

def Run():
    """Run function.
    
    Function to process the arguments and send the mail.
    """
    processLineArgument()
    if DEBUG:
        print "*Global Options*"
        print "Filepath:    ", FILEPATH
        print "From:        ", FROM
        print "To:          ", TO
        print "Host:        ", HOST
        print "User:        ", USER
        print "Pass:        ", PASS
        print "Body:        ", BODY
        print "Subject:     ", SUBJECT
        
    sendmail()

#Launching the main execution
if __name__ == "__main__":
    Run()
