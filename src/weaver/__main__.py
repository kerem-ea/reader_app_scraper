# Allow `python -m weaver` to act as the top-level CLI dispatcher.
from .cli import main

if __name__ == "__main__":
    main()