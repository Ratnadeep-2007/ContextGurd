"""Private parser subprocess entry point: binary stdin → validated JSON stdout."""
import sys

from .ingestion import MAX_BYTES, parse_source

if __name__ == "__main__":
    source = parse_source(sys.argv[1], sys.stdin.buffer.read(MAX_BYTES + 1))
    sys.stdout.buffer.write(source.model_dump_json().encode("utf-8"))
