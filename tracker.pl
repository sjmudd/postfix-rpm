##
##  openpkg -- OpenPKG Tool Chain
##  Copyright (c) 2003-2004 The OpenPKG Project <http://www.openpkg.org/>
##  Copyright (c) 2003-2004 Ralf S. Engelschall <rse@engelschall.com>
##  Copyright (c) 2003-2004 Cable & Wireless <http://www.cw.com/>
##
##  Permission to use, copy, modify, and distribute this software for
##  any purpose with or without fee is hereby granted, provided that
##  the above copyright notice and this permission notice appear in all
##  copies.
##
##  THIS SOFTWARE IS PROVIDED ``AS IS'' AND ANY EXPRESSED OR IMPLIED
##  WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
##  MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
##  IN NO EVENT SHALL THE AUTHORS AND COPYRIGHT HOLDERS AND THEIR
##  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
##  SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
##  LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
##  USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
##  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
##  OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
##  OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
##  SUCH DAMAGE.
##
##  cmd/tracker.pl: OpenPKG Vendor Source Tracking Report Generator
##
##  Modified by Simon J Mudd for use with his own Postfix RPM builds
##

require 5;
use Getopt::Long;
use IO;
use strict;

#   program information
my $progname = "tracker";
my $progvers = "2.0.0-sjm";

#   parameters (defaults)
my $version  = 0;
my $verbose  = 0;
my $help     = 0;
my $tmpdir   = ($ENV{TMPDIR} || "/tmp");
my $rpm      = 'rpm';
my $vcheck   = './vcheck';
my $sendmail = '/usr/sbin/sendmail';
my $address  = '';
my $sender   = 'sjmudd@nl.wl0.org';

#   exception handling support
$SIG{__DIE__} = sub {
    my ($err) = @_;
    $err =~ s|\s+at\s+.*||s if (not $verbose);
    print STDERR "$progname:ERROR: $err ". ($! ? "($!)" : "") . "\n";
    exit(1);
};
#   command line parsing
Getopt::Long::Configure("bundling");
my $result = GetOptions(
    'V|version'     => \$version,
    'v|verbose'     => \$verbose,
    'h|help'        => \$help,
    't|tmpdir=s'    => \$tmpdir,
    'r|rpm=s'       => \$rpm,
    'c|vcheck=s'    => \$vcheck,
    's|sendmail=s'  => \$sendmail,
    'a|address=s'   => \$address,
) || die "option parsing failed";
if ($help) {
    print "Usage: $progname [options] [SPECFILE ...]\n" .
          "Available options:\n" .
          " -v,--verbose           enable verbose run-time mode\n" .
          " -h,--help              print out this usage page\n" .
          " -t,--tmpdir=PATH       filesystem path to temporary directory\n" .
          " -r,--rpm=FILE          filesystem path to RPM program\n" .
          " -a,--address=ADDRESS   send to ADDRESS (default stdout)\n" .
          " -V,--version           print program version\n" .
    exit(0);
}
if ($version) {
    print "MODIFIED OpenPKG $progname $progvers\n";
    exit(0);
}

#   verbose message printing
sub msg_verbose {
    my ($msg) = @_;
    print STDERR "$msg\n" if ($verbose);
}

#   warning message printing
sub msg_warning {
    my ($msg) = @_;
    print STDERR "$progname:WARNING: $msg\n";
}

#   error message printing
sub msg_error {
    my ($msg) = @_;
    print STDERR "$progname:ERROR: $msg\n";
}

#   determine vcheck(1) path
if ($vcheck eq '') {
    $vcheck = `$rpm --eval '%{l_vcheck}'`;
    $vcheck =~ s|^\s+||s;
    $vcheck =~ s|\s+$||s;
    die "no path to vcheck(1) known"
        if ($vcheck eq '');
}

#   sanity check .spec files
die "no .spec files given" if (@ARGV == 0);
my @specs = ();
foreach my $spec (@ARGV) {
    die "invalid .spec filename \"$spec\""
        if ($spec !~ m/^(.+\/)?([^\/]+)\.spec\.in$/);
    die ".spec file \"$spec\" not found"
        if (! -f $spec);
    push(@specs, $spec);
}

