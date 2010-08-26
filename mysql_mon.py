#!/usr/bin/python

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; version 2
# of the License.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the Free
# Software Foundation, Inc., 59 Temple Place - Suite 330, Boston,
# MA 02111-1307, USA

mysql_user='test'
mysql_password='test'
mysql_host_list=['malvinas','127.0.0.1','malvinas.localhost.com'] # do not use localhost. Use a unique identifier (hostname, IP...)

svn_co_url='http://user:password@localhost/subversion/' # where am  I going to put all the stuff!
cwd='/tmp/' #where am I going to store temporary files and svn checkout

mail_to='test@me.com' #Where to send the changes

#############################################################################
## Do not change anything below this line unless you know what you are doing
#############################################################################

DEBUG=True

import os
import pysvn
import shutil 
import time
import sys
import MySQLdb
import smtplib
import socket
import random
import string
from email.mime.text import MIMEText

mail_from='mysql_mon@'+socket.gethostname()
svn_client = pysvn.Client()
random_str=''.join(random.choice(string.letters) for i in xrange(10))
cwd+='/'+random_str+'/' # generating a random dir to store the checkout


if os.environ['USER'] == "root": 
	print "Can't run as root"
	sys.exit()

os.mkdir(cwd)

def p(string):
	if DEBUG:
		print string;

def create_svn():
	svn_client.checkout(svn_co_url,cwd)
	try:
		svn_client.mkdir(cwd+'/mysql_mon/','initializing mysql_mon directory')
	except:
		p("Error creating svn directory. It may already exists")

def checkout_svn():
	p('Checking existing svn checkout...')
	try:
		if os.path.exists(cwd+'/mysql_mon/') and svn_client.root_url_from_path(cwd+'/mysql_mon') == svn_co_url+'/mysql_mon/': 
			p("Svn directory seems to exist.")
		else:
			p("Checking out from SVN")
			svn_client.checkout(svn_co_url+'/mysql_mon/',cwd+'/mysql_mon/')
	except:
		print"Unexpected error during checkout. Is it the first time you run mysql_mon? run it with '--create' first. ",sys.exc_info()[0]
		return False
	return True

def dump_and_diff_schema(mysql_host):
	p('\tDumping DB schema ...')
	diff_text=''
	first_run=True
	dst_file=cwd+'/mysql_mon/schema.'+mysql_host+'.sql'
	if os.path.exists(dst_file):
		first_run=False
	os.system('mysqldump -R --skip-dump-date -d -u'+mysql_user+' -p'+mysql_password+' -h'+mysql_host+' -A|sed -r "s/ AUTO_INCREMENT=[0-9]+ / /g">'+dst_file)
	if first_run:
		svn_client.add(dst_file)
	diff_text = svn_client.diff(cwd,dst_file)
	return diff_text

def get_mysql_variables(mysql_host):
	p('\tChecking variables ...')
        diff_text=''
        first_run=True
	dst_file = cwd+'/mysql_mon/variables.'+mysql_host
        if os.path.exists(dst_file):
                first_run=False
	os.system('mysql -u'+mysql_user+' -p'+mysql_password+' -h'+mysql_host+' -e"show variables"|egrep -v "(pseudo_thread_id|timestamp)">'+dst_file)
        if first_run:
                svn_client.add(dst_file)
        diff_text = svn_client.diff(cwd,dst_file)
        return diff_text

def get_user_permissions(mysql_host):
	p('\tChecking user permissions ...')
	conn = MySQLdb.connect (mysql_host, mysql_user, mysql_password)
	mysqlcursor = conn.cursor()
	diff_text=''
        first_run=True
	dst_file = cwd+'/mysql_mon/users.'+mysql_host

        if os.path.exists(dst_file):
                first_run=False

	f = open(dst_file,'w')

	mysqlcursor.execute("""select user,host from mysql.user""")
	rows = mysqlcursor.fetchall()
	for row in rows:
		p("\t\tshow grants for '"+row[0]+"'@'"+row[1]+"'")
		mysqlcursor.execute("""show grants for %s@%s """, (row[0], row[1]))
		rows_grant = mysqlcursor.fetchall()
		diff_text+="/* grants for %s@%s */\n" %(row[0], row[1])
		for row_grant in rows_grant:
			diff_text+=row_grant[0]+"\n"

	f.writelines(diff_text)
	f.close()
        if first_run:
                svn_client.add(dst_file)
        else:
                diff_text = svn_client.diff(cwd,dst_file)
        return diff_text



def cleanup():
	p('Cleaning tmp directories and files')
	shutil.rmtree(cwd);	

def commit_differences():
	svn_client.checkin(cwd+'/mysql_mon/','Commit of DB schema')

def send_email(text):
	msg =  MIMEText(text, 'plain')
	msg['Subject'] = 'MySQL mon: Changes on %s' % socket.gethostname()
	msg['From'] = mail_from
	msg['To'] = mail_to

	# Send the message via our own SMTP server, but don't include the
	# envelope header.
	s = smtplib.SMTP('localhost')
	s.sendmail(mail_from, [mail_to], msg.as_string())
	s.quit()
	

if __name__ == '__main__':
	if '--create' in sys.argv:
		p('creating mysql_mon svn directory...')
		create_svn()
		p('done')
		commit_differences()
	else:
		if checkout_svn():
			all_diff=''
			for mysql_host in mysql_host_list:
				p(mysql_host+":")
			        all_diff+=dump_and_diff_schema(mysql_host)
			        all_diff+=get_mysql_variables(mysql_host)
				all_diff+=get_user_permissions(mysql_host)
			if len(all_diff) > 0:
				p('Sending email!')
				send_email(all_diff)
				print all_diff
			else:
				p('No changes found')
			commit_differences()
	cleanup()
	p('Bye!')
