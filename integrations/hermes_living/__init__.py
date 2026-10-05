"""Dedicated Hermes platform plugin; never a generic Living send surface."""

def register(ctx):
    # Hermes imports the adapter only when invoking the official plugin seam.
    from .adapter import register as register_platform
    return register_platform(ctx)

__all__ = ['register']
