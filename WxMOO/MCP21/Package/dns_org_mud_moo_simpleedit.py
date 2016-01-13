package WxMOO::MCP21::Package::dns_org_mud_moo_simpleedit;
use strict;
use warnings;
use v5.14;

use Carp;
no if $] >= 5.018, warnings => "experimental::smartmatch";

# this code is already in dire need of a rework, but it's starting work at all, at least.

use File::Temp;
use Wx qw( :id :execute );
use Wx::Event qw( EVT_END_PROCESS EVT_TIMER );

use WxMOO::Editor;

use parent 'WxMOO::MCP21::Package';

sub new {
    my ($class) = @_;
    my $self = $class->SUPER::new({
        package => 'dns-org-mud-moo-simpleedit',
        min     => '1.0',
        max     => '1.0',
    });

    $self->{'in_progress'} = {};

    $WxMOO::MCP21::registry->register($self, qw( dns-org-mud-moo-simpleedit-content ));
}

sub dispatch {
    my ($self, $message) = @_;
    given ($message->{'message'}) {
        when ('dns-org-mud-moo-simpleedit-content') {
            $self->dns_org_mud_moo_simpleedit_content($message);
        }
    }
}

sub dns_org_mud_moo_simpleedit_content {
    my ($self, $mcp_msg) = @_;

    my $id = WxMOO::Editor::launch_editor({
        type     => $mcp_msg->{'data'}->{'type'},
        content  => $mcp_msg->{'data'}->{'content'},
        callback => sub { $self->_send_file_if_needed(@_) },
    });
    $self->{'in_progress'}->{$id} = $mcp_msg;
}

sub _send_file_if_needed {
    my ($self, $id, $content) = @_;
    # shipit!
    my $mcp_msg = $self->{'in_progress'}->{$id};
    WxMOO::MCP21::server_notify(
        'dns-org-mud-moo-simpleedit-set', {
            reference => $mcp_msg->{'data'}->{'reference'},
            type      => $mcp_msg->{'data'}->{'type'},
            content   => $content,
        }
    );
}

1;
