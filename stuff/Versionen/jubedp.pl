#!/usr/bin/perl -w

use strict;
use JuBE::XML_Manager;

my($debug)=3;

my $include=JuBE::XML_Manager->new("bench.xml","BGP");

print ref($include),"\n" if($debug>=3);

$include->write_tree();

exit;
