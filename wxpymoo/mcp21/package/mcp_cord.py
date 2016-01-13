package WxMOO::MCP21::Package::mcp_cord;
use strict;
use warnings;
use v5.14;

no if $] >= 5.018, warnings => "experimental::smartmatch";

use WxMOO::MCP21;
use parent 'WxMOO::MCP21::Package';

sub new {
    my ($class) = @_;
    my $self = $class->SUPER::new({
        package => 'mcp-cord',
        min     => '1.0',
        max     => '1.0',
    });
    $WxMOO::MCP21::registry->register($self, qw( mcp-cord mcp_cord mcp-cord-open ));
}

sub dispatch {
    my ($self, $message) = @_;
    given ($message->{'message'}) {
        when ( /mcp-cord/ )        { $self->do_mcp_cord($message); }
        when ( /mcp-cord-open/ )   { $self->do_mcp_cord_open($message); }
        when ( /mcp-cord-closed/ ) { $self->do_mcp_cord_closed($message); }
    }
}

sub do_mcp_cord        { WxMOO::MCP21::debug("do_mcp_cord called with @_"        ) }
sub do_mcp_cord_open   { WxMOO::MCP21::debug("do_mcp_cord_open called with @_"   ) }
sub do_mcp_cord_closed { WxMOO::MCP21::debug("do_mcp_cord_closed called with @_" ) }

1;
