#!/usr/bin/perl -w

use strict;
use XML_Manager;

my($debug)=3;

my $include=XML_Manager->new("bench.xml","BGP");

print ref($include),"\n" if($debug>=3);

$include->write_tree();

exit;
