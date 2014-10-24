#
# Logger packer for JuBE
# stores and read data benchmark runs in/from XML files
#
package Logger;
use strict;
use Carp;
use Storable qw(dclone); 
use Data::Dumper;

my($debug)=0;

sub new {
    my $self  = {};
    my $proto = shift;
    my $class = ref($proto) || $proto;
    printf("\tjube_logger: new %s\n",ref($proto)) if($debug>=3);
    $self->{DATA}        = {};
    $self->{XS}          = XML::Simple->new();

    bless $self, $class;
    return $self;
}

# member function init_with($otherlogger): 
# initialize internal data structure with data of another logger
# 
sub init_with {
    my($self) = shift;
    my($otherlogger) = shift;
    $self->{DATA}      =dclone($otherlogger->get_data_ref());
    return(1);
}

# member function log($section,$hashref): 
# hashref is a hash of key value pairs (must at least contain 'name' and 'value')
# stores one entry in internal log
# 
sub log {
    my($self) = shift;
    my($section) = shift;
    my($hashref) = shift;
    my($nosub) = shift;
    my $name=$hashref->{"name"};
    $nosub="SUB" if(!$nosub);
    if($name=~/^\s*$/) {
	print "ERROR in logger: name is empty ",caller(),"\n";
	croak "error in logger";
    }
    if($nosub ne "NOSUB") {
	# remember scalar values in substitute DB
	if (!ref($hashref->{"value"})) {
#	printf("logger: %-20s -> %-20s (%s)\n",$name,$hashref->{"value"},ref($hashref->{"value"}));
	    $self->{DATA}->{SUBSTITUTE}->{$name}=$hashref->{"value"};
	}
    }

    push (@{$self->{DATA}->{$section}->[0]->{"entry"}},dclone($hashref));
    return(1);
}

# member function log_substitute_only($key,$value): 
# logs only a key value pair in SUBSTITUTE data structure
# 
sub log_substitute_only {
    my($self) = shift;
    my($key) = shift;
    my($value) = shift;
    $self->{DATA}->{SUBSTITUTE}->{$key}=$value;
    return(1);
}


# member function writetofile($filename): 
# 
sub writetofile {
    my($self) = shift;
    my($filename) = shift;

    if(! open(OUT,"> $filename") ) { 
	print("... failed to open logger file $filename\n");  return (-1);
    }
    my $header = '<?xml-stylesheet href="jube_report.xsl" type="text/xsl"?>';
#    print OUT $header,"\n";
#    print OUT $self->{XS}->XMLout($header, noescape => 1);
    print OUT $self->{XS}->XMLout($self->{DATA}, AttrIndent => 1, KeyAttr => "name", RootName => "benchrun" );
    close(OUT);

    if(! open(OUT,"> $filename.dump") ) { 
	print("... failed to open logger file $filename.dump\n");  return (-1);
    }
    print OUT Dumper($self->{DATA});
    close(OUT);
    
    return(1);
}

# member function readfromfile($filename): 
# 
sub readfromfile {
    my($self) = shift;
    my($filename) = shift;

    if(! -f $filename ) { 
	print("... failed to open logger file $filename\n");  return (-1);
    }

    $self->{DATA}=$self->{XS}->XMLin($filename, KeyAttr => { }, ForceArray => 1);

    if(! open(OUT,"> $filename.readdump") ) { 
	print("... failed to open logger file $filename.readdump\n");  return (-1);
    }
    print OUT Dumper($self->{DATA});
    close(OUT);
    
    return(1);
}

# member function getdataref(): 
# returns reference to internal data structure
# 
sub get_data_ref {
    my($self) = shift;
    return($self->{DATA});
}

# member function getdataref(): 
# returns reference to internal data structure
# 
sub get_substitute_hashref {
    my($self) = shift;
    return($self->{DATA}->{SUBSTITUTE});
}

1;
