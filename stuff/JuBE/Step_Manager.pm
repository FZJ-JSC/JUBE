package Step_Manager;

use strict;
use Carp;

use Util::CheckArgs;

my $debug=2;

#####################################################################################################
# Interface functions
#####################################################################################################

sub new {
    my $self  = {};
    my $proto = shift;
    my $class = ref($proto) || $proto;
 
    my $benchmark_tree=shift;
    my $benchmark_name=shift;
    my $substitute_engine=shift;
    
    $self=$benchmark_tree->{_CONTENT_TREE}->{"bench"}->[0]->{"benchmark"}->[0]->{"stepdef"}->{$benchmark_name};
    #nachgucken!!!!!


    $self->{SUBSTITUTE_ENGINE}=$substitute_engine;

    bless $self, $class;

    return $self;   
}

sub handle_steps {

    my $self=shift;

    my $steporder=_get_steporder($self);
    my @steporder=split(/\s*,\s*/,$actionorder);
    
    foreach my $step (@steporder) {      #--SM todo semantik checks
      # proceed_step, save_state, check 
    }
}


#####################################################################################################
# Utility functions
#####################################################################################################

sub _get_steporder {
    my $self=shift;
    return($self->{"steporder"}->[0]->{"steps"});     
}

sub _get_step {
 # gibt hash der step zurueck, der je nach Typ anders aussieht
    my $self=shift;
    my $stepname=shift;
    return($self->{"step"}->{$stepname});
}

1;


