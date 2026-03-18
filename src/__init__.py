if __name__ != "src":
    # Enable only for ocelescope
    from .plugin import ObjectFlowMiner

    __all__ = [
        "ObjectFlowMiner",
    ]
