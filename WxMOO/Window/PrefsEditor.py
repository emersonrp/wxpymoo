package WxMOO::Window::PrefsEditor;
use strict;
use warnings;
use v5.14;

use Wx qw( :dialog :sizer :id :misc :notebook :font :colour :textctrl
            wxFNTP_USEFONT_FOR_LABEL wxFNTP_FONTDESC_AS_LABEL
            wxCLRP_USE_TEXTCTRL wxCLRP_SHOW_LABEL
);
use Wx::Event qw( EVT_BUTTON EVT_FONTPICKER_CHANGED EVT_COLOURPICKER_CHANGED );
use parent -norequire, 'Wx::PropertySheetDialog';
use base qw( Class::Accessor );
WxMOO::Window::PrefsEditor->mk_accessors(qw( parent ));

sub new {
    my ($class, $parent) = @_;

    my $self = $class->SUPER::new( $parent, -1, '', wxDefaultPosition, wxDefaultSize, );

    $self->parent($parent);

    my $book = $self->GetBookCtrl;

    $self->{'page_1'} = Wx::Panel->new($book);
    $self->{'page_2'} = Wx::Panel->new($book);
    $self->{'page_3'} = Wx::Panel->new($book);

    my $sizer        = Wx::BoxSizer->new(wxVERTICAL);
    my $button_sizer = $self->CreateButtonSizer( wxOK | wxCANCEL );

    $book->AddPage($self->{'page_1'}, "General");
    $book->AddPage($self->{'page_2'}, "Fonts and Colors");
    $book->AddPage($self->{'page_3'}, "Paths and Dirs");

    $self->populateGeneralPanel($self->{'page_1'});
    $self->populateFontPanel(   $self->{'page_2'});
    $self->populatePathsPanel(  $self->{'page_3'});

    $sizer->Add($book, 1, wxEXPAND | wxFIXED_MINSIZE | wxALL , 5 );
    $sizer->Add($button_sizer, 0, wxALIGN_CENTER_HORIZONTAL|wxBOTTOM, 5);

    $self->SetSizer($sizer);

    $self->Centre(wxBOTH);

    EVT_BUTTON($self, wxID_OK, \&update_prefs);

    return $self;
}

sub update_prefs {
    my ($self, $evt) = @_;
    my $g_page  = $self->{'page_1'};
    my $fc_page = $self->{'page_2'};
    my $p_page  = $self->{'page_3'};

    WxMOO::Prefs->prefs->save_window_size( $g_page->{'save_size_checkbox'}->GetValue + 0 );

    WxMOO::Prefs->prefs->output_font($fc_page->{'ofont_ctrl'}->GetSelectedFont);
    WxMOO::Prefs->prefs->input_font( $fc_page->{'ifont_ctrl'}->GetSelectedFont);

    WxMOO::Prefs->prefs->output_fgcolour($fc_page->{'o_fgcolour_ctrl'}->GetColour);
    WxMOO::Prefs->prefs->output_bgcolour($fc_page->{'o_bgcolour_ctrl'}->GetColour);
    WxMOO::Prefs->prefs->input_fgcolour( $fc_page->{'i_fgcolour_ctrl'}->GetColour);
    WxMOO::Prefs->prefs->input_bgcolour( $fc_page->{'i_bgcolour_ctrl'}->GetColour);

    WxMOO::Prefs->prefs->use_ansi( $fc_page->{'ansi_checkbox'}->GetValue + 0 );

    WxMOO::Prefs->prefs->external_editor( $p_page->{'external_editor'}->GetValue );

    $self->parent->output_pane->restyle_thyself;
    $self->parent->input_pane->restyle_thyself;
    $evt->Skip;
}

sub populateGeneralPanel {
    my ($self, $gp) = @_;

    $gp->{'save_size_checkbox'} = Wx::CheckBox->new($gp, -1, 'Save Window Size');
    $gp->{'save_size_checkbox'}->SetValue( WxMOO::Prefs->prefs->save_window_size );
    $gp->{'save_size_checkbox'}->Fit;

    $gp->{'panel_sizer'} = Wx::BoxSizer->new(wxVERTICAL);
    $gp->{'panel_sizer'}->Add($gp->{'save_size_checkbox'});

    $gp->SetSizer($gp->{'panel_sizer'});
}

