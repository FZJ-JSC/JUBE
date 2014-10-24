package XML_Manager;

use strict;
use Carp;
use XML::LibXML; 
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
    my $err;

    ($err = CheckArgs::check('$$', @_)) && croak $err; 

    my $include_file = shift;
    # check parameters
    if ( ! defined $include_file ) {
	croak "Missing filename in new";
	return;
    } elsif ( ref $include_file ) {
	croak "Invalid filename argument '$include_file'";
    } 
    $self->{_INCLUDE} = $include_file;

    my $cname        = shift;
#--- check parameters
    if ( ! defined $cname ) {
	$self->{_CNAME} = undef; 
    } elsif ( ref $cname ) {
	croak "Invalid cname argument '$cname'";
    } elsif ( @_ ) {
	croak "Too many parameters in new";
	return;
    } else {
	$self->{_CNAME} = $cname;
    }

    $self->{_XS} = XML::LibXML->new();
    $self->{_CONTENT} = "";
    $self->{_CONTENT_TREE} = {};

    bless $self, $class;

    if ( $self->_get_xml($self->{_INCLUDE},$self->{_CNAME}) ) {
#--- Objekt mit Inhalt des geforderten XML-Abschnitts
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
    print("XML-Object destroyed\n");
}

sub get_tree {
    my($self) = shift;
    return($self->{_CONTENT_TREE});
}

sub write_tree {
    my($self) = @_;
   
#    print Dumper($self->{_CONTENT_TREE});
    foreach my $things ($self->{_CONTENT_TREE}->findnodes('/bench')) { 
	my($attr) = $things->findnodes('./benchmark'); 
	print $attr->to_literal, "\n" 
    } 
#    print "$_->data\n" foreach ($self->{_CONTENT_TREE}->findnodes($query));
#   print ($self->{_CONTENT});

    return(1);
}

#####################################################################################################
# Utility functions
#####################################################################################################

sub _get_xml {
    my($self, $include_file, $cname) = @_;
    my $line;
   
    if( ! open(INCLUDE, "<$include_file") ) {
	carp "Could not open '$include_file'";
	return;
    }
#--- Datei-Original lesen und speichern (auf cname eingrenzen?!)
    while (defined($line=<INCLUDE>)){
	$self->{_CONTENT}.=$line;
    }
    close(INCLUDE);

#--- XML-Baum lesen
    $self->{_CONTENT_TREE} = $self->{_XS}->parse_file($include_file); 

    return(1);
}

1;


