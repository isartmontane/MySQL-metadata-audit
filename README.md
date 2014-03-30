# MySQL Metadata Audit

## What is it?

MySQL Metadata Audit used to be a python version of (dbRecorder)[http://www.wave2.org/w2wiki/dbRecorder], but now there's some more features. It's intended to notify via email when:

+ There are schema changes on any of your tables.
+ There are variable changes.
+ There are user permission changes (or new users).

The latest version of MySQL Metadata Audit is able to read servers from config file or from an AWS tag (i.e. all servers with tag A will be audited)

## Installation

## Prerequisites

You will need a working GIT repository. If you don't know how to create one, Google for it.

### Debian / Ubuntu

			apt-get install python python-git python-mysqldb

### RH / CentOS / Fedora

			yum ??

## Getting the code

get the latest version from github 

			http://github.com/isartmontane/MySQL-metadata-audit			

## Create a MySQL user

		GRANT SELECT, LOCK TABLES ON *.* TO 'user'@'host' IDENTIFIED BY 'password';

##Edit mysql_mon.py and change the configuration variables.
MySQL user, servers and destination email will be the minimum required. 

If you are using AWS tags to audit your servers you will also need to change aws_tag_name AND aws_tag_value.

## From now on you just need to run mysql_mon without any params

		python mysql_mon.py	

### If you are using AWS tags you will need to run the app with "--mode aws"

			python mysql_mon.py --mode aws

## If you want to run it every day (recommended), just edit the mysql_mon.cron and then copy it to /etc/cron.d

		vim mysql_mon.cron

		cp mysql_mon.cron /etc/cron.d/

## Example runs

### config file mode

		$ python mysql_mon.py
			Running MySQL Metadata Audit in config_file mode
			Checking the following servers: 2myServer.mydomain.com, 5myServer.mydomain.com, 1myServer.mydomain.com, 3myServer.mydomain.com, 4myServer.mydomain.com, 6myServer.mydomain.com
				Checking existing git directory...
			Host - 2myServer.mydomain.com:
				Checking variables ...
				Checking user permissions ...
					show grants for 'isart'@'%'
					show grants for 'isart'@'127.0.0.1'
					show grants for 'root'@'127.0.0.1'
					show grants for 'root'@'::1'
					show grants for 'debian-sys-maint'@'localhost'
					show grants for 'root'@'localhost'
				Dumping DB schema ...
			Host - 5myServer.mydomain.com:
				Checking variables ...
				Checking user permissions ...
					show grants for 'isart'@'%'
					show grants for 'isart'@'127.0.0.1'
					show grants for 'root'@'127.0.0.1'
					show grants for 'root'@'::1'
					show grants for 'debian-sys-maint'@'localhost'
					show grants for 'root'@'localhost'
				Dumping DB schema ...
			Host - 1myServer.mydomain.com:
				Checking variables ...
				Checking user permissions ...
					show grants for 'isart'@'%'
					show grants for 'isart'@'127.0.0.1'
					show grants for 'root'@'127.0.0.1'
					show grants for 'root'@'::1'
					show grants for 'debian-sys-maint'@'localhost'
					show grants for 'root'@'localhost'
				Dumping DB schema ...
			Host - 3myServer.mydomain.com:
				Checking variables ...
				Checking user permissions ...
					show grants for 'isart'@'%'
					show grants for 'isart'@'127.0.0.1'
					show grants for 'root'@'127.0.0.1'
					show grants for 'root'@'::1'
					show grants for 'debian-sys-maint'@'localhost'
					show grants for 'root'@'localhost'
				Dumping DB schema ...
			Host - 4myServer.mydomain.com:
				Checking variables ...
				Checking user permissions ...
					show grants for 'isart'@'%'
					show grants for 'isart'@'127.0.0.1'
					show grants for 'root'@'127.0.0.1'
					show grants for 'root'@'::1'
					show grants for 'debian-sys-maint'@'localhost'
					show grants for 'root'@'localhost'
				Dumping DB schema ...
			Host - 6myServer.mydomain.com:
				Checking variables ...
				Checking user permissions ...
					show grants for 'isart'@'%'
					show grants for 'isart'@'127.0.0.1'
					show grants for 'root'@'127.0.0.1'
					show grants for 'root'@'::1'
					show grants for 'debian-sys-maint'@'localhost'
					show grants for 'root'@'localhost'
				Dumping DB schema ...
			New file found: schema.1myServer.mydomain.com
			New file found: schema.2myServer.mydomain.com
			New file found: schema.3myServer.mydomain.com
			New file found: schema.4myServer.mydomain.com
			New file found: schema.5myServer.mydomain.com
			New file found: schema.6myServer.mydomain.com
			New file found: users.1myServer.mydomain.com
			New file found: users.2myServer.mydomain.com
			New file found: users.3myServer.mydomain.com
			New file found: users.4myServer.mydomain.com
			New file found: users.5myServer.mydomain.com
			New file found: users.6myServer.mydomain.com
			New file found: variables.1myServer.mydomain.com
			New file found: variables.2myServer.mydomain.com
			New file found: variables.3myServer.mydomain.com
			New file found: variables.4myServer.mydomain.com
			New file found: variables.5myServer.mydomain.com
			New file found: variables.6myServer.mydomain.com
			Changes found:
			
			schema.1myServer.mydomain.com, schema.2myServer.mydomain.com, schema.3myServer.mydomain.com, schema.4myServer.mydomain.com, schema.5myServer.mydomain.com, schema.6myServer.mydomain.com, users.1myServer.mydomain.com, users.2myServer.mydomain.com, users.3myServer.mydomain.com, users.4myServer.mydomain.com, users.5myServer.mydomain.com, users.6myServer.mydomain.com, variables.1myServer.mydomain.com, variables.2myServer.mydomain.com, variables.3myServer.mydomain.com, variables.4myServer.mydomain.com, variables.5myServer.mydomain.com, variables.6myServer.mydomain.com
			Pushing changes to repo
			Sending email!
	

### AWS mode

		$ python mysql_mon.py
			Running MySQL Metadata Audit in AWS mode 
			Checking the following servers: 1myServer.mydomain.com, 2myServer.mydomain.com
			Checking existing git directory...
			Host - 1myServer.mydomain.com:
				Checking variables ...
				Checking user permissions ...
					show grants for 'isart'@'%'
					show grants for 'isart'@'127.0.0.1'
					show grants for 'root'@'127.0.0.1'
					show grants for 'root'@'::1'
					show grants for 'debian-sys-maint'@'localhost'
					show grants for 'root'@'localhost'
				Dumping DB schema ...
			Host - 2myServer.mydomain.com:
				Checking variables ...
				Checking user permissions ...
					show grants for 'isart'@'%'
					show grants for 'isart'@'127.0.0.1'
					show grants for 'root'@'127.0.0.1'
					show grants for 'root'@'::1'
					show grants for 'debian-sys-maint'@'localhost'
					show grants for 'root'@'localhost'
				Dumping DB schema ...
			New file found: schema.1myServer.mydomain.com
			New file found: schema.2myServer.mydomain.com
			New file found: users.1myServer.mydomain.com
			New file found: users.2myServer.mydomain.com
			New file found: variables.1myServer.mydomain.com
			New file found: variables.2myServer.mydomain.com
			Changes found:
			
			schema.1myServer.mydomain.com, schema.2myServer.mydomain.com, users.1myServer.mydomain.com, users.2myServer.mydomain.com, variables.1myServer.mydomain.com, variables.2myServer.mydomain.com
			Pushing changes to repo
			Sending email!

			
## Older versions
Older versions of MySQL Metadata Audit supported SVN instead of GIT. That's not supported anymore on the newest versions. If you still use SVN you can grap an older version and give it a go, but you won't benefit of the new features.

## Changelog
	see changelog
## Comments & author
Feel free to contact me if you have any question, feature requests or you have found a bug.
Isart Montane Mogas <isart.montane@gmail.com>