sub populateFontPanel {
    my ($self, $fcp) = @_;

    my $ofont = WxMOO::Prefs->prefs->output_font || wxNullFont;
    my $ifont = WxMOO::Prefs->prefs->input_font  || wxNullFont;

    my $o_fgcolour = WxMOO::Prefs->prefs->output_fgcolour || wxBLACK;
    my $o_bgcolour = WxMOO::Prefs->prefs->output_bgcolour || wxWHITE;
    my $i_fgcolour = WxMOO::Prefs->prefs->input_fgcolour  || wxBLACK;
    my $i_bgcolour = WxMOO::Prefs->prefs->input_bgcolour  || wxWHITE;

    # output sample/controls
    $fcp->{'o_sample'}    = Wx::TextCtrl      ->new($fcp, -1, "",     wxDefaultPosition, wxDefaultSize, wxTE_READONLY);
    $fcp->{'ofont_ctrl' } = Wx::FontPickerCtrl->new($fcp, -1, $ofont, wxDefaultPosition, wxDefaultSize,
                                                                      wxFNTP_FONTDESC_AS_LABEL|wxFNTP_USEFONT_FOR_LABEL);

    my $bsize = $fcp->{'ofont_ctrl'}->GetSize->GetHeight;
    my $button_size = [$bsize, $bsize];

    $fcp->{'o_fgcolour_ctrl' } = Wx::ColourPickerCtrl->new($fcp, -1, $o_fgcolour, wxDefaultPosition, $button_size);
    $fcp->{'o_bgcolour_ctrl' } = Wx::ColourPickerCtrl->new($fcp, -1, $o_bgcolour, wxDefaultPosition, $button_size);

    $fcp->{'o_sample'}->SetFont($ofont);
    $fcp->{'o_sample'}->SetBackgroundColour($o_bgcolour);
    $fcp->{'o_sample'}->SetForegroundColour($o_fgcolour);
    $fcp->{'o_sample'}->SetValue(qq|Haakon says, "This is the output window."|);

    # input sample/controls
    $fcp->{'i_sample'}    = Wx::TextCtrl      ->new($fcp, -1, "",     wxDefaultPosition, wxDefaultSize, wxTE_READONLY);
    $fcp->{'ifont_ctrl' } = Wx::FontPickerCtrl->new($fcp, -1, $ifont, wxDefaultPosition, wxDefaultSize,
                                                                            wxFNTP_FONTDESC_AS_LABEL|wxFNTP_USEFONT_FOR_LABEL);
    $fcp->{'i_fgcolour_ctrl' } = Wx::ColourPickerCtrl->new($fcp, -1, $i_fgcolour, wxDefaultPosition, $button_size);
    $fcp->{'i_bgcolour_ctrl' } = Wx::ColourPickerCtrl->new($fcp, -1, $o_bgcolour, wxDefaultPosition, $button_size);

    $fcp->{'i_sample'}->SetFont($ifont);
    $fcp->{'i_sample'}->SetBackgroundColour($i_bgcolour);
    $fcp->{'i_sample'}->SetForegroundColour($i_fgcolour);
    $fcp->{'i_sample'}->SetValue(qq|`Haakon Hello from the input window.|);

    $fcp->{'ansi_checkbox'} = Wx::CheckBox->new($fcp, -1, 'Use ANSI colors');
    $fcp->{'ansi_checkbox'}->SetValue( WxMOO::Prefs->prefs->use_ansi );

    my $output_sizer = Wx::FlexGridSizer->new(1, 3, 5, 10);
    $output_sizer->Add($fcp->{'ofont_ctrl'      }, 0, wxEXPAND, 0);
    $output_sizer->Add($fcp->{'o_fgcolour_ctrl' }, 0);
    $output_sizer->Add($fcp->{'o_bgcolour_ctrl' }, 0);
    $output_sizer->AddGrowableCol(0);
    $output_sizer->Fit($fcp);

    my $input_sizer = Wx::FlexGridSizer->new(1, 3, 5, 10);
    $input_sizer->Add($fcp->{'ifont_ctrl'      }, 0, wxEXPAND, 0);
    $input_sizer->Add($fcp->{'i_fgcolour_ctrl' }, 0);
    $input_sizer->Add($fcp->{'i_bgcolour_ctrl' }, 0);
    $input_sizer->AddGrowableCol(0);
    $input_sizer->Fit($fcp);

    my $ansi_sizer = Wx::BoxSizer->new(wxVERTICAL);
    $ansi_sizer->Add($fcp->{'ansi_checkbox'});
    $ansi_sizer->Fit($fcp);

    my $panel_sizer = Wx::BoxSizer->new(wxVERTICAL);
    $panel_sizer->Add($fcp->{'o_sample'}, 0, wxRIGHT|wxLEFT|wxTOP|wxEXPAND, 10);
    $panel_sizer->Add($output_sizer,      0, wxRIGHT|wxLEFT|wxEXPAND, 10);
    $panel_sizer->AddSpacer($bsize);
    $panel_sizer->Add($fcp->{'i_sample'}, 0, wxRIGHT|wxLEFT|wxTOP|wxEXPAND, 10);
    $panel_sizer->Add($input_sizer,       0, wxRIGHT|wxLEFT|wxEXPAND, 10);
    $panel_sizer->AddSpacer($bsize);
    $panel_sizer->Add($ansi_sizer);

    EVT_FONTPICKER_CHANGED  ($fcp, $fcp->{'ofont_ctrl'}, \&update_sample_text);
    EVT_FONTPICKER_CHANGED  ($fcp, $fcp->{'ifont_ctrl'}, \&update_sample_text);
    EVT_COLOURPICKER_CHANGED($fcp, $fcp->{'i_fgcolour_ctrl'}, \&update_sample_text);
    EVT_COLOURPICKER_CHANGED($fcp, $fcp->{'i_bgcolour_ctrl'}, \&update_sample_text);
    EVT_COLOURPICKER_CHANGED($fcp, $fcp->{'o_fgcolour_ctrl'}, \&update_sample_text);
    EVT_COLOURPICKER_CHANGED($fcp, $fcp->{'o_bgcolour_ctrl'}, \&update_sample_text);

    $fcp->SetSizer($panel_sizer);
}

sub populatePathsPanel {
    my ($self, $pp) = @_;

    my $editor_label  = Wx::StaticText->new($pp, -1, "External Editor");
    $pp->{'external_editor'} = Wx::TextCtrl->new($pp, -1, "");
    $pp->{'external_editor'}->SetValue( WxMOO::Prefs->prefs->external_editor );
    $pp->{'external_editor'}->Fit;

    my $editor_sizer = Wx::FlexGridSizer->new(1,2,5,10);
    $editor_sizer->Add($editor_label,            0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL, 0);
    $editor_sizer->Add($pp->{'external_editor'}, 1, wxEXPAND, 0);
    $editor_sizer->AddGrowableCol(1);

    $pp->{'panel_sizer'} = Wx::BoxSizer->new(wxVERTICAL);
    $pp->{'panel_sizer'}->Add($editor_sizer, 0, wxEXPAND|wxALL, 10);

    $pp->SetSizer($pp->{'panel_sizer'});
}

sub update_sample_text {
    my ($self, $evt) = @_;
    for my $l ('o','i') {
        $self->{"${l}_sample"}->SetFont($self->{"${l}font_ctrl"}->GetSelectedFont);
        $self->{"${l}_sample"}->SetForegroundColour($self->{"${l}_fgcolour_ctrl"}->GetColour);
        $self->{"${l}_sample"}->SetBackgroundColour($self->{"${l}_bgcolour_ctrl"}->GetColour);
    }
    $evt->Skip;
}

1;
