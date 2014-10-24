package Benchmark_Manager;

use strict;
use Carp;

use Util::CheckArgs;

use JuBE::Substitute_Engine;

my $patint="([\\+\\-\\d]+)";    # Pattern for Integer number
my $patfp ="([\\+\\-\\d.Ee]+)"; # Pattern for Floating Point number
my $patwrd="([\^\\s]+)";        # Pattern for Work (all noblank characters)
my $patnint="[\\+\\-\\d]+";     # Pattern for Integer number, no () 
my $patnfp ="[\\+\\-\\d.Ee]+";  # Pattern for Floating Point number, no () 
my $patnwrd="[\^\\s]+";         # Pattern for Work (all noblank characters), no () 
my $patbl ="\\s+";              # Pattern for blank space (variable length)

my $debug=2;

#####################################################################################################
# Interface functions
#####################################################################################################

sub new {
    my $self  = {};
    my $proto = shift;
    my $class = ref($proto) || $proto;
 
    my $benchmark_tree=shift;
    my $benchmarkname=shift;
    my $substitute_engine=shift;

    $self=$benchmark_tree->{_CONTENT_TREE}->{"bench"}->[0]->{"benchmark"}->{$benchmarkname};
    $self->{SUBSTITUTE_ENGINE}=$substitute_engine;
    $self->{_PARAMETER_SPACE}->[0]="once";

    bless $self, $class;

    return $self;   
}

