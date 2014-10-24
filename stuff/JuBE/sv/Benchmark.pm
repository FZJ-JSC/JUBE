package Benchmark;

use strict;
use Carp;
use XML::Simple;
use Data::Dumper;

$Data::Dumper::Indent = 1;

sub new {
    my $self  = {};
    my $proto = shift;
    my $class = ref($proto) || $proto;
    my $err;

#Einlesen bzw. durchlaufen des Root-xmls
#includes einfuegen + Verschachtelung
#consts sichern
#Benchmark-Objekt erzeugen
#steps

    my $benchxmlfile=shift;
    my ($benchname,$platform);
   
    $self->{XS}=XML::Simple->new();
    my $benchref=$self->{XS}->XMLin($benchxmlfile, 
				    KeyAttr => { 'map' => "n",'benchmark' => "+name" },
				    ForceArray => 1);
    if($benchref) {     
	$benchname= $benchref->{'name'};
	$platform = $benchref->{'platform'};
    }

    #my $include=XML_Manager->new("Benchmarks/bench.xml","BGP");    
    #print ref($include),"\n" if($debug>=3);
    
    #$include->write_tree();
    #$include->get_tree();
    #$include->get_content();

    $platform=Platform->new("Benchmarks/platform.xml");

}

sub AUTOLOAD {
    no strict "refs";
    my ($self,$newval) = @_;
    
    # get_...method?
    if ($AUTOLOAD=~/.*::get(_\S+)/) { 
	my $attr_name=$1;
	*{AUTOLOAD} = sub {return $_[0]->{$attr_name}};
	return $self->{$attr_name}
    }
}
