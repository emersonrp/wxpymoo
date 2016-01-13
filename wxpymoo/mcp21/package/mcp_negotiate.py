package WxMOO::MCP21::Package::mcp_negotiate;
use strict;
use warnings;
use v5.14;

no if $] >= 5.018, warnings => "experimental::smartmatch";

use WxMOO::MCP21;
use parent 'WxMOO::MCP21::Package';

sub new {
    my ($class) = @_;
    my $self = $class->SUPER::new({
        package   => 'mcp-negotiate',
        min       => '2.0',
        max       => '2.0',
        activated => '2.0',
    });

    $WxMOO::MCP21::registry->register($self, qw( mcp-negotiate-can mcp-negotiate-end ));
    bless $self, $class;
}

sub _init {
    for my $p ($WxMOO::MCP21::registry->packages) {
        next if $p->package eq 'mcp';
        WxMOO::MCP21::server_notify("mcp-negotiate-can", {
            'package'     => $p->package,
            'min-version' => $p->min,
            'max-version' => $p->max,
        });
    }
    WxMOO::MCP21::server_notify('mcp-negotiation-end');
}

sub dispatch {
    my ($self, $message) = @_;
    given ($message->{'message'}) {
        when (/mcp-negotiate-can/) { $self->do_mcp_negotiate_can($message); }
        when (/mcp-negotiate-end/) { $self->do_mcp_negotiate_end; }
    }
}


sub do_mcp_negotiate_can {
    my ($self, $message) = @_;
    my $data = $message->{'data'};
    my $min = $data->{'min-version'};
    my $max = $data->{'max-version'};
    my $pkg = $data->{'package'};
    if (my $ver = $WxMOO::MCP21::registry->get_best_version($pkg, $min, $max)) {
        WxMOO::MCP21::debug("activating $pkg");
        $WxMOO::MCP21::registry->get_package($pkg)->activated($ver);
    }
}

sub do_mcp_negotiate_end {
    # TODO - do we need to do anything?  maybe like unregister packages that aren't activated?
}

1;