#   sanity check address
#   - it can be empty (then we output to stdout)
if ($address ne '') {
    # if ($address !~ m|^[^@]+\@[^@.]+(\.[^@.])+$|) {
    #     die "invalid recipient mail address $address";
    # }
}

#   statistics
my $s_pkg = 0;
my $s_src = 0;
my $s_new = 0;
my $s_err = 0;
my $s_rem = 0;
my $t_prepare = 0;
my $t_track   = 0;
my $t_report  = 0;

#   assemble all-in-one vcheck(1) configuration
msg_verbose("++ preparing vcheck(1) configuration");
my $t_prepare = time();
my $vc = '';
$vc .= "config = {\n}\n";
foreach my $spec (@specs) {
    msg_verbose("   -- processing \"$spec\"");
#    my $io = new IO::File "$rpm --track-dump $spec 2>&1 |"
#        or die "unable to extract \"%track\" section from \"$spec\": $!";
    # take vc name from specfile name
    my $file = $spec;
    $file =~ s|\.in$|.vc|;
    my $io = new IO::File $file
        or die "unable to extract info from $file: $!";
    $vc .= $_ while (<$io>);
    $io->close();
    $s_pkg++;
}
$t_prepare = (time() - $t_prepare);

#   run vcheck(1) to perform tracking    
msg_verbose("++ running vcheck(1) for determining new versions");
my $t_track = time();
my $io = new IO::File ">$tmpdir/tracker.vc"
    or die "unable to write \"$tmpdir/tracker.vc\": $!";
$io->print($vc);
$io->close();
unlink("$tmpdir/tracker.out");
system("$vcheck --plain --no-update -f $tmpdir/tracker.vc 2>&1 | tee $tmpdir/tracker.out");

my $out = '';
$io = new IO::File "<$tmpdir/tracker.out"
    or die "unable to read \"$tmpdir/tracker.out\": $!";
$out .= $_ while (<$io>);
$io->close();
unlink("$tmpdir/tracker.out");
unlink("$tmpdir/tracker.vc");

$t_track = (time() - $t_track);

#   start reporting
my $t_report = time();

#   determine last known versions
my $O = {};
my $C = {};
my $cfg = $vc;
$cfg =~ s|\nprog\s+(\S+)\s+=\s*\{(.+?)\}|&do_cfg($1, $2), ''|sge;
sub do_cfg {
    my ($pkg, $cfg) = ($1, $2);
    if ($cfg =~ m|version\s+=\s+(\S+)|s and $cfg !~ m|disabled\s*\n|s) {
        $O->{$pkg} = $1;
        $s_src++;
        if ($cfg =~ m|comment\s+=\s+"([^"]*)"|s) {
            $C->{$pkg} = $1;
        }
        else {
            $C->{$pkg} = "";
        }
    }
}

#   determine new versions
my $N = {};
foreach my $line (split(/\n/, $out)) {
    if ($line =~ m|^Checking for (\S+)\.\.\.\s+(.+)$|) {
        my ($pkg, $report) = ($1, $2);
        if ($report =~ m|new version:\s+(\S+)\.\s*$|) {
            $N->{$pkg} = $1;
            $s_new++;
        }
        elsif ($report =~ m|(\S+)\s+remains latest version\.\s*$|) {
            $N->{$pkg} = $1;
            $s_rem++;
        }
        else {
            $N->{$pkg} = "ERROR: ". $report;
            $s_err++;
        }
    }
}

#   end reporting
$t_report = (time() - $t_report);

#   generate report
my $R = '';
my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time());
my $rtime = sprintf("%04d-%02d-%02d %02d:%02d", 1900+$year, $mon+1, $mday, $hour, $min);
my $ttime = sprintf("%d:%02d:%02d (H:M:S)", $t_track/(60*60), ($t_track%(60*60))/60, ($t_track%(60*60))%60);

