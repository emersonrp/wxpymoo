# This is a class that wraps Wx::Prefs for simpler access to
# the worlds list and individual worlds
package WxMOO::Worlds;
use strict;
use warnings;
use v5.14;

use Carp;
use File::Slurp 'read_file';
use JSON;
use WxMOO::Prefs;
use base qw( Class::Accessor );
WxMOO::Worlds->mk_accessors(qw( config ));

sub init {
    my ($class) = @_;
    state $self;

    unless ($self) {
        $self = {
            'prefs' => WxMOO::Prefs->prefs,
        };
        bless $self, $class;
    };
    return $self;
}

sub load_worlds {
    my ($self) = @_;

    my $prefs = $self->{'prefs'};

    $prefs->config->SetPath('/worlds');
    my $worlds = [];

    if (my $groupcount = $prefs->config->GetNumberOfGroups) {
        for my $i (1 .. $groupcount) {
            my (undef, $worldname, undef) = $prefs->config->GetNextGroup($i-1);
            $prefs->config->SetPath($worldname);
            my $worlddata = {};
            if (my $datacount = $prefs->config->GetNumberOfEntries) {
                for my $j (1 .. $datacount) {
                    my (undef, $dataname, undef) = $prefs->config->GetNextEntry($j-1);
                    $worlddata->{$dataname} = $prefs->config->Read($dataname);
                }
                push @$worlds, WxMOO::World->new($worlddata);
            }
            $prefs->config->SetPath('/worlds');
        }
    } else {
        # populate the worlds with the default list, and save it.
        say STDERR "populating empty list";
        my $init_worlds = initial_worlds();
        for my $data (@$init_worlds) {
            push @$worlds, WxMOO::World->new($data);
use Data::Dumper;
print STDERR Data::Dumper::Dumper $data unless $data->{'name'};
            $prefs->config->SetPath($data->{'name'});
            while (my ($k, $v) = each %$data) {
                $prefs->config->Write($k, $v);
            }
            $prefs->config->SetPath('/worlds');
        }
    }
    return $worlds;
}

sub worlds {
    my $self = shift;
    $self->{'worlds'} //= $self->load_worlds;
}

sub initial_worlds {
    my $moolist = read_file('moolist.json');
    return decode_json $moolist;
}

#####################
package WxMOO::World;
use strict;
use warnings;
use v5.14;
use Class::Accessor;

use base qw( Class::Accessor );

my @fields = qw(
    name host port user pass note type
    ssh_server ssh_user ssh_loc_host ssh_loc_port
    ssh_rem_host ssh_rem_port
);
WxMOO::World->mk_accessors(@fields);

### DEFAULTS -- this will set everything to a default value if it's not already set.
#               This gives us both brand-new-file and add-new-params'-default-values
my %defaults = (
    port       => 7777,
    type       => 0,   # Socket
);

sub new {
    my ($class, $init) = @_;
    unless (%$init) { $init = \%defaults; }
    bless $init, $class;

}

sub save {
    my $self = shift;
    my $prefs = WxMOO::Prefs->prefs;

    (my $keyname = $self->name) =~ s/\W/_/g;
    $prefs->config->SetPath("/worlds/$keyname");
    for my $f (@fields) {
        $prefs->Write($f, $self->{$f});
    }
    return $self;
}

sub create {
    my $self = shift;
    my $newworld = $self->new;
    $newworld->save;
}

1;

