package WxMOO::Window::WorldsList;
use strict;
use warnings;
use v5.14;

use Wx qw( :combobox :misc :dialog :sizer :id );
use Wx::Event qw(EVT_CHOICE EVT_BUTTON);

use WxMOO::Prefs;
use WxMOO::Worlds;

use base qw( Wx::Dialog Class::Accessor );
WxMOO::Window::WorldsList->mk_accessors(qw( connection world_details_panel ));

sub new {
    state $self;

    unless ($self) {
        my ($class, $parent) = @_;

        WxMOO::Worlds->init;

        $self = $class->SUPER::new( $parent, -1, 'Worlds List');

        $self->connection($parent->connection);

        my $worlds = WxMOO::Worlds->init->worlds;

        my $world_details_staticbox = Wx::StaticBox->new($self, -1, "" );
        my $world_details_box       = Wx::StaticBoxSizer->new($world_details_staticbox, wxHORIZONTAL);

        my $world_label  = Wx::StaticText->new($self, -1, "World");
        my $world_picker = Wx::Choice    ->new($self, -1, wxDefaultPosition, wxDefaultSize, [], wxCB_SORT );

        # This 'reverse' is necessary for ->GetClientData(0) to get filled.
        # There is no clue as to why this is.
        for my $world (reverse @$worlds) {
            $world_picker->Append($world->{'name'}, $world);
        }

        my $world_picker_sizer = Wx::BoxSizer->new(wxHORIZONTAL);
        $world_picker_sizer->Add($world_label,  0,        wxALIGN_CENTER_VERTICAL, 0);
        $world_picker_sizer->Add($world_picker, 1, wxLEFT|wxALIGN_CENTER_VERTICAL, 5);

        $self->world_details_panel(WxMOO::Window::WorldPanel->new($self));
        $world_details_box->Add($self->world_details_panel, 1, wxEXPAND, 0);

        my $button_sizer = $self->CreateButtonSizer( wxOK | wxCANCEL );
        # Hax: change the "OK" button to "Connect"
        # This is a hoop-jumping exercise to use the platform-specific locations
        # of "OK" and "Cancel" instead of the hoop-jumping exercise of making my
        # own buttons.  There's almost certainly a better way to do this.
        for my $b ($button_sizer->GetChildren) {
            next unless ($b->GetWindow and $b->GetWindow->GetLabel eq '&OK');
            $b->GetWindow->SetLabel('&Connect');
            last;
        }

        my $main_sizer = Wx::BoxSizer->new(wxVERTICAL);
        $main_sizer->Add($world_picker_sizer, 0, wxEXPAND | wxALL,            10);
        $main_sizer->Add($world_details_box,  1, wxEXPAND | wxLEFT | wxRIGHT, 10);
        $main_sizer->Add($button_sizer,       0, wxEXPAND | wxALL,            10);

        $world_picker->SetSelection(0);
        $self->world_details_panel->fill_thyself($world_picker->GetClientData(0));

        $self->SetSizer($main_sizer);
        $main_sizer->Fit($self);
        $self->Layout;

        $self->Centre(wxBOTH);

        EVT_CHOICE($self, $world_picker, \&select_world);
        EVT_BUTTON($self, wxID_OK,       \&on_connect);

        bless $self, $class;
    }

    return $self;
}

sub select_world { shift->world_details_panel->fill_thyself(shift->GetClientData); }

# TODO - make WxMOO::World have a notion of "connect to yourself"
# Also therefore merge WxMOO::World and WxMOO::Window::WorldPanel
sub on_connect {
    my $self = shift;
    $self->connection->connect(
        $self->world_details_panel->world->host,
        $self->world_details_panel->world->port);
    $self->Hide;
}


#################################
package WxMOO::Window::WorldPanel;
use strict;
use warnings;
use v5.14;

use Wx qw( :misc :sizer :textctrl );
use Wx::Event qw(EVT_CHOICE);

use WxMOO::Prefs;

use base qw( Wx::Panel Class::Accessor );
WxMOO::Window::WorldPanel->mk_accessors(qw( world
                                            name host port user pass type note
                                            ssh_user
                                            ssh_loc_host ssh_loc_port
                                            ssh_rem_host ssh_rem_port ));

