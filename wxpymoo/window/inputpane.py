package WxMOO::Window::InputPane;
use strict;
use warnings;
use v5.14;

use Wx qw( wxTheClipboard :misc :textctrl :font :keycode );
use Wx::DND;
use Wx::RichText qw( EVT_RICHTEXT_SELECTION_CHANGED );
use Wx::Event qw( EVT_TEXT EVT_TEXT_ENTER EVT_KEY_DOWN EVT_CHAR EVT_MIDDLE_UP );
use WxMOO::Prefs;
use WxMOO::Utility;

use parent -norequire, qw( Wx::RichTextCtrl Class::Accessor );
WxMOO::Window::InputPane->mk_accessors(qw( parent connection cmd_history ));

sub new {
    my ($class, $parent) = @_;

    my $self = $class->SUPER::new( $parent, -1, "",
        wxDefaultPosition, wxDefaultSize,
        wxTE_PROCESS_ENTER | wxTE_MULTILINE
    );

    $self->parent($parent);

    my $font = WxMOO::Prefs->prefs->input_font;
    $self->SetFont($font);

    $self->cmd_history(WxMOO::Window::InputPane::CommandHistory->new);

    EVT_TEXT_ENTER( $self, -1, \&send_to_connection );
    EVT_TEXT      ( $self, -1, \&update_command_history );
    EVT_KEY_DOWN  ( $self,     \&check_for_interesting_keystrokes );
#    EVT_CHAR      ( $self,     \&debug_key_code );

    if (WxMOO::Prefs->prefs->use_x_copy_paste) {
        EVT_MIDDLE_UP                  ( $self, \&paste_from_selection );
#        EVT_RICHTEXT_SELECTION_CHANGED ( $self, \&copy_from_selection );
    }

    $self->SetFocus;
    $self->Clear;

    $self->restyle_thyself;

    bless $self, $class;
}

sub paste_from_selection {
    # we only get here if we have ->prefs->use_x_copy paste set.
    # We might have selected that option in a non-Unix context, though,
    # so we want to check to decide which clipboard to paste from.
    wxTheClipboard->UsePrimarySelection(1) if WxMOO::Utility::is_unix;
    shift->Paste;
    wxTheClipboard->UsePrimarySelection(0) if WxMOO::Utility::is_unix;
}

sub copy_from_selection {
    wxTheClipboard->UsePrimarySelection(1) if WxMOO::Utility::is_unix;
    shift->Copy;
    say STDERR "Copied!!!";
    wxTheClipboard->UsePrimarySelection(0) if WxMOO::Utility::is_unix;
}

sub restyle_thyself {
    my ($self) = @_;
    my $basic_style = Wx::RichTextAttr->new;
    $basic_style->SetTextColour      (WxMOO::Prefs->prefs->input_fgcolour);
    $basic_style->SetBackgroundColour(WxMOO::Prefs->prefs->input_bgcolour);
    $self->SetBackgroundColour(WxMOO::Prefs->prefs->input_bgcolour);
    $self->SetBasicStyle($basic_style);
    $self->SetFont(WxMOO::Prefs->prefs->input_font);
}

sub send_to_connection {
    my ($self, $evt) = @_;
    if ($self->connection) {
        (my $stuff = $self->GetValue) =~ s/\n//g;
        $self->cmd_history->add($stuff);
        $self->connection->output("$stuff\n");
        $self->Clear;
    }
}

sub update_command_history {
    my ($self, $evt) = @_;
    $self->cmd_history->update($self->GetValue)
}

sub debug_key_code {
    my ($self, $evt) = @_;
    my $k = $evt->GetKeyCode;
    say STDERR "EVT_CHAR $k";
}

sub check_for_interesting_keystrokes {
    my ($self, $evt) = @_;
    my $k = $evt->GetKeyCode;

    if    ($k == WXK_UP)       { $self->SetValue($self->cmd_history->prev); }
    elsif ($k == WXK_DOWN)     { $self->SetValue($self->cmd_history->next); }
    elsif ($k == WXK_PAGEUP)   { $self->parent->output_pane->ScrollPages(-1) }
    elsif ($k == WXK_PAGEDOWN) { $self->parent->output_pane->ScrollPages(1) }
    elsif ($k == WXK_INSERT)   { $self->Paste if $evt->ShiftDown }
    elsif ($k == 23) { # Ctrl-W.  Is this right?
            my $end = $self->GetInsertionPoint;

            $self->GetValue =~ /(\s*[[:graph:]]+\s*)$/;

            return unless $1;

            my $start = $end - (length $1);
            $self->Remove($start, $end);
    } else {
# if ($self->GetValue =~ /^con?n?e?c?t? +\w+ +/) {
#     # it's a connection attempt, style the passwd to come out as *****
# }
        $evt->Skip; return;
    }
    $self->SetInsertionPointEnd;
}

######################
package WxMOO::Window::InputPane::CommandHistory;
use strict;
use warnings;
use v5.14;

# Rolling our own simplified command history here b/c Term::Readline
# et al are differently-supported on different platforms.  We only
# need a small subset anyway.

# we keep a list of historical entries, and a 'cursor' so we can
# keep track of where we are looking in the list.  The last
# entry in the history gets twiddled as we go.  Once we are done
# with it and enter it into history, a fresh '' gets appended to
# the array, on and on, world without end.
sub new {
    my ($class) = @_;
    bless {
        'history' => [''],
        'current' => 0,
    }, $class;
}

sub end { $#{shift->{'history'}} }

# which entry does our 'cursor' point to?
sub current_entry {
    my ($self, $new) = @_;
    $self->{'history'}->[$self->{'current'}] = $new if defined $new;
    $self->{'history'}->[$self->{'current'}];
}

sub prev {
    my ($self) = @_;
    $self->{'current'}-- if $self->{'current'} > 0;
    $self->current_entry;
}

sub next {
    my ($self) = @_;
    $self->{'current'}++ if $self->{'current'} < $self->end;
    $self->current_entry;
}

# if we've actually changed anything, take the changed value
# and use it as the new "current" value, at the end of the array.
sub update {
    my ($self, $string) = @_;
    if ($self->current_entry ne $string) {
        $self->{'current'} = $self->end;
        $self->current_entry($string);
    }
}

# this is the final state of the thing we input.
# Make sure it's updated, then push a fresh '' onto the end
sub add {
    my ($self, $string) = @_;
    return unless $string;  # don't stick blank lines in there.
    @{$self->{'history'}}[-1] = $string;

    push @{$self->{'history'}}, '';
    $self->{'current'} = $self->end;
}

1;
