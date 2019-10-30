import xml.etree.ElementTree as ET
from lxml import etree
import xml.dom.minidom as DOM
import yaml
import jube2.util.output
import os
from eric6.ThirdParty.Pygments.pygments.lexers.data import YamlLexer


class Conv():
    def __init__(self, path):
        self.path = path
        yaml.add_constructor("!include", self.yaml_include)
        self.convert()
        
    def convert(self):
         """ Opens given file, make a Tree of it and print it """
        file_handle = open(self.path,"r")
        data = file_handle.read()
        a = yaml.load(data,  Loader=yaml.Loader)
        tree = XMLTree(a)
        xml = jube2.util.output.element_tree_tostring(tree.tree, encoding="UTF-8")
        xml = etree.fromstring(xml)
        print(etree.tostring(xml, pretty_print=True).decode())
        
    # adapted from http://code.activestate.com/recipes/577613-yaml-include-support/
    def yaml_include(self, loader, node):
        """ Constructor for the include tag"""
        _yaml_node_data = node.value.split(":")
        with open(os.path.join(os.path.dirname(self.path),_yaml_node_data[0])) as inputfile:
            _ = yaml.load(inputfile.read(), Loader=yaml.Loader)
            inputfile.close()
            if len(_yaml_node_data)>1:
                _ = eval("_"+_yaml_node_data[1])
                if len(_yaml_node_data)>2:
                    _ = eval(_yaml_node_data[2])
            return _
    #              leave out the [0] if your include file drops the key ^^^

        