sub new {
    my ($class, $parent) = @_;

    my $self = $class->SUPER::new( $parent, -1,
        wxDefaultPosition, wxDefaultSize,
        # $style,
    );

    my $name_label = Wx::StaticText->new($self, -1, "Name:");
    my $host_label = Wx::StaticText->new($self, -1, "Host:");
    my $port_label = Wx::StaticText->new($self, -1, "Port:");
    $self->name(Wx::TextCtrl->new($self, -1, ""));
    $self->host(Wx::TextCtrl->new($self, -1, ""));
    $self->port(Wx::SpinCtrl->new($self, -1, ""));
    $self->port->SetRange(0, 65535);
    $self->port->SetValue(7777);

    my $user_label = Wx::StaticText->new($self, -1, "Username:");
    my $pass_label = Wx::StaticText->new($self, -1, "Password:");
    my $type_label = Wx::StaticText->new($self, -1, "Type:");
    $self->user(Wx::TextCtrl->new($self, -1, ""));
    $self->pass(Wx::TextCtrl->new($self, -1, "", wxDefaultPosition, wxDefaultSize, wxTE_PASSWORD));
    $self->type(Wx::Choice  ->new($self, -1,     wxDefaultPosition, wxDefaultSize,
                                 ['Socket','SSL','SSH Forwarding'], ));
    $self->type->SetSelection(0);

    $self->{'ssh_user_label'}     = Wx::StaticText->new($self, -1, "SSH Username:");
    $self->{'ssh_loc_host_label'} = Wx::StaticText->new($self, -1, "SSH Host:");
    $self->{'ssh_loc_port_label'} = Wx::StaticText->new($self, -1, "Local Port:");
    $self->{'ssh_rem_host_label'} = Wx::StaticText->new($self, -1, "Remote Host:");
    $self->{'ssh_rem_port_label'} = Wx::StaticText->new($self, -1, "Remote Port:");
    $self->ssh_user    (Wx::TextCtrl->new($self, -1, ""));
    $self->ssh_loc_host(Wx::TextCtrl->new($self, -1, ""));
    $self->ssh_loc_port(Wx::SpinCtrl->new($self, -1, ""));
    $self->ssh_loc_port->SetRange(0, 65535);
    $self->ssh_loc_port->SetValue(7777);
    $self->ssh_rem_host(Wx::TextCtrl->new($self, -1, ""));
    $self->ssh_rem_port(Wx::SpinCtrl->new($self, -1, ""));
    $self->ssh_rem_port->SetRange(0, 65535);
    $self->ssh_rem_port->SetValue(7777);

    my $field_sizer = Wx::FlexGridSizer->new(5, 2, 5, 10);
    $field_sizer->Add($name_label, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL, 0);
    $field_sizer->Add($self->name, 0, wxEXPAND, 0);
    $field_sizer->Add($host_label, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL, 0);
    $field_sizer->Add($self->host, 0, wxEXPAND, 0);
    $field_sizer->Add($port_label, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL, 0);
    $field_sizer->Add($self->port, 0, wxEXPAND, 0);
    $field_sizer->Add($user_label, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL, 0);
    $field_sizer->Add($self->user, 0, wxEXPAND, 0);
    $field_sizer->Add($pass_label, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL, 0);
    $field_sizer->Add($self->pass, 0, wxEXPAND, 0);
    $field_sizer->Add($type_label, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL, 0);
    $field_sizer->Add($self->type, 0, wxEXPAND, 0);
    $field_sizer->Add($self->{'ssh_user_label'}, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL, 0);
    $field_sizer->Add($self->ssh_user, 0, wxEXPAND, 0);
    $field_sizer->Add($self->{'ssh_loc_host_label'}, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL, 0);
    $field_sizer->Add($self->ssh_loc_host, 0, wxEXPAND, 0);
    $field_sizer->Add($self->{'ssh_loc_port_label'}, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL, 0);
    $field_sizer->Add($self->ssh_loc_port, 0, wxEXPAND, 0);
    $field_sizer->Add($self->{'ssh_rem_host_label'}, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL, 0);
    $field_sizer->Add($self->ssh_rem_host, 0, wxEXPAND, 0);
    $field_sizer->Add($self->{'ssh_rem_port_label'}, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL, 0);
    $field_sizer->Add($self->ssh_rem_port, 0, wxEXPAND, 0);
    $field_sizer->AddGrowableCol(1);

    my $note_box = Wx::StaticBoxSizer->new(Wx::StaticBox->new($self, -1, "note"), wxHORIZONTAL);
    $self->note(Wx::TextCtrl->new($self, -1, "", wxDefaultPosition, wxDefaultSize, wxTE_MULTILINE));
    $note_box->Add($self->note, 1, wxEXPAND, 0);

    my $mcp_check          = Wx::CheckBox->new($self, -1, "MCP 2.1");
    my $login_dialog_check = Wx::CheckBox->new($self, -1, "Use Login Dialog");
    my $shortlist_check    = Wx::CheckBox->new($self, -1, "On Short List");
    my $checkbox_sizer = Wx::GridSizer->new(3, 2, 0, 0);
    $checkbox_sizer->Add($mcp_check, 0, wxLEFT|wxRIGHT|wxALIGN_CENTER_VERTICAL, 5);
    $checkbox_sizer->Add($login_dialog_check, 0, wxLEFT|wxRIGHT|wxALIGN_CENTER_VERTICAL, 5);
    $checkbox_sizer->Add($shortlist_check, 0, wxLEFT|wxRIGHT|wxALIGN_CENTER_VERTICAL, 5);

    my $new_button = Wx::Button->new($self, -1, "New");
    my $reset_button = Wx::Button->new($self, -1, "Reset");
    my $save_button = Wx::Button->new($self, -1, "Save");
    my $button_sizer = Wx::FlexGridSizer->new(1, 3, 0, 0);
    $button_sizer->Add($new_button, 0, wxALL|wxALIGN_RIGHT, 5);
    $button_sizer->Add($reset_button, 0, wxALL, 5);
    $button_sizer->Add($save_button, 0, wxALL, 5);
    $button_sizer->AddGrowableCol(0);

    my $panel_sizer = Wx::BoxSizer->new(wxVERTICAL);
    $panel_sizer->Add($field_sizer, 0, wxALL|wxEXPAND, 10);
    $panel_sizer->Add($note_box, 1, wxEXPAND, 0);
    $panel_sizer->Add($checkbox_sizer, 0, wxEXPAND, 0);
    $panel_sizer->Add($button_sizer, 0, wxEXPAND, 0);
    $self->{'panel_sizer'} = $panel_sizer;

    $self->SetSizerAndFit($panel_sizer);

    EVT_CHOICE($self, $self->type, \&show_hide_ssh_controls);

    $self->{'ssh_user_label'}->Hide;
    $self->{'ssh_loc_host_label'}->Hide;
    $self->{'ssh_loc_port_label'}->Hide;
    $self->{'ssh_rem_host_label'}->Hide;
    $self->{'ssh_rem_port_label'}->Hide;
    $self->ssh_user->Hide;
    $self->ssh_loc_host->Hide;
    $self->ssh_loc_port->Hide;
    $self->ssh_rem_host->Hide;
    $self->ssh_rem_port->Hide;

    return $self;
}

