package Substitute_Engine;

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

    my $platform = shift;

    # check parameters
    if ( ! defined $platform ) {
	croak "Missing platform";
	return;
    } elsif ( ref $platform ) {
	croak "Invalid filename argument '$platform'";
    } 

    bless $self, $class;
    
    if ( $self->build_subhash($platform) ) {
	return $self;   
    } else {
	return;
    }
}

sub build_subhash {

    my $self = shift;
    my $platform = shift;

    $self->{platform}=$platform;
    
    return($self);
}

sub print_subhash {

    my $self = shift;
    my $key;

    foreach $key (keys %$self) {
	print "--- $key $self->{$key} ---\n";
    }
    
    return($self);
}

sub add_to_subhash {
    my $self = shift;
    my $param= shift;
    my $value= shift;

#    if (!exists($self->{$param})) {    #SM# oder ueberschreiben?? ja, letztes zaehlt
	$self->{$param}=$value;
#    }
}

sub substitute {
    my $self = shift;
    my($strref)=@_;
    my($found,$c,@varlist1,@varlist2,$var);
    $c=0;
    $found=0;

    my $hashref=$self;

    return(0) if($$strref eq "");

    # search normal variables
    @varlist1=($$strref=~/\$([^\{\[\$\\\s\.\,\*\/\+\-\\\`\(\)\'\?\:\;\}]+)/g);
    foreach $var (sort {length($b) <=> length($a)} (@varlist1)) {
	if(exists($hashref->{$var})) {
	    my $val=$hashref->{$var};
	    $$strref=~s/\$$var/$val/egs;
#	    printlog(5,"                      substitute var1: %s = %s\n",$var,$val);
	    $found=1;
	}
    }

    # search variables in following form: ${name}
    @varlist2=($$strref=~/\$\{([^\{\[\$\\\s\.\,\*\/\+\-\\\`\(\)\'\?\:\;\}]+)\}/g);
    foreach $var (sort {length($b) <=> length($a)} (@varlist2)) {
	if(exists($hashref->{$var})) {
	    my $val=$hashref->{$var};
	    $$strref=~s/\$\{$var\}/$val/egs;
#	    printlog(5,"                      substitute var2: %s = %s\n",$var,$val);
	    $found=1;
	} 
    }

    # search eval strings (`...`)
    while($$strref=~/^(.*)(\`(.*?)\`)(.*)$/) {	
	my ($before,$evalall,$evalstr,$after)=($1,$2,$3,$4);
	my($val,$executeval);
        $val=undef;

#SM#$HOME PROBLEM!
#	print "\n\n\nBIN HIER IM SCHRAEGSTRICH -$$strref,$before,$evalall,$evalstr,$after- \n\n\n";

        if($evalstr=~/^\s*getstdout\((.*)\)\s*$/) {
#	    print "1\n";
            $executeval=$1;
#	    print "1: $executeval\n";
	    eval("{\$val=`$executeval`}");
#	    print "1: val= $val\n";
            $val=~s/\n/ /gs;
        } 
	if(!defined($val)) {
#	    print "2\n";
	    eval("{\$val=$evalstr;}");
	}
	if(!defined($val)) {
#	    print "3\n";
	    $val=eval("{$evalstr;}");
#	    print "3$val\n";
	}
	$val="" if(!defined($val));
	if($val ne "") {
#	    print "4\n";
	    $$strref=$before.$val.$after;
	} else {
#	    print "5\n";
	    last;
	}
#	printlog(5,"                      eval %s -> %s >%s<\n",$val,$$strref,$evalall);
    }

    # search for variables which could not be substitute
    @varlist1=($$strref=~/\$([^\{\[\$\\\s\.\,\*\/\+\-\\\`\(\)\'\?\:\;\}]+)/g);
    @varlist2=($$strref=~/\$\{([^\{\[\$\\\s\.\,\*\/\+\-\\\`\(\)\'\?\:\;\}]+)\}/g);
    if ( (@varlist1) || (@varlist2) ) {
	my $SUBSTITUTE_NOTFOUND=join(',',@varlist1,@varlist2);
	$found=-1;
#	printlog(5,"                      unknown vars in %s: %s\n",$$strref,$SUBSTITUTE_NOTFOUND);
    }
    return($found);

}

#####################################################################################################
# Utility functions
#####################################################################################################

1;