sub build_paramspace {
    my($self) = @_;
#    my $paramspace;
    
    my $params = $self->{'params'}->[0];

    my $bm_iter=0;

    my $taskaref;
    if(ref($self->{'tasks'}) eq "ARRAY") {
	$taskaref=$self->{'tasks'};
    } else {
	$taskaref=[$self->{'tasks'}];
    }
    foreach my $taskref (@{$taskaref}) {
	my($threadspertaskspec,$taskspernodespec,$nodesspec)=(1,1,1);
	$threadspertaskspec=$taskref->{threadspertask} if ($taskref->{threadspertask});
	$taskspernodespec=  $taskref->{taskspernode}   if ($taskref->{taskspernode});
	$nodesspec=         $taskref->{nodes}          if ($taskref->{nodes});
	foreach my $nodes (&_getsequence($nodesspec)) {
	    foreach my $taskspernode (&_getsequence($taskspernodespec)) {
		foreach my $threadspertask (&_getsequence($threadspertaskspec)) {
		    my (%paramlist,@param_name,@param_cnt,@param_ptr,$numparam,$numtests,%phash);
		    
		    $phash{nodes}=$nodes;		    $phash{taskspernode}=$taskspernode;
		    $phash{threadspertask}=$threadspertask; $phash{tasks}=$taskspernode*$nodes;
		    $phash{ncpus}=$threadspertask*$taskspernode*$nodes;		    		    
		    
		    foreach my $step (1,2) {
			foreach my $param (keys(%$params)) {
			    my $val=$params->{$param};
#			    &substitute(\$val,\%phash);                #substitute engine!test
			    $self->{SUBSTITUTE_ENGINE}->substitute(\$val);
			    $paramlist{$param}=[&_getsequence($val,$self)]; 
#			    print "Debug1 param: $param @{$paramlist{$param}}\n";
			    if(scalar @{$paramlist{$param}} == 1) {
				$phash{$param}=$paramlist{$param}->[0];   #phash?! paramlist?! l.u.
			    }
			}
		    }
			
		    my $c=0;
		    $numtests=1;
		    foreach my $param ( sort { $#{$paramlist{$a}} <=> $#{$paramlist{$b}} } (keys(%paramlist))) {
			$param_name[$c]=$param;
			$param_cnt[$c]=$#{$paramlist{$param}}+1;
			$numtests*=$param_cnt[$c];
#			print "\n-> ccc $numtests ccc <-\n";
			$param_ptr[$c]=0;
#			print "debug: $c-> $param_name[$c] $param_cnt[$c]\n";
#			print "\n-> $numtests, $param, @{$paramlist{$param}} : $c-> $param_name[$c] $param_cnt[$c] <-\n";
			$c++;			  
		    }
		    $numparam=$c;
#		    print "\n-> CCC $numtests CCC <-\n";
#		    }
		    
		    for(my $t=1;$t<=$numtests;$t++) { 
			my $str="";
			my %parmhash;
#			my $tproto=$bproto;
			
			for(my $p=0;$p<$numparam;$p++) { 
			    $str.=sprintf("[%s->%s]",$param_name[$p],$paramlist{$param_name[$p]}->[$param_ptr[$p]]);
			    if($param_name[$p]=~/\-/) {
				#field of parms
				my @plist=split(/\-/,$param_name[$p]);
				my @vlist=split(/\:/,$paramlist{$param_name[$p]}->[$param_ptr[$p]]);
				for(my $j=0;$j<=$#plist;$j++) {
				    $parmhash{$plist[$j]}=$vlist[$j];
#				    print "pvlist: $plist[$j] $vlist[$j]\n";
				}
			    } else {
				# scalar
				$parmhash{$param_name[$p]}=$paramlist{$param_name[$p]}->[$param_ptr[$p]];
#				print "parmhash:$parmhash{$param_name[$p]} \n";
			    }
#			    $tproto.="     ".$param_name[$p]."=\"".$paramlist{$param_name[$p]}->[$param_ptr[$p]]."\"\n";
			}
#			printlog(0,"\t\t\t\t\t   %2d: %s\n",$t,$str);
#			$parmhash{platform}=$platform;
#			$parmhash{pdir}=$opt_platformsdir;
#			$parmhash{benchname}=$benchname;
#			$parmhash{benchhome}=$pwd;
#			$parmhash{name}=$bench;
			$parmhash{nodes}=$nodes;
			$parmhash{taskspernode}=$taskspernode;
			$parmhash{threadspertask}=$threadspertask;
#			$parmhash{addopt}=$addopt;
			foreach my $param (keys(%phash)) {
#			    print "Debug param: $param $phash{$param}\n";
			    $parmhash{$param}=$phash{$param};
			}
#			$tproto.="     nodes=\"".$nodes."\"\n";
#			$tproto.="     taskspernode=\"".$taskspernode."\"\n";
#			$tproto.="     threadspertask=\"".$threadspertask."\"\n";		       			
			
			
			$self->{_PARAMETER_SPACE}->[$bm_iter]=\%parmhash;
			$bm_iter++;
			
			# search next parameter set
			if($numtests>1) {
			    my $done=0;
			    my $p=$numparam-1;
			    while(!$done) {
				$param_ptr[$p]++;
				if($param_ptr[$p]<$param_cnt[$p]) {
				    $done=1;
				} else {
				    $param_ptr[$p]=0;
				    $p--;
				    $done=1 if($p<0); # only for fun
				}
			    }
			}
			
		    }
		}
	    }
	}
    }
    return($self->{_PARAMETER_SPACE});
}

sub get_paramspace {
    my($self) = @_;         
    return($self->{_PARAMETER_SPACE}); 
}

sub print_paramspace {
    my($self) = @_;         
    #iteration? -> Schleife
#    print ref($paramspace); -> ARRAY 
    foreach my $elem (keys %{$self->{_PARAMETER_SPACE}->[0]}) {
	print ">> $self->{_PARAMETER_SPACE}->[0]->{$elem}\n";
    }


}

sub get_name {
    my($self) = @_;
    
    return($self->{'name'});
}

sub is_active {
    my($self) = @_;
    
    return($self->{'active'});
}

#####################################################################################################
# Utility functions
#####################################################################################################

sub _getsequence {
    my($str,$benchref)=@_;
    my($spec,$i);
    my (@sequence,@result);
    # only if evaluated
#    print "str $str\n";
    return if ($str=~/\$/);
    if($str=~/^$patwrd\($patwrd\)$/) {
	my ($func,$parms)=($1,$2);
#	print "getsequence: $func $parms\n";
#	printlog(-1,"%s",Dumper($benchref));
	@result=&_readperm(split(/\s*,\s*/,$parms),$benchref) if ($func eq "readperm");
	@result=&_factorperm(split(/\s*,\s*/,$parms),$benchref) if ($func eq "factorperm");
	@result=&_factorpermbound(split(/\s*,\s*/,$parms),$benchref) if ($func eq "factorpermbound");
	@result=&_iterator(split(/\s*,\s*/,$parms),$benchref) if ($func eq "iterator");	
	@result=&_predefinedparams(split(/\s*,\s*/,$parms),$benchref) if ($func eq "predefinedparams");
    } else {
	if($str!~/\,/) {
	    push(@sequence,$str);
#	    print "sequence @sequence\n";
	} else {
	    @sequence=split(/,/,$str);
	}
	foreach $spec (@sequence) {
	    if($spec=~/(\d+)\.\.(\d+)/) {
		my($a,$e)=($1,$2);
		for($i=$a;$i<=$e;$i++) {
		    push(@result,$i);
		}
	    } else {
		push(@result,$spec);
	    }
	}
    }
#    print "debug: getsequence >$str< -> $result[0]:$result[1]:$result[2]\n";
    return(@result);
}

sub _readperm {
    my($maptagname,$x,$y,$z,$t,$n,$benchref)=@_;
    my(@result);
    if($benchref->{$maptagname} && $benchref->{$maptagname}->[0]->{"map"}) {
	my $ref=$benchref->{$maptagname}->[0]->{"map"};
	if($ref->{$n}) {
	    my $spec; 
	    foreach $spec (split(/\s+/,$ref->{$n}->{"spec"})) {
		my ($px,$py,$pz,$pt)=split(/:/,$spec);
		if( ($px*$py*$pz*$pt == $n) 
		    && ($x % $px == 0)
		    && ($y % $py == 0)
		    && ($z % $pz == 0)
		    && ($t % $pt == 0)
		    )
		 {
		    push(@result,$spec);
		}
	    }
	} else {
#	    printlog(-1,"... no mapping entry found for $maptagname and tasknumber=%s\n",$n);
	}
    } else {
#	printlog(-1,"... no mapping entry found for %s\n",$maptagname);
    }
    return(@result);
}

sub _iterator {
    my($start,$end,$op,$benchref)=@_;
    my(@result,$val,$opr);
    if($op=~/[+]$patfp/) {
	$opr=$1;
	$val=$start;
	while($val<=$end) {
	    push(@result,$val);
	    $val+=$opr;
	}
    } elsif($op=~/[*]$patfp/) {
	$opr=$1;
	$val=$start;
	while($val<$end) {
	    push(@result,$val);
	    $val*=$opr;
	}
    }elsif($op=~/[-]$patfp/) {
	$opr=$1;
	$val=$start;
	while($val>=$end) {
	    push(@result,$val);
	    $val-=$opr;
	}
    } elsif($op=~/[\/]$patfp/) {
	$opr=$1;
	$val=$start;
	while($val>=$end) {
	    push(@result,$val);
	    $val/=$opr;
	}
    }else {
	@result=();
    }
    return(@result);
}

# subrutine to read in predefined parameter sets, as a function of tasks and tagname
# args:  - xml target tag name
#        - number of tasks
#        - request, i.e. which parameter shall be read in
#        - reference to bench
sub _predefinedparams {
    my($paramtagname, $tasks, $request, $benchref)=@_;
    my $result;

#    printlog(5,"predefined parameter call: $paramtagname, $tasks, $request\n", 0);

    if($benchref->{$paramtagname} && $benchref->{$paramtagname}->[0]->{"predefparam"}) {
#	print Dumper($benchref->{$paramtagname}->[0]->{"predefparam"});
	my $paranmb = @{$benchref->{$paramtagname}->[0]->{"predefparam"}};
	my $parafound = 0;
	for(my $paracnt=0; $paracnt < $paranmb; $paracnt++)
	    {
		my $ref=$benchref->{$paramtagname}->[0]->{"predefparam"}->[$paracnt];
		if( $ref->{$request} && $ref->{"tasks"}==$tasks)
		{
		    $result=$ref->{$request};
		    $parafound = 1;
		}
	    }
	if($parafound == 0)
	{
#	    printlog(-1, "... could not find request $request in predefined params ($paramtagname) for $tasks tasks\n",0);
	}
	else
	{
#	    printlog(5, "request: $request; value: $result\n", 0);
	}

    }
    else {
#	printlog(-1,"... no mapping entry found for %s\n",$paramtagname);
    }
    return $result;
}


sub _factorperm {
    my($x,$y,$z,$t,$n,$benchref)=@_;
    my(@result);
    my (@factors, $i, $limit);
    # factors of $n
    for (my $i = 2; $i <= $n; $i++) {
        last if $i > ($n / 2);
        if ($n % $i == 0)  {  
            push @factors, $i;
        }
    }
    # matches
    my (@matches, @previous_bases, $skip);
    my @base1 = my @base2 = my @base3 = my @base4 = @factors;

    for my $base1 (@base1) { 
	for my $base2 (@base2) { 
	    for my $base3 (@base3) { 
		for my $base4 (@base4) { 
		    if ($base1 * $base2 * $base3 * $base4 == $n) {
			$skip=0;
			$skip=1 if (( ($x % $base1) != 0) && ($x != $base1));
			$skip=1 if (( ($y % $base2) != 0) && ($y != $base2));
			$skip=1 if (( ($z % $base3) != 0) && ($z != $base3));
			$skip=1 if (( ($t % $base4) != 0) && ($t != $base4));
			push(@result, "$base1:$base2:$base3:$base4") if(!$skip);
		    }
		}
	    }
	}
    }
    return(@result);
}

sub _factorpermbound {
    my($x,$y,$z,$t,$n,$benchref)=@_;
    my(@result);
    my (@factors, $i, $limit);
    # factors of $n
    for (my $i = 2; $i <= $n; $i++) {
        last if $i > ($n / 2);
        if ($n % $i == 0)  {  
            push @factors, $i;
        }
    }
    push(@factors,1);
    push(@factors,$n);

    # matches
    my (@matches, @previous_bases, $skip);
    my @base1 = my @base2 = my @base3 = my @base4 = @factors;

    for my $base1 (@base1) { 
	for my $base2 (@base2) { 
	    for my $base3 (@base3) { 
		for my $base4 (@base4) { 
		    if ($base1 * $base2 * $base3 * $base4 == $n) {
			$skip=0;
			$skip=1 if (( ($x % $base1) != 0) && ($x != $base1));
			$skip=1 if (( ($y % $base2) != 0) && ($y != $base2));
			$skip=1 if (( ($z % $base3) != 0) && ($z != $base3));
			$skip=1 if (( ($t % $base4) != 0) && ($t != $base4));
			push(@result, "$base1:$base2:$base3:$base4") if(!$skip);
		    }
		}
	    }
	}
    }
    return(@result);
}

sub _make_sub_hsh {
    my($self) = @_;
    
    my ($key,$val,$rc);
    my $platformparamsref=$self->{'params'}->[0];

    foreach $key (keys(%{$platformparamsref})) {	#SM# s.Platform_mngr--- in Util-Modul vereinbar?
	$val=$platformparamsref->{$key};
	$rc=$self->{SUBSTITUTE_ENGINE}->substitute(\$val);
	$platformparamsref->{$key}=$val;
	$self->{SUBSTITUTE_ENGINE}->add_to_subhash($key,$val);
    }
    return(1);
   
}

1;


