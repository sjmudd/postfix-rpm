Security: writable versus protected maildrop directory
======================================================

By default, Postfix uses a world-writable, sticky, mode 1733 maildrop
directory where local users can submit mail. This approach avoids the
need for set-uid or set-gid software. Mail can be posted even while
the mail system is down.  Queue files in the maildrop directory have no
read/write/execute permission for other users.  The maildrop directory
is not used for mail received via the network.

With directory world write permission come opportunities for annoyance:
a local user can make hard links to someone else's maildrop files so
they don't go away and may be delivered multiple times; a local user can
fill the maildrop directory with junk and try to crash the mail system;
and a local user can hard link someone else's files into the maildrop
directory and try to have them delivered as mail.  However, Postfix
queue files have a specific format; less than one in 10^12 non-Postfix
files would be recognized as a valid Postfix queue file.

On systems with many users it may be desirable to revoke maildrop
directory world write permission, and to enable set-gid privileges
on a small "postdrop" command that is provided for this purpose.

In order to revoke world-write permission, create a group "maildrop"
that is unique and that does not share its group ID with any other user,
certainly not with the postfix account, then execute the following
commands to make "postdrop" set-gid, and to make maildrop non-writable
for unprivileged users:

    # chgrp maildrop /var/spool/postfix/maildrop /var/spool/postdrop
    # chmod 730 /var/spool/postfix/maildrop
    # chmod 2755 /var/spool/postdrop

The sendmail posting program will automatically invoke the postdrop
command when maildrop directory write permission is restricted.

You may also wish to update commands in /etc/postfix/postfix-script that
create a missing maildrop directory. Delete the line starting with `-',
and insert the lines starting with `+'.

	    test -d maildrop || {
		    $WARN creating missing Postfix maildrop directory
		    mkdir maildrop || exit 1
    -               chmod 1733 maildrop
    +               chmod 730 maildrop
		    chown $mail_owner maildrop
    +               chgrp maildrop maildrop
	    }
	    test -d pid || {
		    $WARN creating missing Postfix pid directory
