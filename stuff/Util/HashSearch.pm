package HashSearch;

use strict;
use Carp;

my %resulthash = ();
my $resulthash_count = 0;

sub new{
    my $self={};
    my $proto = shift;
    my $class = ref($proto) || $proto;
    my $hashref=shift;

#    print "$hashref\n";
    #mit dem uebergebenen hash initialisieren!   
    if (ref($hashref)=~/HASH/) {
	$self->{_HASHREF} = $hashref;
    } else {
	$self->{_HASHREF} = {};
    }
    
#    foreach my $key (keys %{$self->{_HASHREF}}){
#	print "$key $self->{_HASHREF}->{$key}\n";
#    }

    bless($self, $class);
    return $self;
}

sub hashsearch{

    #prob: auf dem Objekt arbeiten, nicht auf uebergebenen hash
    my $proto = shift;
    my $class = ref($proto) || $proto;
    my ($searchhash_ref, %searchhash);
    my $searchstring = shift;

    #debug
#    print ">>>>>>>>>>>>>>$searchstring\n";
#    print ">>>>>>>>>>>>>>$proto->{_HASHREF}\n";
#    my @helpme=keys(%{$proto->{_HASHREF}});
#    print ">>>>>>>>>>>>>>@helpme\n\n";
    #edebug

    $searchhash_ref=$proto->{_HASHREF};
    if (ref($searchhash_ref)=~/HASH/) {
	%searchhash=%$searchhash_ref;
    } else {
	return 0;
    }
    
    # check arguments   
    if (!%searchhash){
#	carp("The hash given is blank");
	return 0;
    }    
    if (!$searchstring || $searchstring eq ""){
	carp("The expression given is blank");
	return 0;
    }
        
    %resulthash = ();
    $resulthash_count = 0;
    
    foreach my $hash_key (keys %searchhash){	
	if ($hash_key =~ m/$searchstring/){	 	    
	    $resulthash{ $hash_key } = $searchhash{$hash_key};
	    $resulthash_count++;
	}
	else {
	    my $hashsearchdeep=HashSearch->new($searchhash{$hash_key});
	    $hashsearchdeep->hashsearch($searchstring);
#	    hashsearch($class,$searchstring,$searchhash{$hash_key});
	}	
    }
        
    if ($resulthash_count >= 1){
	return(1);
    } else {
	return(0)
    }
    
}
    
sub resulthashdata{
    
    return %resulthash;
    
}

sub resulthashcount{
        
    return $resulthash_count;
    
}

1;
