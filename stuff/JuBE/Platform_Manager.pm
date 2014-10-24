package Platform_Manager;

use strict;
use Carp;
use vars qw ($AUTOLOAD);

use XML::Simple; 

use JuBE::Substitute_Engine;

sub new {
    my $self  = {};
    my $proto = shift;
    my $class = ref($proto) || $proto;
    my $err;

#    ($err = CheckArgs::check('$$$', @_)) && croak $err; 

    my $platform_file = shift;
    my $platform = shift;
    my $substitute_engine=shift;

    $self->{_XS} = XML::Simple->new();
    $self->{DOC} = $self->{_XS}->XMLin($platform_file,
				       KeepRoot=>1,
				       KeyAttr => {'platform' => "+name"},
				       ForceArray => 1); 
    $self->{PLATFORM} = $self->{DOC}->{'platforms'}->[0]->{'platform'}->{$platform};
    $self->{SUBSTITUTE_ENGINE} = $substitute_engine;

    if (exists($self->{PLATFORM})){
	if (_make_sub_hsh($self)) {
	    bless $self, $class;
	    return $self;   
	} else {
	    croak "Error generating subhash\n";	    
	}
    } else {
	croak "Platform doesn't exist\n"; #SM# or no defaults und weiter?
    }
}

sub get_machine_def {
    my ($self) = @_;
    return($self->{PLATFORM}->{'params'}->[0]);
}

sub AUTOLOAD {
    no strict "refs";
    my ($self) = @_;
    
    # get_...method?
    if ($AUTOLOAD=~/.*::get_(\S+)/) { 
	my $attr_name=$1;
	*{AUTOLOAD} = sub {return $self->{PLATFORM}->{params}->[0]->{$attr_name}};
	return $self->{PLATFORM}->{'params'}->[0]->{$attr_name}
    }
}

###################################

sub _make_sub_hsh 
{
    my $self = shift;
    my ($key,$val,$rc);
    my $platformparamsref=$self->{PLATFORM}->{'params'}->[0];

    foreach $key (keys(%{$platformparamsref})) {	
	$val=$platformparamsref->{$key};
	$rc=$self->{SUBSTITUTE_ENGINE}->substitute(\$val); #auf Objekt aktueller Sub-Hash, rc Ersetzung oder nicht
	$platformparamsref->{$key}=$val; #SM# eigentlich nicht noetig?!
	$self->{SUBSTITUTE_ENGINE}->add_to_subhash($key,$val);
    }
    return(1);
}


1;