if ($address ne '') {
    $R .= sprintf("From: Postfix RPM Version Tracker <%s>\n", $sender);
    $R .= sprintf("Subject: [Postfix RPM] Version Tracking Report ($rtime) - $s_new new source(s)\n");
    $R .= sprintf("To: $address\n");
}
$R .= sprintf("\n");
$R .= sprintf(" Postfix RPM Version Tracking Report\n");
$R .= sprintf(" ===================================\n");
$R .= sprintf("\n");
$R .= sprintf(" Reporting Time:    $rtime\n");
$R .= sprintf(" Tracking Duration: $ttime\n");
$R .= sprintf(" Tracking Input:    $s_src sources ($s_pkg sources)\n");
$R .= sprintf(" Tracking Result:   $s_rem up-to-date, $s_new out-dated, $s_err error\n");
$R .= sprintf("\n");
$R .= sprintf(" The following $s_new sources were determined to be out-dated because newer\n");
$R .= sprintf(" vendor versions were found. Upgrade the corresponding sources.\n");
$R .= sprintf("\n");
$R .= sprintf(" ".("-"x25)." ".("-"x25)." ".("-"x25)."\n");
$R .= sprintf(" %-25s %-25s %-25s\n", "Source", "Old Version", "New Version");
$R .= sprintf(" ".("-"x25)." ".("-"x25)." ".("-"x25)."\n");
my $FN = '';
my $fn = 1;
foreach my $pkg (sort(keys(%{$O}))) {
    if (($O->{$pkg} ne $N->{$pkg}) and ($N->{$pkg} !~ m|^ERROR:|s)) {
        my $new = $N->{$pkg};
        if ($C->{$pkg} ne '') {
            my $x = sprintf(" [%d]", $fn);
            $new = substr(sprintf("%-25s", $new), 0, 25-length($x)).$x;
            $FN .= sprintf(" [%d] %s: %s\n", $fn, $pkg, $C->{$pkg});
            $fn++;
        }
        $R .= sprintf(" %-25s %-25s %s\n", $pkg, $O->{$pkg}, $new);
    }
}
$R .= sprintf(" ".("-"x25)." ".("-"x25)." ".("-"x25)."\n");
$R .= $FN;
$R .= sprintf("\n");
$R .= sprintf(" The following $s_err sources could not be successfully checked because\n");
$R .= sprintf(" an error occurred while processing. Keep at least an eye on them.\n");
$R .= sprintf("\n");
$R .= sprintf(" ".("-"x25)." ".("-"x25)." ".("-"x25)."\n");
$R .= sprintf(" %-25s %-25s %-25s\n", "Source", "Old Version", "Error");
$R .= sprintf(" ".("-"x25)." ".("-"x25)." ".("-"x25)."\n");
$FN = '';
$fn = 1;
foreach my $pkg (sort(keys(%{$O}))) {
    if ($N->{$pkg} =~ m|^ERROR:\s+(.*)$|s) {
        my $err = $1;
        if (length($err) > 25) {
            $err = substr($err, 0, 23) . "..";
        }
        if ($C->{$pkg} ne '') {
            my $x = sprintf(" [%d]", $fn);
            $err = substr(sprintf("%-25s", $err), 0, 25-length($x)).$x;
            $FN .= sprintf(" [%d] %s: %s\n", $fn, $pkg, $C->{$pkg});
            $fn++;
        }
        $R .= sprintf(" %-25s %-25s %s\n", $pkg, $O->{$pkg}, $err);
    }
}
$R .= sprintf(" ".("-"x25)." ".("-"x25)." ".("-"x25)."\n");
$R .= $FN;
$R .= sprintf("\n");
$R .= sprintf(" The remaining $s_rem sources were successfully determined to be still\n");
$R .= sprintf(" up to date. No action is required on your part. Just be happy ;)\n");
$R .= sprintf("\n");
$R .= sprintf("                              Postfix RPM Version Tracker\n");
$R .= sprintf("                              sjmudd\@pobox.com\n");

if ($address ne '') {
    $io = new IO::File "|$sendmail -i -f $sender \"$address\""
        or die "failed to open channel to MTA \"$sendmail\"";
    $io->print($R);
    $io->close();
} else {
    print $R;
}

#   die gracefully
exit(0);

