"""
GROMACS CLI Command Parser using PLY
Supports commands from the GROMACS workflow flowchart:
- gmx pdb2gmx, editconf, solvate, grompp, mdrun, energy, and other analysis tools
"""

import ply.lex as lex
import ply.yacc as yacc
from typing import Dict, List, Any, Optional

class GromacsLexer:
    """Lexer for GROMACS command-line interface"""
    
    # Token list
    tokens = (
        'GMX',
        'COMMAND',
        'FLAG',
        'FILENAME',
        'STRING',
        'NUMBER',
        'INTEGER',
        'LPAREN',
        'RPAREN',
    )
    
    # GROMACS commands from the flowchart
    commands = {
        'pdb2gmx', 'editconf', 'solvate', 'grompp', 'mdrun', 'energy',
        # Additional common analysis commands
        'trjconv', 'rms', 'rmsf', 'gyrate', 'distance', 'angle',
        'mindist', 'hbond', 'sasa', 'cluster', 'density', 'potential',
        'genion', 'genrestr', 'make_ndx', 'do_dssp', 'rama'
    }
    
    def __init__(self):
        self.lexer = None
        
    def build(self, **kwargs):
        """Build the lexer"""
        self.lexer = lex.lex(module=self, **kwargs)
        return self.lexer
    
    # Token rules (ORDER MATTERS - longer/more specific patterns first!)
    
    def t_FLAG(self, t):
        r'-[a-zA-Z][a-zA-Z0-9]*'
        return t
    
    def t_LPAREN(self, t):
        r'\('
        return t
    
    def t_RPAREN(self, t):
        r'\)'
        return t
    
    def t_FILENAME(self, t):
        r'[a-zA-Z0-9_/\-]+\.(pdb|gro|top|mdp|tpr|xtc|trr|edr|cpt|xvg|ndx|itp|dat|log|out|tng|pqr)'
        return t
    
    def t_NUMBER(self, t):
        r'-?\d+\.\d+([eE][+-]?\d+)?'
        t.value = float(t.value)
        return t
    
    def t_INTEGER(self, t):
        r'-?\d+'
        t.value = int(t.value)
        return t
    
    def t_STRING(self, t):
        r'"[^"]*"|\'[^\']*\'|[a-zA-Z_][a-zA-Z0-9_]*'
        # Remove quotes if present
        if t.value.startswith('"') or t.value.startswith("'"):
            t.value = t.value[1:-1]
            return t
        
        # Check if it's 'gmx'
        if t.value == 'gmx':
            t.type = 'GMX'
            return t
        
        # Check if it's a recognized GROMACS command
        if t.value in self.commands:
            t.type = 'COMMAND'
            return t
        
        # Otherwise it's just a string
        return t
    
    # Ignored characters (spaces and tabs)
    t_ignore = ' \t'
    
    # Newline handling
    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)
    
    # Error handling
    def t_error(self, t):
        print(f"Illegal character '{t.value[0]}' at line {t.lexer.lineno}")
        t.lexer.skip(1)
    
    def tokenize(self, data):
        """Tokenize input data"""
        self.lexer.input(data)
        tokens = []
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            tokens.append(tok)
        return tokens

