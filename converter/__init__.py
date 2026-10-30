"""Original-table-validated PDDL to Prolog reconstruction."""
from .pddl2pl import ConversionError, convert, convert_with_diagnostics

__all__ = ['ConversionError', 'convert', 'convert_with_diagnostics']
