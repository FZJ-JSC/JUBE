package Step_Handler;

use strict;
use Carp;

use JuBE::File_Manager;

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
    my $stepname=shift;
    my $substitute_engine=shift;
    my $parameter_space=shift;
    
    $self=$benchmark_tree->{_CONTENT_TREE}->{"bench"}->[0]->{"steps"}->[0]->{"stepdef"}->{$stepname};
    $self->{SUBSTITUTE_ENGINE}=$substitute_engine;
    $self->{_PARAMETER_SPACE}=$parameter_space;
    $self->{_SCOPE}=$benchmark_tree->{_CONTENT_TREE}->{"bench"}->[0]->{"steps"}->[0]->{"stepdef"}->{$stepname}->{"scope"};
    bless $self, $class;

    return $self;   
}

sub handle_actions {

    my $self=shift;

    my $actionorder=_get_actionorder($self);
    my @actionorder=split(/\s*,\s*/,$actionorder);
    
    foreach my $action (@actionorder) {      #--SM todo semantik checks
      # proceed_step, save_state, check 
	my $actiontype=_get_actiontype($self,$action);
	my $actionscope=_get_actionscope($self,$action);
#	print "actionscope $actionscope\n";	    
      SWITCH: {
	  if ($actiontype=~/^copy$/)       { _action_copy(_get_from_to($self,$action)); last SWITCH; }
	  if ($actiontype=~/^copydir$/)    { _action_copydir(_get_from_to_dir($self,$action)); last SWITCH; }
	  if ($actiontype=~/^substitute$/) { _action_substitute($self,$action); last SWITCH; }
	  if ($actiontype=~/^execute$/)    { _action_execute($self,$action,$actionscope);    last SWITCH; }
	  carp "Unknown actiontype $actiontype\n";
	}  	
    }
}



#####################################################################################################
# Utility functions
#####################################################################################################

sub _get_actionorder {
    my $self=shift;
    return($self->{"actionorder"}->[0]->{"actions"});     
}

sub _get_action {
 # gibt hash der action zurueck, der je nach Typ anders aussieht
    my $self=shift;
    my $actionname=shift;
    return($self->{"action"}->{$actionname});
}

sub _get_actiontype {
    my $self=shift;
    my $actionname=shift;
        
    return($self->{"action"}->{$actionname}->{"type"}); 
#    foreach my $temp (values %{$self->{action}->{$actionname}})    {    }    
}

sub _get_actionscope {
    my $self=shift;
    my $actionname=shift;
    
    if (exists($self->{"action"}->{$actionname}->{"scope"})) {
	return($self->{"action"}->{$actionname}->{"scope"}); 
    } else {
	return("once");
    }
#    foreach my $temp (values %{$self->{action}->{$actionname}})    {    }    
}

sub _action_copydir {
    my $fromfiles=$_[0];
    my $fromdir=$_[1];
    my $todir=$_[2];

    my @from = map { $fromdir . "/" . $_ } @$fromfiles;

    foreach my $file (@from) {
	my $cmd="cp -p ${file} ${todir}";
#	print "copy: $cmd\n";
#       system($cmd);    
    }
}

sub _get_from_to_dir {
    my $self=shift;
    my $actionname=shift;

    my @fromfiles=split(/ /,$self->{action}->{$actionname}->{"from"}->[0]->{"files"});
    my $fromdir=$self->{action}->{$actionname}->{"from"}->[0]->{"directory"};
    my $todir=$self->{action}->{$actionname}->{"to"}->[0]->{"directory"};
    return(\@fromfiles,$fromdir,$todir); 
}

sub _action_copy {
    my $from=$_[0];
    my $to=$_[1];
    my $cmd="cp -p ${from} ${to}";
    print "copy: $cmd\n";
#    system($cmd);    
}

sub _get_from_to {
    my $self=shift;
    my $actionname=shift;

    return($self->{action}->{$actionname}->{"from"},$self->{action}->{$actionname}->{"to"}); 
}

sub _action_execute {
    my $self=shift;
    my $action_name=shift;
    my $action_scope=$self->{_SCOPE};
    my $command=$self->{"action"}->{$action_name}->{"command"}->[0];
    if ($action_scope eq "once") {
	print("command: $command\n");
#       system($command);    
    } else {
	print("parameterspace-lauf\n");
	foreach my $ind (0..$#{$self->{_PARAMETER_SPACE}}) {
	    print "----> $ind: ",keys(%{$self->{_PARAMETER_SPACE}->[$ind]}),"\n";
	    foreach my $elem (keys %{$self->{_PARAMETER_SPACE}->[$ind]}) {
		print ">>>> $elem : $self->{_PARAMETER_SPACE}->[$ind]->{$elem}\n";
	    }
	}
	#Parameterspace durchlaufen mit Befehl!
	#iteration ?! <-uebergeben oder mehrfacher aufruf, eigentlich aussen, da hier generalisiert UP
	#kann ich erst hier die subs machen, da ich erst hier den aktuellen parameterset habe??!definitiv ja..?!
	#sub abhaengig vom parameterset, nicht von execute, muss aber zusammenpassen..strategie?
    }
}

sub _action_substitute {          #substitute engine!!!!!!

    my $self=shift;
    my $action_name=shift;
    my $infile=$self->{"action"}->{$action_name}->{"infile"}; 
    my $outfile=$self->{"action"}->{$action_name}->{"outfile"};
    my $subpath=$self->{"action"}->{$action_name}->{"sub"};

    #Aufruf File-Manager..
    my $fmgr=File_Manager->new($infile,$self->{SUBSTITUTE_ENGINE});
#subhash in substitute-engine integrieren?! ja, aber nur temporaer
    $fmgr->substitute($infile,$outfile,$subpath);    
}


1;


