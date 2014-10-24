#!/usr/bin/perl -w

use XML::Simple;
use Data::Dumper;

# Objekt erstellen
my $xml = new XML::Simple;

# XML-Datei einlesen
my $data = $xml->XMLin("Benchmarks/bench.xml", KeepRoot=>1, KeyAttr => {'benchmark' => "+name",'include' => "+file"},ForceArray => 1);

#my $data = $xml->XMLin("Benchmarks/bench.xml", KeepRoot=>1, KeyAttr => {'benchmark' => "+name",'include' => "+file"},ForceArray=>[qr//]);

# Ausgabe
print Dumper($data); 
