--- snapshot-20020107/INSTALL.sh.orig	2002/01/07 02:03:21
+++ snapshot-20020107/INSTALL.sh	2002/01/07 06:51:06
@@ -194,28 +199,48 @@
 # Do not destroy parameter settings from environment or command line.

 for name in daemon_directory command_directory queue_directory mail_owner \
-    setgid_group sendmail_path newaliases_path mailq_path manpage_path
+    sendmail_path newaliases_path mailq_path
 do
     eval : \${$name=\`bin/postconf $conf -h $name\`} || kill $$
 done

 # Grandfathering: if not in main.cf, get defaults from obsolete install.cf file.
+
+# XXX: We rely on 'postconf -n' listing main.cf variables even if equal
+# to their default values. This is consistent with the implementation,
+# but is not explicit in the documentation. Perhaps 'postconf -n'
+# documentation should explicitly specify the current behaviour. If the
+# implementation is changed to only show "actual" non-default values,
+# this code will need to change. (A '-N' option which implements the
+# current semantics might then be useful.)
+#
+conf="-c $CONFIG_DIRECTORY -n -h"
+: ${setgid_group=`bin/postconf $conf setgid_group 2>/dev/null`}
+: ${manpage_path=`bin/postconf $conf manpage_path 2>/dev/null`}

-grep setgid_group $CONFIG_DIRECTORY/main.cf >/dev/null 2>&1 || {
+if [ -z "$setgid_group" -o -z "$manpage_path" ]
+then
     if [ -f $CONFIG_DIRECTORY/install.cf ]
     then
 	. $CONFIG_DIRECTORY/install.cf
-	setgid_group=${setgid-$setgid_group}
-	manpage_path=${manpages-$manpage_path}
-    elif [ -n "$non_interactive" ]
+	: ${setgid_group=$setgid}
+	: ${manpage_path=$manpages}
+    fi
+fi
+
+if [ -z "$setgid_group" -o -z "$manpage_path" ]
+then
+    if [ -n "$non_interactive" ]
     then
 	echo Error: \"make upgrade\" requires the $CONFIG_DIRECTORY/main.cf 1>&2
 	echo file from a sufficiently recent Postfix installation. 1>&2
 	echo 1>&2
+	echo For automated builds set \"setgid_group\" in the environment. 1>&2
+	echo OR 1>&2
 	echo Use \"make install\" instead. 1>&2
 	exit 1
     fi
-}
+fi

 # Override default settings.

@@ -331,7 +356,7 @@
 	compare_or_replace a+r,go-w conf/$file $CONFIG_DIRECTORY/$file || exit 1
     done
 else
-    for file in `cd conf; censored_ls * | grep -v postfix-script`
+    for file in `cd conf; censored_ls | grep -v postfix-script`
     do
 	compare_or_replace a+r,go-w conf/$file $CONFIG_DIRECTORY/$file || exit 1
     done
@@ -361,7 +386,7 @@
 for dir in man?
     do test -d $MANPAGE_PATH/$dir || mkdir -p $MANPAGE_PATH/$dir || exit 1
 done
-for file in `censored_ls man?/*`
+for file in `censored_ls -d man?/*`
 do
     (test -f $MANPAGE_PATH/$file && cmp -s $file $MANPAGE_PATH/$file &&
      echo Skipping $MANPAGE_PATH/$file...) || {

