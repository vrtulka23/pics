from typing import List
from pydantic import BaseModel
import re

from DPML_Converter import *
import ParseDPML

class DPML_Parser(BaseModel):
    code: str 
    ccode: str
    line: int
    source: str

    keyword: str = None
    dtype = str
    indent: int = 0
    name: str = None
    value: str = None
    isimport: bool = False           # is value an import path?
    defined: bool = False
    units: str = None
    comment: str = None
    dimension: List[tuple] = None
    options: List[BaseModel] = None

    def __init__(self, **kwargs):
        kwargs['ccode'] = kwargs['code']
        super().__init__(**kwargs)
    
    def _strip(self, text):
        self.ccode = self.ccode[len(text):]

    def isempty(self):
        return self.ccode.strip()==''

    def get_indent(self):
        m=re.match(r'^(\s*)',self.ccode)
        if m:
            self.indent = len(m.group(1))
            self._strip(m.group(1))

    def get_condition(self):
        m=re.match(r'^(([a-zA-Z0-9_.-]*@case)\s+("""(.*)"""|([^#]*)))', self.ccode)
        if m:
            self.name = m.group(2)
            if m.group(4):
                self.value = m.group(4)
            elif m.group(5):
                self.value = m.group(5)
            else:
                raise Exception("Invalid condition format on line: ", self.code)
            self._strip(m.group(1))
        else:
            m=re.match(r'^([a-zA-Z0-9_.-]*@(else|end))', self.ccode)
            if m:
                self.name = m.group(1)
                self._strip(m.group(1))
            
    def get_name(self):
        m=re.match(r'^([a-zA-Z0-9_.-]+)', self.ccode)
        if m:
            self.name = m.group(1)
            self._strip(m.group(1))
            if not self.isempty() and self.ccode[0]!=' ':
                raise Exception("Name has an invalid format: "+self.code)
        else:
            raise Exception("Name has an invalid format: "+self.ccode)
        
    def get_type(self):
        types = ['bool','int','float','str','table']
        for keyword in types:
            m=re.match(r'^(\s+'+keyword+')', self.ccode)
            if m:
                self.keyword = keyword
                self._strip(m.group(1))
                break
        if self.keyword is None:
            raise Exception(f"Type not recognized: {self.code}")
        
    def get_defined(self):
        if self.ccode[:1]=='!':
            self.defined = True
            self._strip('!')
        
    def get_dimension(self):
        pattern = r'^(\[([0-9:]+)\])'
        m=re.match(pattern, self.ccode)
        if m: self.dimension = []
        while m:
            if ":" not in m.group(2):
                self.dimension.append((int(m.group(2)),int(m.group(2))))
            else:
                dmin,dmax = m.group(2).split(':')
                self.dimension.append((
                    int(dmin) if dmin else None,
                    int(dmax) if dmax else None
                ))
            self._strip(m.group(1))
            m=re.match(pattern, self.ccode)

    def get_import(self):
        m=re.match(r'^({(.*)})', self.ccode)
        if m:
            self.isimport = True 
            self.value = m.group(2)
            if '?' in m.group(2):
                filename,query = m.group(2).split('?')
                self.source = filename
            else:
                self.source = m.group(2)
            if self.keyword=='import':
                if self.name:
                    self.name = f"{self.name}.{m.group(1)}"
                else:
                    self.name = f"{m.group(1)}"
            self._strip(m.group(1))

    def get_value(self):
        # Remove equal sign
        m=re.match(r'^(\s*=\s*)', self.ccode)
        if m:
            self._strip(m.group(1))
        else:
            raise Exception("Value has to be set after equal sign")
        # Import block values if required
        self.get_import()
        if self.value:
            return
        # If not block value, parse standard text value
        m=re.match(r'^(("""(.*)"""|"(.*)"|\'(.*)\'|([^# ]+)))', self.ccode)
        if m:
            # Reduce matches
            results = [x for x in m.groups()[1:] if x is not None]
            # Save value
            self.value = results[1]
            self._strip(m.group(1))
        if self.value is None:
            raise Exception("Value has to be set after equal sign")
        
    def get_units(self):
        m=re.match(r'^(\s+([^\s#=]+))', self.ccode)
        if m:
            self.units = m.group(2)
            with DPML_Converter() as p:
                p.expression(self.units)
            self._strip(m.group(1))
        
    def get_comment(self):
        m=re.match(r'^(\s*#\s*(.*))$', self.ccode)
        if m:
            self.comment = m.group(2)
            self._strip(m.group(1))
