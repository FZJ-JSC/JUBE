package Platform;

use strict;
use Carp;
use vars qw ($AUTOLOAD);

#use XML::Simple qw(:strict); 
#my $library = XMLin($filename, ForceArray => 1, KeyAttr => {}, ); 
#foreach my $book (@{$library->{book}}) { 
#    print $book->{title}->[0], "\n" 
#}

use XML::LibXML; 

sub new {
    my $self  = {};
    my $proto = shift;
    my $class = ref($proto) || $proto;
    my $err;

    ($err = CheckArgs::check('$', @_)) && croak $err; 

    my $platform_file = shift;

    my $parser = XML::LibXML->new(); 
    $self->{DOC} = $parser->parse_file($platform_file); 

    foreach my $params ($self->{DOC}->findnodes('/platforms')) { 
	my($attr) = $params->findnodes('./platform'); 
	print $attr->to_literal, "\n" 
    } 
    bless $self, $class;
    return $self;   
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

1;
