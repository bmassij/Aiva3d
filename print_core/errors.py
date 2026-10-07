"""Print core exceptions."""


class PrintCoreError(Exception):
    """Base error for 3MF/mesh analysis."""


class Invalid3MFError(PrintCoreError):
    """File is not a valid or readable 3MF."""


class Empty3MFError(PrintCoreError):
    """No mesh geometry found."""


class EmptyFileError(PrintCoreError):
    """Zero-byte input."""
