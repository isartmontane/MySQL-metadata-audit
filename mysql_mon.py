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
import ConfigParser
import json

config = ConfigParser.ConfigParser()
config.read('config.cfg')

##MySQL user/password used to get the MySQL metadata
mysql_user=config.get('Defaults', 'mysql_user')
mysql_password=config.get('Defaults', 'mysql_user')
#

##Used only on config_file mode
mysql_host_list=json.loads(config.get('Defaults', 'mysql_host_list'))[0]
#
##Used only on AWS mode. We will query AWS and filter all the servers that have the tag Role=mysql
aws_tag_name=config.get('Defaults', 'aws_tag_name')
aws_tag_value=config.get('Defaults', 'aws_tag_value')

#
##Where to send the changes
mail_to=config.get('Defaults', 'mail_to')
mail_from=config.get('Defaults', 'mail_from')

#the following variables will be excluded from the diff. It should be a valid egrep expression
mysql_exclude_var=config.get('Defaults','mysql_exclude_var')

#Where do you have your repo?
repo_dir=config.get('Defaults','repo_dir')

#############################################################################
## Do not change anything below this line unless you know what you are doing
#############################################################################

DEBUG=False
#DEBUG=True

import os
import subprocess 
import time
import sys
import getopt 
import smtplib
import string
import datetime
from email.mime.text import MIMEText

aws_server_list={}
skip_audits={}
now=datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
summary_text=[]

def p(string,debug_v=1):
	if DEBUG and debug_v>1:
		print string;
	if DEBUG and debug_v==1:
		print string;

def dump_schema(tag,mysql_host):
	p('\tDumping DB schema ...')
	diff_text=''
	file_name='schema.'+tag+'.'+mysql_host+'.'+now
	dst_file = repo_dir+'/'+file_name
	os.system('mysqldump -R --skip-dump-date -d -u'+mysql_user+' -p'+mysql_password+' -h'+mysql_host+' -A|sed -r "s/ AUTO_INCREMENT=[0-9]+ / /g" >>'+dst_file)

def get_mysql_variables(tag,mysql_host):
	p('\tChecking variables ...')
	file_name='variables.'+tag+'.'+mysql_host+'.'+now
	dst_file = repo_dir+'/'+file_name
	cmd = 'mysql -u'+mysql_user+' -p'+mysql_password+' -h'+mysql_host+' -e"show variables"|egrep -v '+mysql_exclude_var+'>'+dst_file
	p(cmd,10)
	os.system(cmd)

def get_user_permissions(tag,mysql_host):
	p('\tChecking user permissions ...')
	file_name='users.'+tag+'.'+mysql_host+'.'+now
	dst_file = './'+file_name
	cmd = 'mysql -u'+mysql_user+' -p'+mysql_password+' -h'+mysql_host+' -e"select concat(\\"show grants for \'\\",user,\\"\'@\'\\",host,\\"\'\\") from mysql.user"'
	
	p(cmd,10)
	pr = subprocess.Popen(cmd , cwd = repo_dir, shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE )
	(out, error) = pr.communicate()

	if error:
		print error 

	for user_grant in out.splitlines():
		cmd = 'mysql -u'+mysql_user+' -p'+mysql_password+' -h'+mysql_host+' -e"'+user_grant+'" >>'+dst_file
		p(cmd,10)
		pr = subprocess.Popen(cmd , cwd = repo_dir, shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE )
		(out, error) = pr.communicate()

		if error:
			print error 

def send_email(text):
	p('Sending email!')
	msg =  MIMEText(text, 'plain')
	msg['Subject'] = 'MySQL-metadata-audit: Changes found.'
	msg['From'] = mail_from
	msg['To'] = mail_to

	# Send the message via our own SMTP server, but don't include the
	# envelope header.
	s = smtplib.SMTP('localhost')
	s.sendmail(mail_from, [mail_to], msg.as_string())
	s.quit()

def get_diff(what_to_diff, tag):
	cmd="file=$(ls "+what_to_diff+"."+tag+".* -rt|tail -2);diff $file"
	p(cmd,10)
	pr = subprocess.Popen(cmd , cwd = repo_dir, shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE )
	(out, error) = pr.communicate()
	if error:
		p("Couldn't run diff, probably first run.\n"+error)
	if out:
		p("\tDifferences found for server {}".format(tag))
		p(out)
		summary_text.append("\n\nDifferences on {} for server {}:\n{}".format(what_to_diff,tag,out))

def get_aws_instances():
	p('Getting servers from AWS')
	server_list = []
	pr = subprocess.Popen('aws ec2 describe-instances --filter Name=tag:'+aws_tag_name+',Values='+aws_tag_value+' --query "Reservations[].Instances[].[State.Name,Tags,PublicDnsName]"', cwd = repo_dir, shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE )
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
	if not os.path.exists(repo_dir):
	    os.makedirs(repo_dir)
	all_diff=''
	for tag, mysql_host in mysql_host_list.iteritems():
		p('Checking the following servers: {} ({}) '.format(tag,mysql_host))
		if "skip-variables-audit" not in skip_audits:
		        get_mysql_variables(tag,mysql_host)
			get_diff("variables",tag)
		if "skip-user-audit" not in skip_audits:
			get_user_permissions(tag,mysql_host)
			get_diff("users",tag)
		if "skip-schema-audit" not in skip_audits.keys():
			dump_schema(tag,mysql_host)
			get_diff("schema",tag)
	print '\n'.join(summary_text)
	if len(summary_text)>1:
		send_email('\n'.join(summary_text))

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
