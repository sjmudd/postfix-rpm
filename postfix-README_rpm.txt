This RPM uses the standard Postfix installation paths:

	1. config files in compiled-in default /etc/postfix/
	2a commands in /usr/sbin/
        2b daemons in /usr/libexec/postfix/
        2c newaliases and mailq in /usr/bin/
	3. spool queue in /var/spool/postfix/, set up to be the root for
	   clients to chroot(2)

Note that assumptions (2) and (3) are specified in
/etc/postfix/main.cf. By editing that file you can change all _kinds_
of useful things about the way Postfix works and where it looks for
things and so on. The favourite parameters to frob are included in that
file, with comments describing them; the authoritative documentation for
all possible parameters is available in the man page mail_params(3H);
to read it type

	man 3H mail_params

This rpm installs a userID "postfix", with UID and GID 89, if there isn't
already a "postfix" user in /etc/passwd. It doesn't try and search for
an ``available'' UID; if 89 is already taken on your system, and there
isn't a "postfix" user already installed, then the installation fails.

During installation and removal such actions as creating or deleting the
postfix userID in /etc/passwd generate commentary via logger(1) with syslog.
In a standard RedHat system this will be recorded in /var/log/maillog.
The following command should extract them:

	grep postfix-rpm /var/log/maillog

