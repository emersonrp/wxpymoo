package WxMOO::MCP21;
use strict;
use warnings;
use v5.14;

use parent 'Exporter';
our @EXPORT_OK = qw( debug );

use WxMOO::MCP21::Registry;
use WxMOO::Window::DebugMCP;

# This module was developed by squinting directly at both the MCP spec
# at http://www.moo.mud.org/mcp2/mcp2.html and tkMOO-light's plugins/mcp21.tcl
# file, to which this code bears more than a little resemblance and owes
# more than a little debt.

my $PREFIX       = qr/^#\$#/;
my $QUOTE_PREFIX = qr/^#\$"/;

# TODO - these -work- as package-scope vars, but might want some better encapsulation
# later on.  tkmoo has the notion of a request object that it stashes them in.
our $mcp_active = 0;
our $mcp_auth_key = '';
our $connection = '';

# This is probably the right place for this, though.
our $registry = WxMOO::MCP21::Registry->new;
our $multiline_messages = {};

# We'd like to enumerate this automatically.
use WxMOO::MCP21::Package::mcp;
#use WxMOO::MCP21::Package::mcp_cord;
use WxMOO::MCP21::Package::mcp_negotiate;
use WxMOO::MCP21::Package::dns_org_mud_moo_simpleedit;
use WxMOO::MCP21::Package::dns_com_awns_status;

my $pkg_mcp            = WxMOO::MCP21::Package::mcp          ->new;
#my $pkg_mcp_cord       = WxMOO::MCP21::Package::mcp_cord     ->new;
my $pkg_mcp_negotiate  = WxMOO::MCP21::Package::mcp_negotiate->new;
my $pkg_mcp_simpleedit = WxMOO::MCP21::Package::dns_org_mud_moo_simpleedit->new;
my $pkg_mcp_status     = WxMOO::MCP21::Package::dns_com_awns_status->new;

sub debug {
    # TODO - we might want one debug window per-connection-window
    WxMOO::Window::DebugMCP->new->display("@_\n");
}

sub output_filter {
    my ($data) = @_;

    # MCP spec, 2.1:
    # A received network line that begins with the characters #$# is translated
    # to an out-of-band (MCP message) line consisting of exactly the same
    # characters.  A received network line that begins with the characters #$"
    # must be translated to an in-band line consisting of the network line with
    # the prefix #$" removed.  Any other received network line translates to an
    # in-band line consisting of exactly the same characters.

    if (
        (!($data =~ s/$PREFIX//))    # we had no prefix to trim off the front
            or
        ($data =~ s/$QUOTE_PREFIX//) # we had the quote prefix, and trimmed it

    ) { return $data; }

    # now we have only lines that started with $PREFIX, which has been trimmed
    debug("S->C: #\$#$data");

    my ($message_name, $rest) = $data =~ /(\S+)\s*(.*)/;

    if (!$mcp_active and $message_name ne 'mcp') {
        # we haven't started yet, and the message isn't a startup negotiation
        return;
    }

    my $message = {};  # here's where we decode this

    # multi-line message handling.  This is awful.
    if ($message_name eq '*') {
        my ($tag, $field, $value) = ($rest =~ /^(\S*) ([^:]*): (.*)/);
        $message = $multiline_messages->{$tag};
        $message->{'_data-tag'} = $tag;
        push @{$message->{'data'}->{$field}}, $value;
    } elsif ($message_name eq ':') {
        my ($tag) = ($rest =~ /^(\S+)/);
        $message = $multiline_messages->{$tag};
        delete $message->{'multi_in_progress'};
    } else {
        $message = parse($rest);
    }

    # check auth
    if (($message_name ne '*')   and
        ($message_name ne 'mcp') and
        ($message->{'auth_key'} ne $mcp_auth_key)
    ) {
        debug("mcp - auth failed");
        return;
    }

    $message->{'message'} //= $message_name;

    if ($message->{'multi_in_progress'}) {
        $multiline_messages->{$message->{'_data-tag'}} ||= $message;
    } else {
        # don't dispatch multilines in progress
        dispatch($message);
    }

    # always return undef so the output widget skips this line
    return;
}

my $simpleChars = q|[-a-z0-9~`!@#$%^&*()=+{}[\]\|';?/><.,]|;

sub parse {
    my ($raw) = @_;

    return unless $raw;
    my ($first) = split /\s+/, $raw;
    my $message = {};

    if ($first !~ /:$/) {
        $message->{'auth_key'} = $first;
        $raw =~ s/^$first\s+//;
    }
    while ($raw =~ /([-_*a-z0-9]+)              # keyword
                        :                       # followed by colon
                        \s+                     # some space
                        (                       # and either
                            (?:"[^"]*")         # a quoted string - TODO - the grammar is more picky than [^"]
                            |                   # or
                            (?:$simpleChars)+   # a value
                        )/igx)
    {
        my ($keyword, $value) = ($1, $2);
        if ($keyword =~ s/\*$//) {
            $message->{'data'}->{$keyword} = [];
            $message->{'multi_in_progress'} = 1;
        } elsif ($keyword eq '_data-tag') {
            $message->{'_data-tag'} = $value;
        } else {
            $message->{'data'}->{$keyword} = $value;
        }
    }
    return $message;
}

sub dispatch {
    my ($message) = @_;

    my $package = $registry->package_for_message($message->{'message'}) or return;

    $package->dispatch($message) if $package->activated;
}


sub server_notify {
    my ($msg, $args) = @_;


    my $key = $WxMOO::MCP21::mcp_auth_key;

    my $out = "#\$#$msg $key ";

    my ($multiline, $datatag);
    while (my ($k, $v) = each %$args) {
        # TODO escape $v if needed
        $v //= '';
        if (ref $v) { # multiline!
            $multiline->{$k} = $v;
            $datatag = int(rand(1000000));
            $out .= qq|$k*: "" _data-tag: $datatag |;
        } else {
            $out .= "$k: $v ";
        }
    }
    debug("C->S: $out");
    $connection->Write("$out\n");

    if ($multiline) {
        while (my ($k, $l) = each %$multiline) {
            for my $line (@$l) {
                $connection->Write("#\$#* $datatag $k: $line\n");
                debug("#\$#* $datatag $k: $line");
            }
            $connection->Write("#\$#: $datatag\n");
            debug("#\$#: $datatag");
        }
    }
}

sub new_connection { $connection = shift; }

sub start_mcp {
    for my $p ($registry->packages) { $p->_init; }
}

1;
