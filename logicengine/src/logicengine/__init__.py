# Core parser and validation
from .parser import LogicParser, LogicExpressionError, validate_and_standardize
from .validation import ValidationError

# AST and processing
from .ast import generate_ast, ASTError
from .onp import to_onp, ONPError
from .truth_table import generate_truth_table, TruthTableError

# Simplification algorithms
from .kmap import simplify_kmap, KMapError
from .qm import simplify_qm, QMError

# Rules and rewriting
from .rules import LIST_OF_RULES, Rule, Pattern, Var
from .rewriter import find_matches, apply_match, Match

# Utilities
from .utils import compute_metrics

# Submodules
from . import laws
from . import rewriter
from . import rules

__all__ = [
    # Core
    'LogicParser', 'LogicExpressionError', 'validate_and_standardize',
    'ValidationError',
    
    # Processing
    'generate_ast', 'ASTError',
    'to_onp', 'ONPError', 
    'generate_truth_table', 'TruthTableError',
    
    # Simplification
    'simplify_kmap', 'KMapError',
    'simplify_qm', 'QMError',
    
    # Rules
    'LIST_OF_RULES', 'Rule', 'Pattern', 'Var',
    'find_matches', 'apply_match', 'Match',
    
    # Utils
    'compute_metrics',
    
    # Modules
    'laws', 'rewriter', 'rules',
]
