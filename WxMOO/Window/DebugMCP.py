package WxMOO::Window::DebugMCP;
use strict;
use warnings;
use v5.14;

use Wx qw( :misc :sizer );
use Wx::Event qw( EVT_SIZE );

use WxMOO::Prefs;

use base qw( Wx::Frame Class::Accessor );
WxMOO::Window::DebugMCP->mk_accessors(qw( active output_pane ));

sub new {
    my ($class) = @_;
    state $self;
    unless ($self) {
        $self = $class->SUPER::new( undef, -1, 'Debug MCP');

        $self->addEvents;

        if (1 || WxMOO::Prefs->prefs->save_mcp_window_size) {
            my $w = WxMOO::Prefs->prefs->mcp_window_width  || 600;
            my $h = WxMOO::Prefs->prefs->mcp_window_height || 400;
            $self->SetSize([$w, $h]);
        }

        $self->output_pane(WxMOO::Window::DebugMCP::Pane->new($self));
        my $sizer = Wx::BoxSizer->new( wxVERTICAL );
        $sizer->Add($self->output_pane, 1, wxALL|wxGROW, 5);
        $self->SetSizer($sizer);
    }

    return $self;
}

sub toggle_visible  {
    my $self = shift;
    if ($self->IsShown) {
        $self->Hide->();
        $self->active(0);
    } else {
        $self->Show->();
        $self->active(1);
    }
}
sub Close {
    my $self = shift;
    $self->SUPER::Close->();
    $self->active(0);
}

SCOPE: {
    my $serverMsgColour = Wx::Colour->new(128, 0, 0);
    my $clientMsgColour = Wx::Colour->new(0,   0, 128);
    sub display {
        my ($self, @data) = @_;
        return unless $self->active;

        my $op = $self->output_pane;

        for my $line (@data) {
            unless ($line =~ /\n$/) { $line = "$line\n"; }

            if ($line =~ /^S->C/) {
                $op->BeginTextColour($serverMsgColour);
            } elsif ($line =~ /^C->S/) {
                $op->BeginTextColour($clientMsgColour);
            } else {
                $op->BeginBold;
            }
            $op->WriteText($line);
            $op->EndTextColour;
            $op->EndBold;
        }
        $op->ShowPosition($op->GetCaretPosition);
    }
}

sub addEvents {
    my ($self) = @_;

    EVT_SIZE( $self, \&onSize );
}

sub onSize {
    my ($self, $evt) = @_;

    if (1 || WxMOO::Prefs->prefs->save_mcp_window_size) {
        my ($w, $h) = $self->GetSizeWH;
        WxMOO::Prefs->prefs->mcp_window_width($w);
        WxMOO::Prefs->prefs->mcp_window_height($h);
    }
    $evt->Skip;
}

package WxMOO::Window::DebugMCP::Pane;
use strict;
use warnings;
use v5.14;

use Wx qw( :misc :textctrl );
use Wx::RichText;

use base 'Wx::RichTextCtrl';

sub new {
    my ($class, $parent) = @_;
    my $self = $class->SUPER::new(
        $parent, -1, "", wxDefaultPosition, wxDefaultSize,
            wxTE_READONLY | wxTE_NOHIDESEL
        );

    return bless $self, $class;
}

1;