class GromacsParser:
    """Parser for GROMACS command-line interface"""
    
    tokens = GromacsLexer.tokens
    
    def __init__(self):
        self.lexer = GromacsLexer()
        self.lexer.build()
        self.parser = None
        self.commands_parsed = []
        
    def build(self, **kwargs):
        """Build the parser"""
        self.parser = yacc.yacc(module=self, **kwargs)
        return self.parser
    
    # Grammar rules
    def p_command(self, p):
        """command : GMX COMMAND options"""
        p[0] = {
            'type': 'gromacs_command',
            'command': p[2],
            'options': p[3] if len(p) > 3 else {}
        }
        
    def p_command_no_options(self, p):
        """command : GMX COMMAND"""
        p[0] = {
            'type': 'gromacs_command',
            'command': p[2],
            'options': {}
        }
    
    def p_options(self, p):
        """options : option
                   | options option"""
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = {**p[1], **p[2]}
    
    def p_option(self, p):
        """option : FLAG value"""
        p[0] = {p[1]: p[2]}
    
    def p_option_flag_only(self, p):
        """option : FLAG"""
        # Boolean flag without value
        p[0] = {p[1]: True}
    
    def p_value(self, p):
        """value : FILENAME
                 | STRING
                 | NUMBER
                 | INTEGER
                 | vector"""
        p[0] = p[1]
    
    def p_vector(self, p):
        """vector : LPAREN number_list RPAREN"""
        p[0] = p[2]
    
    def p_number_list(self, p):
        """number_list : number_value
                       | number_list number_value"""
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[2]]
    
    def p_number_value(self, p):
        """number_value : NUMBER
                        | INTEGER"""
        p[0] = p[1]
    
    def p_error(self, p):
        if p:
            print(f"Syntax error at token {p.type} ('{p.value}') at line {p.lineno}")
        else:
            print("Syntax error at EOF")
    
    def parse(self, data: str) -> Optional[Dict[str, Any]]:
        """Parse a GROMACS command"""
        self.commands_parsed = []
        result = self.parser.parse(data, lexer=self.lexer.lexer)
        return result

class GromacsCommandValidator:
    """Validates parsed GROMACS commands based on workflow requirements"""
    
    # Common flags for each command
    COMMAND_FLAGS = {
        'pdb2gmx': {'-f', '-o', '-p', '-i', '-n', '-q', '-ff', '-water'},
        'editconf': {'-f', '-o', '-n', '-bf', '-box', '-angles', '-d', '-c', '-center'},
        'solvate': {'-cp', '-cs', '-o', '-p', '-box', '-radius'},
        'grompp': {'-f', '-c', '-r', '-p', '-n', '-o', '-t', '-maxwarn'},
        'mdrun': {'-s', '-o', '-x', '-c', '-e', '-g', '-cpi', '-cpo', '-deffnm', '-v', '-nt', '-ntmpi'},
        'energy': {'-f', '-o', '-xvg'},
    }
    
    @classmethod
    def validate(cls, parsed_command: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate a parsed command
        Returns: (is_valid, list_of_warnings)
        """
        warnings = []
        
        if parsed_command['type'] != 'gromacs_command':
            return False, ["Not a valid GROMACS command"]
        
        command = parsed_command['command']
        options = parsed_command['options']
        
        # Check if command is recognized
        if command in cls.COMMAND_FLAGS:
            valid_flags = cls.COMMAND_FLAGS[command]
            for flag in options.keys():
                if flag not in valid_flags:
                    warnings.append(f"Warning: '{flag}' may not be a valid flag for 'gmx {command}'")
        
        # Command-specific validation
        if command == 'pdb2gmx':
            if '-f' not in options:
                warnings.append("Warning: 'pdb2gmx' typically requires -f (input PDB file)")
        
        elif command == 'grompp':
            if '-f' not in options:
                warnings.append("Warning: 'grompp' requires -f (MDP file)")
            if '-c' not in options:
                warnings.append("Warning: 'grompp' requires -c (coordinate file)")
            if '-p' not in options:
                warnings.append("Warning: 'grompp' requires -p (topology file)")
        
        elif command == 'mdrun':
            if '-s' not in options and '-deffnm' not in options:
                warnings.append("Warning: 'mdrun' requires -s (TPR file) or -deffnm")
        
        return len(warnings) == 0 or all('Warning' in w for w in warnings), warnings

def parse_gromacs_command(command_string: str, validate: bool = True) -> Optional[Dict[str, Any]]:
    """
    Parse a GROMACS command string
    
    Args:
        command_string: The command to parse (e.g., "gmx pdb2gmx -f input.pdb -o output.gro")
        validate: Whether to validate the command
    
    Returns:
        Dictionary containing parsed command structure, or None if parsing failed
    """
    parser = GromacsParser()
    parser.build()
    
    result = parser.parse(command_string)
    
    if result and validate:
        is_valid, warnings = GromacsCommandValidator.validate(result)
        result['validation'] = {
            'valid': is_valid,
            'warnings': warnings
        }
    
    return result