sub on_save {
}

sub on_reset {
}

sub on_new {
}

sub fill_thyself {
    my ($self, $world) = @_;

    unless (ref $world) {
        say STDERR "got a bad world in fill_thyself:";
        say STDERR Data::Dumper::Dumper $world;
        return;
    }

    $self->world($world);

    no warnings 'uninitialized';
    $self->name->SetValue($world->name);
    $self->host->SetValue($world->host);
    $self->port->SetValue($world->port);
    $self->user->SetValue($world->user);
    $self->pass->SetValue($world->pass);
    $self->note->SetValue($world->note);
    $self->type->SetSelection($world->type);
    $self->ssh_user->SetValue($world->ssh_user);
    $self->ssh_loc_host->SetValue($world->ssh_loc_host);
    $self->ssh_loc_port->SetValue($world->ssh_loc_port);
    $self->ssh_rem_host->SetValue($world->ssh_rem_host);
    $self->ssh_rem_port->SetValue($world->ssh_rem_port);

    $self->show_hide_ssh_controls($self->type->GetSelection == 2);
}

sub show_hide_ssh_controls{
    my ($self, $to_show) = @_;
    $to_show //= $self->type->GetSelection == 2;
    $self->{'ssh_user_label'}->Show($to_show);
    $self->{'ssh_loc_host_label'}->Show($to_show);
    $self->{'ssh_loc_port_label'}->Show($to_show);
    $self->{'ssh_rem_port_label'}->Show($to_show);
    $self->{'ssh_rem_host_label'}->Show($to_show);
    $self->ssh_user->Show($to_show);
    $self->ssh_loc_host->Show($to_show);
    $self->ssh_loc_port->Show($to_show);
    $self->ssh_rem_host->Show($to_show);
    $self->ssh_rem_port->Show($to_show);

    $self->{'panel_sizer'}->Layout;
}

1;
