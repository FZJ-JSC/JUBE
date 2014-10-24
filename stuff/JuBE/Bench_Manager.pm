package Bench_Manager;

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

my $debug=0;

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

#--- Object which includes the required XML-Part and "includes"
    if ( $self->_get_xml(@params) ) {
	return $self;   
    } else {
	return;
    }
}

sub get_content {
    my($self) = shift;
    return($self->{_CONTENT});
}

sub get_tree {
    my($self) = shift;
    return($self->{_CONTENT_TREE});
}

sub write_tree {
    my($self) = @_;
   
    print Dumper($self->{_CONTENT_TREE});
    return(1);
}

sub write_xml {
    my($self) = @_;
   
    print ($self->{_CONTENT});
    return(1);
}

sub get_benchmarks {
    my($self) = @_;
    my @benchmarks=keys(%{$self->{_CONTENT_TREE}->{"bench"}->[0]->{"benchmark"}});
    return (\@benchmarks);
}

sub get_platform {
    my($self) = @_;
    
    return($self->{_CONTENT_TREE}->{"bench"}->[0]->{'platform'});
}
 
sub DESTROY {
    my($self) = shift;
#    printf("XML-Object destroyed\n");
}

#####################################################################################################
# Utility functions
#####################################################################################################

sub _get_xml {
    my $self   = shift @_;
    my @params = @_;
    my $line;
    my %part;
   
#--- parse parameter list -> search function for xml-sections
    if (@params!=0) {
	foreach my $param (@params) {
	    my ($attr, $val) = split(/=/, $param);
	    $part{$attr}=$val;
	}	
    }    

#--- read and store original file              #SM# auf params eingrenzen?! nein <- Filemanager nutzen
                                               #SM# bzw. trennen von xml-einlesen  
    if( ! open(XML, "<$self->{_XML}") ) {
	carp "Could not open '$self->{_XML}'";
	return;
    }
    while (defined($line=<XML>)){
	$self->{_CONTENT}.=$line;
    }
    close(XML);

#--- read XML-Tree
    $self->{_CONTENT_TREE} = $self->{_XS}->XMLin("$self->{_XML}",
						 KeepRoot=>1,
						 KeyAttr => {'benchmark' => "+name",
							     'include'   => "+file",
							     'step'      => "+name",
							     'stepdef'   => "+name",
							     'action'    => "+name"},
						 ForceArray => 1);

    if ($debug>3) {
	print "-----------------------------\n";
	print Dumper($self->{_CONTENT_TREE}); 
	print "-----------------------------\n";
    }

#--- parse - search function -> only part of the hash shall be included
    if (keys(%part)) {
		
	my $type=$part{"type"};
	if (!defined($type)) { croak "Missing type\n";return;}
	delete($part{"type"});
	
	my $found=0;
      PARSE: foreach my $attr (keys %{$self->{_CONTENT_TREE}}) {
	  
	  if (exists ($self->{_CONTENT_TREE}->{$attr}->[0]->{$type})) {
	      
	      foreach my $arg (keys %part) {
		
		  if (defined(my $argval=$self->{_CONTENT_TREE}->{$attr}->[0]->{$type}->{$arg})) {
		      if ($argval=~/^$part{$arg}$/) {
			  $found++;
			  if ($found==keys(%part)) {
			      $self->{_CONTENT_TREE}=$self->{_CONTENT_TREE}->{$attr}->[0]->{$type};     #SM# ?
			      last PARSE;
			  }
		      }		    
		  } 
	      }
	  }
      }
    }
	

#--- parse - searching includes, include them recursively  #SM# nur Teilhashes? tiefer rekursen
#--- Hint: Only one main element per xml-file allowed (XML-Simple&Jube2)
    foreach my $attr (keys %{$self->{_CONTENT_TREE}}) {

	if (exists ($self->{_CONTENT_TREE}->{$attr}->[0]->{include})) {   

	    foreach my $file (keys %{$self->{_CONTENT_TREE}->{$attr}->[0]->{include}}) {

		my @params=();
		foreach my $param (keys %{$self->{_CONTENT_TREE}->{$attr}->[0]->{include}->{$file}}) {

		    my $paramvalue="$param=$self->{_CONTENT_TREE}->{$attr}->[0]->{include}->{$file}->{$param}";
		    push(@params,$paramvalue) unless ($param=~/^file$/);		

		}
		print ">>@params<<\n" if ($debug>3);

		my $include=Bench_Manager->new($file,@params);   
		my ($include_tmp)=keys(%{$include->{_CONTENT_TREE}});      #CONTENT auch speichern?!
		$self->{_CONTENT_TREE}->{$attr}->[0]->{$include_tmp}=$include->{_CONTENT_TREE}->{$include_tmp};	
	    }
	}
    }

    return(1);
}

1;


