package WxMOO::MCP21::Package;
use strict;
use warnings;
use v5.14;

use Wx;
use parent "Class::Accessor";
use parent -norequire, "Wx::EvtHandler";
WxMOO::MCP21::Package->mk_accessors( qw( package min max message callback activated ) );

sub new {
    my ($class, $args) = @_;
    my $self = Wx::EvtHandler->new;
    while (my($k, $v) = each %$args) {
        $self->{$k} = $v;
    }
    bless $self, $class;
}

sub _init { }

1;
