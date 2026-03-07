# src/pymol_topology/core/errors.py

class FetchError(RuntimeError):
    pass


class NotFoundError(FetchError):
    pass