#What is it?
	MySQL metadata audit is a dbRecorder python port that tries to keep it simple: 
		- Notify via email when there are schema changes, variable changes and permission changes.
	If you need more features I recommend you to take a look at dbRecorder home page: http://www.wave2.org/w2wiki/dbRecorder 
#Why port an existing application and not extend dbRecorder?
	There are a few reasons for that:
		- dbRecorder does lots of things I'm not interested on (i.e. chat and XMPP alerts, PostgreSQL compatibility...)
		- It's wrote in Java ... 
		- I like coding!
#Installation
	## Prerequisites
		## You will need a working SVN repository. If you don't know how to create one, take a look at the following link or Google for it.
			http://www.howtoforge.com/apache_subversion_repository

		## Debian / Ubuntu
			apt-get install python python-svn python-mysqldb
		## RH / CentOS / Fedora
			yum ??
	## Code
		get the latest version from github 
			http://github.com/isartmontane/MySQL-metadata-audit			
	## Create a MySQL user
		GRANT SELECT, LOCK TABLES ON *.* TO 'user'@'host' IDENTIFIED BY 'password';
	## Edit mysql_mon.py and change the configuration variables.
	## The first run will require mysql_mon to create the required directory on SVN
		python mysql_mon.py --create
	## From now on you just need to run mysql_mon without any params
		python mysql_mon.py	
	## If you want to run it every day (recommended), just edit the mysql_mon.cron and then copy it to /etc/cron.d
		vim mysql_mon.cron
		cp mysql_mon.cron /etc/cron.d/
# Basic Usage.
	mysql_mon will add into your SVN repository the variables, users and schema of each of the databases defined. 
	It will also notify you via email (or stdout if it's running in Debug mode) if there are changes on the server variables, schema or user grants.
	
	Ideally, mysql_mon needs to run on a daily cron job so you get a daily email when something is changed.

#Comments & author
	Feel free to contact me if you have any question, feature requests or you have found a bug.
	Isart Montane Mogas <isart.montane@gmail.com>
