package WxMOO::Editor;
use strict;
use warnings;
use v5.14;

use Carp;
no if $] >= 5.018, warnings => "experimental::smartmatch";

# this code is already in dire need of a rework, but it's starting work at all, at least.

use File::Temp;
use Wx qw( :id :execute );
use Wx::Event qw( EVT_END_PROCESS EVT_TIMER );

use WxMOO::Prefs;

my $collection = WxMOO::Editor::Collection->new;

# class method
# params:
#     type:     file type for making tempfile/extension
#     content:  actual content for the editor
#     callback: coderef to call with $id when sending back the contents
sub launch_editor {
    my ($opts) = @_;
    my $process = Wx::Process->new;
    while (my ($k, $v) = each %$opts) {
        $process->{"_$k"} = $v;
    }
    $process->{"_id"} = Wx::NewId;
    my $tempfile = _make_tempfile($opts->{'type'}, $opts->{'content'});
    $process->{'_filename'} = $tempfile;

    $process->{'_last_sent'} = 0;
    Wx::ExecuteCommand(WxMOO::Prefs->prefs->external_editor . " $tempfile", wxEXEC_NODISABLE, $process );

    $collection->in_progress($process->{'_id'}, $process);

    _start_watching($process);

    EVT_END_PROCESS( $process, wxID_ANY, \&_send_and_cleanup );

    return $process->{'_id'};
}


sub _send_and_cleanup {

    my ($proc) = @_;
    _send_file_if_needed($proc);
    _stop_watching($proc);
    unlink $proc->{'_filename'};
}

# our queue of known tempfiles with editors sitting open.
# we want "save" to send the data to the MOO, so we'll
# stat() the queue every once in a while.
sub _start_watching {
    my ($proc) = @_;
    my $file = $proc->{'_filename'};
    $proc->{'_last_sent'} = (stat $file)[9];
    unless ($collection->watchTimer->IsRunning) {
        $collection->watchTimer->Start(250, 0);
    }
}

sub _stop_watching {
    my ($proc) = @_;
    delete $collection->in_progress->{$proc->{'_id'}};
    unless (%{$collection->in_progress}) {
        $collection->watchTimer->Stop;
    }
}

sub _watch_queue {
    for (values %{$collection->in_progress}) {
        _send_file_if_needed($_);
    }
}

sub _send_file_if_needed {
    my ($proc) = @_;
    my $file = $proc->{'_filename'};
    my $mtime = (stat $file)[9] or carp "wtf is wrong with $file?!?";
    if ($mtime > $proc->{'_last_sent'}) {
        # shipit!
        my @content;
        {
            local $\;
            open my $FILE, '<', $file or die $!;
            @content = <$FILE>;
            close $FILE;
        }
        $proc->{'_callback'}->($proc->{'_id'}, \@content);
        $proc->{'_last_sent'} = $mtime;
    }
}

sub _make_tempfile {
    my ($type, $content) = @_;

    # if it's a known type, give it an extension to give the editor a hint
    my $extension = {
        'moo-code' => '.moo',
    }->{$type};

    my $tempfile = File::Temp->new(
        TEMPLATE => 'wxmoo_XXXXX',
        SUFFIX   => $extension || '.tmp',
        DIR      => '/tmp',  # TODO - cross-platform pls
    );

    if (ref $content eq 'ARRAY') {
        for (@$content) {
            s///; # TODO ok ew - there's got to be some deterministic way to dtrt here.
            say $tempfile $_;
        }
    }
    $tempfile->flush;

    return $tempfile;
}

package WxMOO::Editor::Collection;
use strict;
use warnings;
use v5.14;

use Wx;
use Wx::Event qw( EVT_TIMER );

use base 'Wx::EvtHandler';

sub new {
    my ($class) = @_;
    state $self;
    unless ($self) {
        $self = Wx::EvtHandler->new;
        $self->{'in_progress'} = {};
        $self->{'watchTimer'} = Wx::Timer->new($self, -1);

        EVT_TIMER($self, $self->{'watchTimer'}, \&WxMOO::Editor::_watch_queue);
    }

    bless($self, $class);

    return $self;
}

sub watchTimer  { shift->{'watchTimer'}  }
sub in_progress {
    my ($self, $k, $v) = @_;
    if ($k and $v) {
        $self->{'in_progress'}->{$k} = $v;
    }
    return $self->{'in_progress'};
}

1;