class XMLTree():
    def __init__(self, dict):
        """ Create the Treeelement Jube """
        self.dict = dict
        self.tree = etree.Element('jube')
        self.current_sub = self.tree
        self.create_tags(self.dict)
        
    def create_analyse(self, attr_and_tags, current_sub):
        """ Create the Subelement analyse, search for known tags
            and set the given attributes"""
        local_sub = etree.SubElement(self.current_sub \
                                     if current_sub is None else current_sub,
                                     "analyse")
        for key,value in attr_and_tags.items():
            if key == "file":
                for file in value:
                    self.create_endtag("file", file, local_sub)
            else:
                local_sub.set(key, str(value))
    
    def create_analyser(self, attr_and_tags, current_sub):
        """ Create the Subelement analyser, search for known tags
            and set the given attributes"""
        local_sub = etree.SubElement(self.current_sub \
                                     if current_sub is None else current_sub,
                                     "analyser")
        for key,value in attr_and_tags.items():
            if key == "use":
                for use in value:
                    self.create_endtag("use", use, local_sub)
            elif key == "analyse":
                for analyse in value:
                    self.create_analyse(analyse, local_sub)
            else:
                local_sub.set(key, str(value))
    
    def create_benchmark(self, attr_and_tags):
        """ Create the Subelement benchmark, set the comment, the attributes and 
            search for tags in the left over"""
        local_sub = etree.SubElement(self.current_sub, "benchmark")
        next_subtags = {}
        for key,value in attr_and_tags.items():
            #Create attributes for benchmark
            if type(value) is not list:
                if key == "comment":
                    comment = etree.SubElement(local_sub, "comment")
                    comment.text = str(value)
                else:
                    local_sub.set(key, str(value))
            else:
                next_subtags[key] = value;
                
        self.create_tags(next_subtags, local_sub)
        
    def create_endtag(self, tag, attr, current_sub):
        """ Create the Subelement with the given name 
        and set the given attributes"""
        local_sub = etree.SubElement(self.current_sub \
                                     if current_sub is None else current_sub,
                                     tag)
        if type(attr) is not dict:
            local_sub.text = str(attr)
        else:
            for key, value in attr.items():
                if key == "_":
                    local_sub.text = str(value)
                else:
                    local_sub.set(key, str(value))
        
    def create_fileset(self, attr_and_tags, current_sub):
        """ Create the Subelement fileset, search for known tags
            and set the given attributes"""
        local_sub = etree.SubElement(self.current_sub \
                                     if current_sub is None else current_sub,
                                     "fileset")
        for key,value in attr_and_tags.items():
            if type(value) is not list:
                local_sub.set(key, str(value))
            elif key == "link":
                for link_attr in value:
                    self.create_endtag("link", link_attr, local_sub)
            elif key == "copy":
                for copy_attr in value:
                    self.create_endtag("copy", copy_attr, local_sub)
            elif key == "prepare":
                for prepare_attr in value:
                    self.create_endtag("prepare", prepare_attr, local_sub)
        
    def create_parameterset(self, attr_and_tags, current_sub):
        """ Create the Subelement parameterset, search for known tags
            and set the given attributes"""
        local_sub = etree.SubElement(self.current_sub \
                                     if current_sub is None else current_sub,
                                     "parameterset")
        for key,value in attr_and_tags.items():
            if key == "parameter":
                for para_attr in value:
                    self.create_endtag("parameter", para_attr, local_sub)
            else:
                local_sub.set(key, str(value))
                
    def create_patternset(self, attr_and_tags, current_sub):
        """ Create the Subelement patternset, search for known tags
            and set the given attributes"""
        local_sub = etree.SubElement(self.current_sub \
                                     if current_sub is None else current_sub,
                                     "patternset")
        for key,value in attr_and_tags.items():
            if key == "pattern":
                for pattern in value:
                    self.create_endtag("pattern", pattern, local_sub)
            else:
                local_sub.set(key, str(value))
                
    def create_result(self, attr_and_tags, current_sub):
        """ Create the Subelement result, search for known tags
            and set the given attributes"""
        local_sub = etree.SubElement(self.current_sub \
                                     if current_sub is None else current_sub,
                                     "result")
        for key,value in attr_and_tags.items():
            if key == "use":
                for use in value:
                    self.create_endtag("use", use, local_sub)
            elif key == "table":
                for table in value:
                    self.create_table(table, local_sub)
            elif key == "syslog":
                for syslog in value:
                    self.create_syslog(syslog, local_sub)
            else:
                local_sub.set(key, str(value))
                
    def create_selection(self, attr_and_tags, current_sub):
        """ Create the Subelement selection, search for known tags
            and set the given attributes"""
        local_sub = etree.SubElement(self.current_sub \
                                     if current_sub is None else current_sub,
                                     "selection")
        for key,value in attr_and_tags.items():
            if key == "not":
                for not_attr in value:
                    self.create_endtag("not", not_attr, local_sub)
            elif key == "only":
                for only in value:
                    self.create_endtag("only", only, local_sub)
            else:
                local_sub.set(key, str(value))
       
    def create_step(self, attr_and_tags, current_sub):
        """ Create the Subelement step, search for known tags
            and set the given attributes"""
        local_sub = etree.SubElement(self.current_sub \
                                     if current_sub is None else current_sub,
                                     "step")
        for key,value in attr_and_tags.items():
            if key == "use":
                for use in value:
                    self.create_endtag("use", use, local_sub)
            elif key == "do":
                for do in value:
                    self.create_endtag("do", do, local_sub)
            else:
                local_sub.set(key, str(value))
    
    def create_substituteset(self, attr_and_tags, current_sub):
        """ Create the Subelement substituteset, search for known tags
            and set the given attributes"""
        local_sub = etree.SubElement(self.current_sub \
                                     if current_sub is None else current_sub,
                                     "substituteset")
        for key,value in attr_and_tags.items():
            if "iofile" in key:
                for io_attr in value:
                    self.create_endtag("iofile", io_attr, local_sub)
            elif "sub" in key:
                for sub_attr in value:
                    self.create_endtag("sub", sub_attr, local_sub)
            else:
                local_sub.set(key, str(value))
    
    def create_syslog(self, attr_and_tags, current_sub):
        """ Create the Subelement syslog, search for known tags
            and set the given attributes"""
        local_sub = etree.SubElement(self.current_sub \
                                     if current_sub is None else current_sub,
                                     "syslog")
        for key,value in attr_and_tags.items():
            if key == "key":
                for key_attr in value:
                    self.create_key(key_attr, local_sub)
            else:
                local_sub.set(key, str(value))
    
    def create_table(self, attr_and_tags, current_sub):
        """ Create the Subelement table, search for known tags
            and set the given attributes"""
        local_sub = etree.SubElement(self.current_sub \
                                     if current_sub is None else current_sub,
                                     "table")
        for key,value in attr_and_tags.items():
            if key == "column":
                for column in value:
                    self.create_endtag("column", column, local_sub)
            else:
                local_sub.set(key, str(value))
                
                    
    def create_tags(self, dict, current_sub = None):
        """ Search for known tags in given dictionary """
        for key in dict:
            for attr_and_tags in dict[key]:
                if key == "benchmark":
                    self.create_benchmark(attr_and_tags)
                elif key == "parameterset":
                    self.create_parameterset(attr_and_tags, current_sub)
                elif key == "step":
                    self.create_step(attr_and_tags, current_sub)
                elif key == "fileset":
                    self.create_fileset(attr_and_tags, current_sub)
                elif key == "substituteset":
                    self.create_substituteset(attr_and_tags, current_sub)
                elif key == "analyser":
                    self.create_analyser(attr_and_tags, current_sub)
                elif key == "result":
                    self.create_result(attr_and_tags, current_sub)
                elif key == "patternset":
                    self.create_patternset(attr_and_tags, current_sub)
                elif key == "selection":
                    self.create_selection(attr_and_tags, current_sub)
        

file = Conv("/home/zam/wellmann/jube/examples/include/main.yaml")


