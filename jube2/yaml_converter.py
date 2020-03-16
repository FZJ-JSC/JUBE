from lxml import etree
import xml.dom.minidom as DOM
import yaml
import jube2.util.output
import os


class Conv():
    def __init__(self, path):
        self.path = path
        yaml.add_constructor("!include", self.yaml_include)
        
    def convert(self):
        """ Opens given file, make a Tree of it and print it """
        file_handle = open(self.path,"r")
        data = file_handle.read()
        a = yaml.load(data,  Loader=yaml.Loader)
        tree = XMLTree(a)
        xml = jube2.util.output.element_tree_tostring(tree.tree, encoding="UTF-8")
        xml = etree.fromstring(xml)
        with open(os.path.basename(os.path.splitext(self.path)[0] + '.xml'),
                  'w') as f: 
            f.write(etree.tostring(xml, pretty_print=True).decode())
        
        return os.path.basename(os.path.splitext(self.path)[0] + '.xml')
        
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
    allowed = {"headtag": ["benchmark", "parameterset", "step", "fileset",
                           "substituteset", "analyser", "result", "patternset",
                           "selection","include-path"],
                "analyse": ["file"], "analyser": ["use", "analyse"],
                "fileset": ["link", "copy", "prepare"], 
                "include_path": ["path"], "parameterset": ["parameter"],
                "patternset": ["pattern"], "result": ["use", "table", "syslog"],
                "selection": ["not", "only"], "step": ["use", "do"],
                "substituteset":["iofile", "sub"], "syslog": ["key"],
                "table": ["column"]}
    
    def __init__(self, dict):
        """ Create the Treeelement Jube """
        self.dict = dict
        self.tree = etree.Element('jube')
        self.current_sub = self.tree
        self.create_headtags(self.dict)

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
                
        self.create_headtags(next_subtags, local_sub)
        
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
             
    def create_headtags(self, dict, current_sub = None):
        """ Search for the headtags in given dictionary """
        for key in dict:
            for attr_and_tags in dict[key]:
                if key == "benchmark":
                    self.create_benchmark(attr_and_tags)
                elif key in self.allowed["headtag"]:
                    self.create_tag(key, attr_and_tags, current_sub)
                    
    def create_tag(self, name, attr_and_tags, current_sub):
        """ Create the Subtag name, search for known tags
            and set the given attributes"""
        if name in self.allowed:
            allowed_tags = self.allowed[name]
            local_sub = etree.SubElement(self.current_sub \
                                     if current_sub is None else current_sub,
                                     name)
            for key,value in attr_and_tags.items():
                if key in allowed_tags:
                    if key in ["analyse", "table", "syslog"]:
                        self.create_tag(key, value, local_sub)
                    else:
                        self.create_endtag(key, value, local_sub)
                else:
                    local_sub.set(key, str(value))

