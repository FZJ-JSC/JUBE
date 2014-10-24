package File_Manager;

use strict;
use Carp;

use JuBE::Substitute_Engine;
use Util::CheckArgs;

my $debug=2;

#####################################################################################################
# Interface functions
#####################################################################################################

sub new {
    my $self  = {};
    my $proto = shift;
    my $class = ref($proto) || $proto;

    my $file = shift;
    my $substitute_engine=shift;

    # check parameters
    if ( ! defined $file ) {
	croak "Missing filename in new";
	return;
    } elsif ( ref $file ) {
	croak "Invalid filename argument '$file'";
    } 

    $self->{_NAME} = $file;
    $self->{_CONTENT} = "";
    $self->{SUBSTITUTE_ENGINE}=$substitute_engine;

    bless $self, $class;

    if ( $self->_read_file ) {
	return $self;   
    } else {
	return;
    }

    return $self;   
}

sub substitute {

#jedes File einzeln?!!


#    my $self= ??!!?? file oder doch submod oder subs ... geklaert?
    my $self=shift;
    
#    my($substhashref,$parmhash,$dir)=@_;   #was muss ich hier uebergeben
    my $dir="."; #SM vorlaeufig
    my($infile,$outfile,$subhash)=@_;   
    my($subst,$data,$from,$to,$nc);
    my $fromtoh;

#    print "inout $infile, $outfile\n";

#    foreach $subst (keys(%{$substhashref})) {
#	my $infile=$_[1];
#	my $outfile=$_[2];
	$self->{SUBSTITUTE_ENGINE}->substitute(\$infile);
	$self->{SUBSTITUTE_ENGINE}->substitute(\$outfile);
	
#    print "inout2 $infile, $outfile\n";

#	printlog(2,"\t\t\t\t\t\t\t sub: %s -> %s\n",$infile,$outfile);
	
	$data=$self->{_CONTENT};
	
	# substitute params
#	my $subhash=$substhashref; #?????
	foreach $fromtoh (@$subhash) {
	    $from=$fromtoh->{"from"};         #ist das so abgespeichert?
	    $to=$fromtoh->{"to"};
#	    print "!!!!!!! from to $from $to !!!!!!\n";
	    $self->{SUBSTITUTE_ENGINE}->substitute(\$to);
	    $nc= $data=~s/$from/$to/gs;
	    my $tto=substr($to,0,80);
	    $tto.="..." if(length($to)>80);
	    $tto=~s/\n/ /gs;
#	    printlog(2,"\t\t\t\t\t\t(1)  #%02d %-20s -> %s\n",$nc,$from,$tto);
	}
	# second substitute step for recursive definitions
#	foreach $from (keys(%$subhash)) {
	foreach $fromtoh (@$subhash) {
	    $from=$fromtoh->{"from"};         #ist das so abgespeichert?
	    $to=$fromtoh->{"to"};
#	    $to=$subhash->{$from}->{to};
	    $self->{SUBSTITUTE_ENGINE}->substitute(\$to);
	    $nc= $data=~s/$from/$to/gs;
	    my $tto=substr($to,0,80);
	    $tto.="..." if(length($to)>80);
	    $tto=~s/\n/ /gs;
#	    printlog(2,"\t\t\t\t\t\t(2)  #%02d %-20s -> %s\n",$nc,$from,$tto);
	}
	
	#write outfile
#    print " OUTFILE FUER SUB : $dir/$outfile \n";
#	if(! open(OUT,"> $dir/$outfile") ) { 
	if(! open(OUT,"> $outfile") ) { 
#	    printlog(-1,"... failed to open output file to %s/%s\n",$dir,$outfile);  return (-1);
	}
	print OUT $data;
	close(OUT);
#    }
}


#####################################################################################################
# Utility functions
#####################################################################################################

sub _read_file {

    my $self=shift;

#--- read and store original file             
    if( ! open(IN, "<$self->{_NAME}") ) {
	carp "Could not open '$self->{_NAME}'";
	return;
    }
    while (defined(my $line=<IN>)){
	$self->{_CONTENT}.=$line;
    }
    close(IN);

}

1;


