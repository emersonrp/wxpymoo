package WxMOO::Window::ConnectDialog;
use strict;
use warnings;
use v5.14;

use Wx qw( :id :misc :dialog :sizer );
use Wx::Event qw( EVT_BUTTON );
use base qw( Wx::Dialog Class::Accessor );
WxMOO::Window::ConnectDialog->mk_accessors(qw( parent host port ));

sub new {
    my ($class, $parent) = @_;

    my $self = $class->SUPER::new( $parent, -1, "Connect to World",
       wxDefaultPosition, wxDefaultSize,
       wxDEFAULT_DIALOG_STYLE | wxSTAY_ON_TOP
    );

    $self->parent($parent);

    my $host_label = Wx::StaticText->new($self, -1, "Host:");
    my $port_label = Wx::StaticText->new($self, -1, "Port:");
    $self->host(Wx::TextCtrl->new($self, -1, ""));
    $self->port(Wx::TextCtrl->new($self, -1, ""));

    my $input_sizer = Wx::FlexGridSizer->new(2, 2, 0, 0);
    $input_sizer->AddGrowableCol( 1 );
    $input_sizer->Add($host_label, 0, wxLEFT | wxALIGN_RIGHT | wxALIGN_CENTER_VERTICAL, 10);
    $input_sizer->Add($self->host, 0, wxEXPAND | wxALL, 5);
    $input_sizer->Add($port_label, 0, wxLEFT | wxALIGN_RIGHT | wxALIGN_CENTER_VERTICAL, 10);
    $input_sizer->Add($self->port, 0, wxEXPAND | wxALL, 5);


    my $button_sizer = $self->CreateButtonSizer( wxOK | wxCANCEL );

    my $sizer = Wx::BoxSizer->new(wxVERTICAL);
    $sizer->Add($input_sizer,  1, wxALL | wxEXPAND, 10);
    $sizer->Add($button_sizer, 0, wxALL, 10);
    $self->SetSizer($sizer);
    $sizer->Fit($self);
    $self->Layout();
    $self->Centre(wxBOTH);

    EVT_BUTTON($self, wxID_OK, \&connect_please);

    return $self;
}

sub connect_please {
    my ($self, $evt) = @_;
    my $host = $self->host->GetValue;
    my $port = $self->port->GetValue;

    $self->host->Clear;
    $self->port->Clear;

    $self->parent->connection->connect($host, $port);
    $evt->Skip;
}

1;
