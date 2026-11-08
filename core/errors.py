"""Exception domain aplikasi — dipisah agar bebas circular import."""


class GenerationError(Exception):
    """Error validasi/generate yang pesannya layak ditampilkan ke user."""
