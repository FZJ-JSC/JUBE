#
#  CheckArgs.pm
#
#  Version 13.April 2000
#
#  Ueberprueft, ob eine Argumentliste gewisse
#  Anforderungen erfuellt. Im Moment wird
#  unterstuetzt:
#
#   \[$@%] eine Referenz auf Skalar, Array, bzw. Hash
#   $      ein Skalar
#
#  Wozu ?   Nun - Methoden lassen sich leider nicht mit
#           Prototypen versehen.
#
package CheckArgs;

use Carp;

sub check {
    my $cstring = shift || croak 'Usage: checkArgs::check($cstring, @_)';
    my $argnr = 0;

    while( $cstring ) {
	$argnr++;
	return "Too few arguments" unless( @_ );
	if( $cstring =~ s/^\\\$// ) {
	    return "Scalar ref expected as Argument nr $argnr"
		unless( ref shift eq "SCALAR" );
	} elsif( $cstring =~ s/^\\@// ) {
	    return "Array ref expected as Argument nr $argnr"
		unless( ref shift eq "ARRAY" );
	} elsif( $cstring =~ s/^\\%// ) {
	    return "Hash ref expected as Argument nr $argnr"
		unless( ref shift eq "HASH" );
	} elsif( $cstring =~ s/^\$// ) {
	    return "Scalar expected as Argument nr $argnr"
		unless( ref shift eq "" );
	} else {
	    return "invalid cstring Argument in checkArgs::check '$cstring'";
	}
    }
    return "Too many arguments" if( @_ );
}
1;
