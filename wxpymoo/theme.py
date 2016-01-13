package WxMOO::Theme;
use strict;
use warnings;
use Wx qw(:colour);
use v5.14;

sub new {
    my ($class, %args) = @_;
    bless {
        b_black   => '002b36',
        d_black   => '073642',
        b_red     => 'cb4b16',
        d_red     => 'dc322f',
        b_green   => '586e75',
        d_green   => '859900',
        d_yellow  => '657b83',
        b_yellow  => 'b58900',
        b_blue    => '839496',
        d_blue    => '268bd2',
        b_magenta => '6c71c4',
        d_magenta => 'd33682',
        b_cyan    => '93a1a1',
        d_cyan    => '2aa198',
        b_white   => 'fdf6e3',
        d_white   => 'eee8d5',
        %args,
    }, $class;
}

sub Colour {
    my ($self, $color, $brightness) = @_;
    $brightness = $brightness ? 'b' : 'd';
    my @rgb = unpack 'C*', pack 'H*', $self->{"${brightness}_$color"};
    return Wx::Colour->new(@rgb);
}

1;
