#!/usr/bin/python3
import numpy as np
import re
import os

def parse_line(line):
    if (len(line.strip())==0):
        indent = 0
    else:
        indent = len(line)-len(line.lstrip(' '))        # calculate indentation
    line = line.strip()                                 # remove whitespaces on both sides
    split = line.split('#', 1)                          # separate code and comments
    code = split[0].strip()                             # get code
    comment = split[1].strip() if len(split)>1 else ""  # get comments
    return indent, code, comment

def new_node(**kwargs):
    node = { 
        'indent': 0,
        'code': '',
        'comments': [],
        'nodes': [],
        'file_name': '',
        'line_number': 0
    }
    node.update(kwargs)
    return node

def parse_lines(file_pics):
    nodes = {}
    with open(file_pics,'r') as f:
        line = f.readline()
        line_number = 1
        nodes = []
        while line:
            indent, code, comments = parse_line(line)
            
            if code[:2]=="@ ":
                line = f.readline()
                line_number += 1
                continue            

            elif code[:2]=="& ":                 # include a new file
                m = re.match("\& (.*)", code)
                file_include = m.group(1)
                nodes.extend( parse_lines(file_include) )
                print(f"Including file '{file_include}'")
                
            elif code[:2]=="% ":                 # parse template
                m = re.match("\% (.*) (.*)", code)
                file_template = m.group(1)
                file_output = m.group(2)
                print(f"Parsing template '{file_include}' as '{file_output}'")

            else:                                # parse a new node
                nodes.append(new_node(
                    indent = indent,
                    code = code,
                    comments = [comments] if comments else [],
                    file_name = file_pics,
                    line_number = line_number
                ))
                
            line = f.readline()
            line_number +=1
    return nodes

def parse_indent(nodes, indent_current=0):
    node_tree = []
    while len(nodes)>0:
        indent_next = nodes[0]['indent']
        if (indent_next%2>0):
            print(indent_next)
            raise Exception("Invalid indent "+str(indent_next)+" if file '"+nodes[0]['file_name']+"' on line "+str(nodes[0]['line_number']))
        if indent_next==indent_current:
            node_current = nodes.pop(0)
            node_tree.append(node_current)
        elif indent_next>indent_current:
            node_tree[-1]['nodes'] = parse_indent(nodes, indent_next)
        else:
            return node_tree
    return node_tree

def group_comments(nodes):
    nnodes = [new_node()]
    for node in nodes:
        if len(node['code'])==0 and len(node['comments'])>0:
            if len(nnodes[-1]['code'])>0 or len(nnodes[-1]['comments'])>0:
                nnodes[-1]['comments'].extend(node['comments'])
            else:
                nnodes.append(new_node(
                    comments = node['comments']
                ))
        else:
            nnodes.append(node)
    nodes = [new_node()]
    for node in reversed(nnodes):
        if len(node['code'])==0 and len(node['comments'])>0:
            if len(nodes[0]['code'])>0 or len(nodes[0]['comments'])>0:
                comments = nodes[0]['comments']
                nodes[0]['comments'] = node['comments']
                nodes[0]['comments'].extend(comments)
            else:
                nodes.insert(0,new_node(
                    comments = node['comments']
                ))
        else:
            nodes.insert(0,node)
    return nodes

def parse_types(nodes):
    return nodes

def print_nodes(nodes):
    for node in nodes:
        if node['comments']:
            comments = '# '+'\n'.join(node['comments'])
        else:
            comments = ''
        print("%03d %14s"%(node['line_number'],node['file_name']),' '*node['indent'], node['code'], comments)
        if node['nodes']:
            print_nodes(node['nodes'])

def parse_file(file_pics):
    if not os.path.exists(file_pics):
        raise Exception(f"File was not found: {file_pics}")
    else:
        print(f"Parsing file '{file_pics}'")
    nodes = parse_lines(file_pics)
    nodes = group_comments(nodes)
    nodes = parse_types(nodes)
    nodes = parse_indent(nodes)
    print_nodes(nodes)    
    return nodes

def main():
    file_pics = 'problem.pics'
    nodes = parse_file(file_pics)
    
if __name__ == "__main__":
    main()
