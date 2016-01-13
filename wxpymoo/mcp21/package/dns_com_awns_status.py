package WxMOO::MCP21::Package::dns_com_awns_status;
use strict;
use warnings;
use v5.14;

no if $] >= 5.018, warnings => "experimental::smartmatch";

use parent 'WxMOO::MCP21::Package';

sub new {
    my $class = shift;
    my $self = $class->SUPER::new({
        package => 'dns-com-awns-status',
        min     => '1.0',
        max     => '1.0',
    });

    $WxMOO::MCP21::registry->register($self, qw( dns-com-awns-status ));
    $self->_init;
}

sub _init { }

sub dispatch {
    my ($self, $message) = @_;
    given ($message->{'message'}) {
        when ('dns-com-awns-status') { $self->do_status($message); }
    }
}

sub do_status {
    return;
    use Data::Dumper;
    print STDERR Data::Dumper::Dumper [@_];
}

1;
