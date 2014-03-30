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

#############################################################################

#
# This project is currently developped and maintained by Isart Montane Mogas <isart.montane@gmail.com>
# If you need to get more information about the project please visit
#  https://github.com/isartmontane/MySQL-metadata-audit
#


#MySQL user/password used to get the MySQL metadata
mysql_user='isart'
mysql_password='isart'

#Used on config_file mode
mysql_host_list={
'6myServer.mydomain.com':'127.0.0.1',
'5myServer.mydomain.com':'127.0.0.1',
'4myServer.mydomain.com':'127.0.0.1',
'3myServer.mydomain.com':'127.0.0.1',
'2myServer.mydomain.com':'127.0.0.1',
'1myServer.mydomain.com':'127.0.0.1',
}

#Used on AWS mode. We will query AWS and filter all the servers that have the tag Role=mysql
aws_tag_name="Role"
aws_tag_value="mysql"

#Where do you have your git repo?
git_repo_dir="/home/isart/git-repos/mysql-monitor"
 #Where to send the changes
mail_to='me@myEmail.com'

#############################################################################
## Do not change anything below this line unless you know what you are doing
#############################################################################

DEBUG=True

from git import *
import os
import subprocess 
import shutil 
import time
import sys
import getopt 
import MySQLdb
import smtplib
import socket
import string
import json
from email.mime.text import MIMEText

mail_from='mysql_mon@'+socket.gethostname()
repo = Repo(git_repo_dir)
git_repo = repo.git
aws_server_list={}
skip_audits={}

def p(string):
	if DEBUG:
		print string;

#Make sure we have the last version of the git repo
def checkout_git():
	p('Checking existing git directory...')
	try:
		git_repo.pull()
	except:
		print"Unexpected error during checkout. Is it the first time you run mysql_mon? Make sure you have configured an exisiting git repo. "
		print sys.exc_info()
		return False
	return True

def dump_and_diff_schema(mysql_host):
	p('\tDumping DB schema ...')
	diff_text=''
	file_name='schema.'+mysql_host[0]
	dst_file = git_repo_dir+'/'+file_name
	os.system('mysqldump -R --skip-dump-date -d -u'+mysql_user+' -p'+mysql_password+' -h'+mysql_host[1]+' -A|sed -r "s/ AUTO_INCREMENT=[0-9]+ / /g">'+dst_file)

def get_mysql_variables(mysql_host):
	p('\tChecking variables ...')
        first_run=True
	file_name='variables.'+mysql_host[0]
	dst_file = git_repo_dir+'/'+file_name
	os.system('mysql -u'+mysql_user+' -p'+mysql_password+' -h'+mysql_host[1]+' -e"show variables"|egrep -v "(pseudo_thread_id|timestamp)">'+dst_file)

def get_user_permissions(mysql_host):
	p('\tChecking user permissions ...')
	conn = MySQLdb.connect (mysql_host[1], mysql_user, mysql_password)
	mysqlcursor = conn.cursor()
	diff_text=''
	file_name='users.'+mysql_host[0]
	dst_file = git_repo_dir+'/'+file_name

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

def commit_differences():
	index = repo.index
	new_files=repo.untracked_files
	for f in new_files:
		p("New file found: "+f)
		index.add([f])
	subprocess.Popen( "git commit -a -m'tracking changes' " , cwd = git_repo_dir, shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE )
	return new_files

def push_changes():
	p('Pushing changes to repo')
	index = repo.index
	git_repo.push()

def send_email(text):
	p('Sending email!')
	msg =  MIMEText(text, 'plain')
	msg['Subject'] = 'MySQL mon: Changes on %s' % socket.gethostname()
	msg['From'] = mail_from
	msg['To'] = mail_to

	# Send the message via our own SMTP server, but don't include the
	# envelope header.
	s = smtplib.SMTP('localhost')
	s.sendmail(mail_from, [mail_to], msg.as_string())
	s.quit()

def get_git_diff():
	pr = subprocess.Popen( "git diff" , cwd = git_repo_dir, shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE )
	(out, error) = pr.communicate()
	new_files=commit_differences()
	if len(new_files) > 0:
		out = out+'\n'+', '.join(new_files)
	return out

def get_aws_instances():
	p('Getting servers from AWS')
	server_list = []
	pr = subprocess.Popen('aws ec2 describe-instances --filter Name=tag:'+aws_tag_name+',Values='+aws_tag_value+' --query "Reservations[].Instances[].[State.Name,Tags,PublicDnsName]"', cwd = git_repo_dir, shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE )
	(out, error) = pr.communicate()
	servers_info = json.loads(out)

	#getting addresses from json array
	for s in servers_info:
		#only get running servers
		if s[0] == 'running':
			for t in s[1]:
				#create a name=ip touple
				if t['Key'] == 'Name':
					aws_server_list[t['Value']]=s[2]

	return aws_server_list

def run_diff(mysql_host_list):
	p('Checking the following servers: '+', '.join(mysql_host_list))
	if checkout_git():
		all_diff=''
		for mysql_host in mysql_host_list.items():
			p("Host - "+mysql_host[0]+":")
			if "skip-variables-audit" not in skip_audits:
			        get_mysql_variables(mysql_host)
			if "skip-user-audit" not in skip_audits:
				get_user_permissions(mysql_host)
			if "skip-schema-audit" not in skip_audits.keys():
				dump_and_diff_schema(mysql_host)
		all_diff=get_git_diff()
		if len(all_diff) > 0:
			p('Changes found:')
			p(all_diff)
			push_changes()
			send_email(all_diff)
		else:
			p('No changes found')

def help():
	print ''
	print 'mysql_mon.py [--mode <mode>] [--skip-schema-audit] [--skip-user-audit] [--skip-variables-audit]'
	print ''
	print '--mode=config_file (Default). It will read the servers list from the beggining of the script.'
	print '--mode=aws It will read the servers list from a given AWS tag.'
	print '--skip-XXXX-audit will skip the audit of schema, user or variables. For databases with a big number of tables it might be necessary to skipt schema audit.'
	print ''


if __name__ == '__main__':
	#mode can be config_file (default) or AWS
	mode="config_file"

	#parsing arguments
	try:
		opts, args = getopt.getopt(sys.argv[1:],"h",["help","mode=","skip-schema-audit","skip-user-audit","skip-variables-audit"])
	except getopt.GetoptError:
		help()
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			help()
			sys.exit()
		elif opt in ("-m", "--mode"):
			mode = arg
		elif opt in ("--skip-schema-audit"):
			skip_audits["skip-schema-audit"]=1
		elif opt in ("--skip-user-audit"):
			skip_audits["skip-user-audit"]=1
		elif opt in ("--skip-variables-audit"):
			skip_audits["skip-variables-audit"]=1

	p('Running MySQL Metadata Audit in '+mode+' mode')
	if len(skip_audits)>0:
		p('Skipping the following audits: '+', '.join(skip_audits.keys()))

	if mode == 'aws':
		get_aws_instances()
		mysql_host_list = aws_server_list

	run_diff(mysql_host_list)

	p('Bye!')
