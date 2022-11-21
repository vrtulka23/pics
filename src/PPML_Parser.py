from typing import List
from pydantic import BaseModel
import re

class PPML_Parser(BaseModel):
    code: str 
    ccode: str
    line: int
    source: str

    keyword: str = None
    dtype = str
    indent: int = 0
    name: str = None
    value: str = None
    defined: bool = False
    units: str = None
    comment: str = None
    dimension: List[tuple] = None
    options: List[BaseModel] = None
    mods: List[BaseModel] = []

    def __init__(self, **kwargs):
        kwargs['ccode'] = kwargs['code']
        super().__init__(**kwargs)
    
    def _strip(self, text):
        self.ccode = self.ccode[len(text):]

    def isempty(self):
        return self.ccode.strip()==''

    def get_indent(self):
        m=re.match('^(\s*)',self.ccode)
        if m:
            self.indent = len(m.group(1))
            self._strip(m.group(1))
            
    def get_name(self):
        m=re.match('^([a-zA-Z0-9_.-]+)', self.ccode)
        if m:
            self.name = m.group(1)
            self._strip(m.group(1))
            if self.ccode[0]!='':
                raise Exception('Hello dolly')
        else:
            raise Exception("Name has an invalid format: "+self.ccode)
                    
    def get_type(self):
        types = ['bool','int','float','str','table']
        for keyword in types:
            m=re.match('^(\s+'+keyword+')', self.ccode)
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
        pattern = '^(\[([0-9:]+)\])'
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
        m=re.match('^({(.*)})', self.ccode)
        if m:
            with open(m.group(2),'r') as f:
                self.source = m.group(2)
                self.value = f.read()
            self._strip(m.group(1))
            
    def get_value(self):
        # Remove equal sign
        m=re.match('^(\s*=\s*)', self.ccode)
        if m:
            self._strip(m.group(1))
        else:
            raise Exception("Value has to be set after equal sign")
        # Import block values if required
        self.get_import()
        if self.value:
            return
        # If not block value, parse standard text value
        m=re.match('^(("""(.*)"""|"(.*)"|\'(.*)\'|([^# ]+)))', self.ccode)
        if m:
            # Reduce matches
            results = [x for x in m.groups()[1:] if x is not None]
            # Save value
            self.value = results[1]
            self._strip(m.group(1))
        if self.value is None:
            raise Exception("Value has to be set after equal sign")
        
    def get_units(self):
        m=re.match('^(\s+([^\s#=]+))', self.ccode)
        if m:
            self.units = m.group(2)
            if self.units not in ['cm','m','s','W/m2']:
                raise Exception(f"Invalid units: {self.units}")
            self._strip(m.group(1))
        
    def get_comment(self):
        m=re.match('^(\s*#\s*(.*))$', self.ccode)
        if m:
            self.comment = m.group(2)
            self._strip(m.group(1))
