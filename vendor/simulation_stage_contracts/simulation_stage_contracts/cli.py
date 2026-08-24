from __future__ import annotations

import argparse
import json
import sys

from .errors import StageContractError, result_envelope
from .version import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["version"])
    args = parser.parse_args(argv)
    try:
        if args.command == "version":
            print(json.dumps(result_envelope("version", True, version=__version__)))
            return 0
    except StageContractError as exc:
        print(json.dumps(exc.as_dict()))
        return exc.exit_code
    print(json.dumps(result_envelope(args.command, False, error_code="E_INTERNAL")))
    return 7


if __name__ == "__main__":
    sys.exit(main())
