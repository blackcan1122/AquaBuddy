from pathlib import Path
from typing import BinaryIO
from llv_utility import dump_line   # re-use exactly the same renderer


def dump_file(path: str | Path,
              skip: int = 0,
              count: int | None = None,
              base: int | None = None,
              bytesperline: int = 16) -> None:

    addr = base if base is not None else skip
    remaining = count

    with Path(path).open("rb") as f:
        f.seek(skip)
        while True:
            if remaining is not None and remaining <= 0:
                break
            need = bytesperline if remaining is None else min(bytesperline,
                                                               remaining)
            chunk = f.read(need)
            if not chunk:
                break            # EOF

            dump_line(addr, chunk, bytesperline)
            addr += len(chunk)
            if remaining is not None:
                remaining -= len(chunk)


if __name__ == "__main__":
    import argparse, sys, textwrap
    parser = argparse.ArgumentParser(
        description="Hex-dump a file using my Stage-0 helpers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
        Numbers accept 0x-prefix hex or decimal.
        Example:
          python filedump_cli.py image.bin -s 0x200 -n 256 -b 0x4000
        """))

    parser.add_argument("file")
    parser.add_argument("-s", "--skip",  type=lambda x: int(x, 0), default=0,
                        help="bytes to skip (default 0)")
    parser.add_argument("-n", "--count", type=lambda x: int(x, 0),
                        help="max bytes to dump")
    parser.add_argument("-b", "--base",  type=lambda x: int(x, 0),
                        help="first address shown (default = skip)")
    parser.add_argument("-bs", "--bytesize", type=int,
                        help="Define size of bytes per line")

    args = parser.parse_args(sys.argv[1:])
    dump_file(args.file, skip=args.skip, count=args.count, base=args.base, bytesperline=args.bytesize)