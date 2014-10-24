package XML_Manager;

use strict;
use Carp;
use XML::Simple;
use Data::Dumper;
use Time::HiRes qw ( time );

use Util::CheckArgs;

$Data::Dumper::Indent = 1;

#####################################################################################################
# POD !!!!
#####################################################################################################

my $patint="([\\+\\-\\d]+)";   # Pattern for Integer number
my $patfp ="([\\+\\-\\d.E]+)"; # Pattern for Floating Point number
my $patwrd="([\^\\s]+)";       # Pattern for Work (all noblank characters)
my $patnint="[\\+\\-\\d]+";    # Pattern for Integer number, no () 
my $patnfp ="[\\+\\-\\d.E]+";  # Pattern for Floating Point number, no () 
my $patnwrd="[\^\\s]+";        # Pattern for Work (all noblank characters), no () 
my $patbl ="\\s+";             # Pattern for blank space (variable length)

my $debug=2;

#####################################################################################################
# Interface functions
#####################################################################################################

sub new {
    my $self  = {};
    my $proto = shift;
    my $class = ref($proto) || $proto;
 
    my $xml_file = shift;
    my @params   = @_; 

    # check parameters
    if ( ! defined $xml_file ) {
	croak "Missing filename in new";
	return;
    } elsif ( ref $xml_file ) {
	croak "Invalid filename argument '$xml_file'";
    } 

    $self->{_XML} = $xml_file;
    $self->{_XS} = XML::Simple->new();
    $self->{_CONTENT} = "";
    $self->{_CONTENT_TREE} = {};
    bless $self, $class;

#--- Objekt mit Inhalt des geforderten XML-Abschnitts und aufgeloesten includes
    if ( $self->_get_xml($self->{_XML}, @params) ) {
	return $self;   
    } else {
	return;
    }
}

sub get_content {
    my($self) = shift;
    return($self->{_CONTENT});
}

sub DESTROY {
    my($self) = shift;
    printf("XML-Object destroyed\n");
}

sub get_tree {
    my($self) = shift;
    return($self->{_CONTENT_TREE});
}

sub write_tree {
    my($self) = @_;
   
    print Dumper($self->{_CONTENT_TREE});
#    print ($self->{_CONTENT});

    return(1);
}

#####################################################################################################
# Utility functions
#####################################################################################################

sub _get_xml {
    my $self   = shift @_;
    my @params = @_;
    my $line;
    my %part;
   
    if (@params==0) {
	#all
    } else {
	#Parameterliste auseinandernehmen -> Suchfunktionen der xml-Abschnitte
	foreach my $param (@params) {
	    my ($attr, $val) = split(/=/, $param);
	    $part{$attr}=$val;
	}
	#auf Suchfunktion parsen, nur Teilhash bearbeiten
    }    

    if( ! open(XML, "<$self->{_XML}") ) {
	carp "Could not open '$self->{_XML}'";
	return;
    }
#--- Datei-Original lesen und speichern (auf cname eingrenzen?!)
    while (defined($line=<XML>)){
	$self->{_CONTENT}.=$line;
    }
    close(XML);

#--- XML-Baum lesen
    $self->{_CONTENT_TREE} = $self->{_XS}->XMLin("$self->{_XML}");
    # auf includes parsen, includes rekurs. einfuegen
    if (exists ($self->{_CONTENT_TREE}->{include})) {      #evtl. mehrere!
	my $include=XML_Manager->new($self->{_CONTENT_TREE}->{include}->{file}); #weitere params!
	$self->{_CONTENT_TREE}->{include_besserername}=$include->{_CONTENT_TREE};
    }

    return(1);
}

1;


