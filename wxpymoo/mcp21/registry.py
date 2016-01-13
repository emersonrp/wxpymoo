package WxMOO::MCP21::Registry;
use strict;
use warnings;
use v5.14;

use Carp;

sub new {
    my ($class) = @_;
    bless {
        registry => {},
        packages => {},
    }, $class;
}

sub register {
    my ($self, $package, @messages) = @_;
    unless ($package->isa('WxMOO::MCP21::Package')) {
        carp "something not a package tried to register with the mcp registry";
        return;
    }
    $self->{'packages'}->{$package->{'package'}} = $package;
    for my $message (@messages) {
        $self->{'registry'}->{$message} = $package;
    }
}

sub packages            { values %{shift->{'packages'}} }

sub get_package         { shift->{'packages'}->{shift()} }

sub package_for_message { shift->{'registry'}->{shift()} }


# next two subs taken from MCP 2.1 specification, section 2.4.3
sub get_best_version {
    my ($self, $package, $smin, $smax) = @_;
    return unless grep { $_->{'package'} eq $package } $self->packages;
    my $cmax = $self->{'packages'}->{$package}->max;
    my $cmin = $self->{'packages'}->{$package}->min;
    return
        (_version_cmp($cmax, $smin) and _version_cmp($smax, $cmin)) ?
        (_version_cmp($smax, $cmax) ? $cmax : $smax)                :
        undef;
}

sub _version_cmp {
    my ($v1, $v2) = @_;
    my @v1 = split /\./, $v1;
    my @v2 = split /\./, $v2;

    return ($v1[0] > $v2[0] or ($v1[0] == $v2[0] and $v1[1] >= $v2[1]));
}

1;
