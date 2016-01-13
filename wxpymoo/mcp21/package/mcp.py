package WxMOO::MCP21::Package::mcp;
use strict;
use warnings;
use v5.14;

no if $] >= 5.018, warnings => "experimental::smartmatch";

use WxMOO::MCP21;
use parent 'WxMOO::MCP21::Package';

sub new {
    my ($class) = @_;
    my $self = $class->SUPER::new({
        activated => 1,
        package   => 'mcp',
        min       => 2.1,
        max       => 2.1,
    });

    $WxMOO::MCP21::registry->register($self, qw(mcp));
}

sub dispatch {
    my ($self, $message) = @_;
    given ($message->{'message'}) {
        when ( /mcp/ ) { $self->do_mcp($message); }
    }
}

### handlers
sub do_mcp {
    my ($self, $args) = @_;

    if ($args->{'data'}->{'version'}+0 == 2.1 or $args->{'data'}->{'to'}+0 >= 2.1) {
        $WxMOO::MCP21::mcp_active = 1;
    } else {
        WxMOO::MCP21::debug("mcp version doesn't match, bailing");
        return;
    }

    # we both support 2.1 - ship the server a key and start haggling
    my $key = $WxMOO::MCP21::mcp_auth_key = $$;
    $WxMOO::MCP21::connection->Write("#\$#mcp authentication-key: $key version: 2.1 to: 2.1\n");
    WxMOO::MCP21::debug("C->S: #\$#mcp authentication-key: $key version: 2.1 to: 2.1");

    WxMOO::MCP21::start_mcp();

}

sub do_splat {
    # all taken care of in MCP21.pm
}

sub do_colon {
    # all taken care of in MCP21.pm
}

1;
