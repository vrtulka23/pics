from pydantic import BaseModel
import re

class PPML_Parser:

    def _strip(self, text):
        self.ccode = self.ccode[len(text):]

    def _isempty(self):
        return self.ccode.strip()==''

    def _get_indent(self):
        m=re.match('^(\s*)',self.ccode)
        if m:
            self.indent = len(m.group(1))
            self._strip(m.group(1))
            
    def _get_name(self):
        m=re.match('^([a-zA-Z0-9_.-]+)', self.ccode)
        if m:
            self.name = m.group(1)
            self._strip(m.group(1))
        else:
            raise Exception("Name has an invalid format: "+self.ccode)

    def _get_defined(self):
        if self.ccode[:1]=='!':
            self.defined = True
            self._strip('!')
            if self.node:
                self.node.defined = self.defined
        
    def _get_dimension(self):
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
        if self.node:
            self.node.dimension = self.dimension
        
    def _get_value(self):
        m=re.match('^(\s*=\s*("""(.*)"""|"(.*)"|\'(.*)\'|([^# ]+)))', self.ccode)
        if m:
            # Reduce matches
            results = [x for x in m.groups()[1:] if x is not None]
            # Save value
            self.value = results[1]
            self._strip(m.group(1))
        if self.value is None:
            raise Exception("Value has to be set after equal sign")
        if self.node:
            self.node.value = self.value
        
    def _get_units(self):
        m=re.match('^(\s*([^\s#=]+))', self.ccode)
        if m:
            self.units = m.group(2)
            self._strip(m.group(1))
            if self.node:
                self.node.units = self.units
        
    def _get_comment(self):
        m=re.match('^(\s*#\s*(.*))$', self.ccode)
        if m:
            self.comment = m.group(2)
            self._strip(m.group(1))
            if self.node:
                self.node.comments.append( self.comment )
