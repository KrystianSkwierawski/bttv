"""Exercise actual patched smali with mocked Android/network boundaries.

Usage: python tests/check_resume_watching.py path/to/ResumeWatchingFetcher.smali
This small instruction runner is not a Dalvik verifier or a device playback test.
It fails on unsupported instructions rather than silently skipping them.
"""
import re
import sys
from pathlib import Path


class Fetcher:
    def __init__(self, source):
        self.source = source
        self.cache = {}
        self.sent = []
        self.logged_in = True

    def run(self, method, *args):
        match = re.search(r"^\.method public " + method + r"\(.*?^\.end method", self.source, re.M | re.S)
        assert match, method
        code = [line.strip() for line in match[0].splitlines()
                if line.strip() and not line.strip().startswith((".", "#"))]
        labels = {line: i for i, line in enumerate(code) if line.startswith(":")}
        regs = {"p0": self, **{f"p{i}": arg for i, arg in enumerate(args, 1)}}
        result = None
        pc = 0
        while pc < len(code):
            line = code[pc]
            pc += 1
            if line.startswith(":"):
                continue
            op, _, operand = line.partition(" ")
            parts = operand.split(", ")
            if op.startswith("move-result"):
                regs[operand] = result
            elif op == "move":
                regs[parts[0]] = regs[parts[1]]
            elif op == "const-string":
                regs[parts[0]] = parts[1].strip('"')
            elif op.startswith("const/"):
                regs[parts[0]] = int(parts[1], 0)
            elif op == "check-cast":
                pass
            elif op == "iget-object":
                field = parts[2].split("->")[1].split(":")[0]
                regs[parts[0]] = {"positionInSecondsByVodId": self.cache,
                                  "twitchAccountManager": self,
                                  "resumeWatchingApi": self}[field]
            elif op in ("sget", "sget-object"):
                field = parts[1].split("->")[1].split(":")[0]
                regs[parts[0]] = {"LIVE_STREAM_WATCHED_POS_OFFSET_SECONDS": 30,
                                  "LIVE": "LIVE", "VOD": "VOD"}[field]
            elif op == "sub-int":
                regs[parts[0]] = regs[parts[1]] - regs[parts[2]]
            elif op == "sub-int/2addr":
                regs[parts[0]] -= regs[parts[1]]
            elif op == "if-eqz":
                value = regs[parts[0]]
                # Dalvik object null must not be confused with boxed Integer(0).
                zero = value is None or (type(value) is int and value == 0) or value is False
                if zero:
                    pc = labels[parts[1]]
            elif op == "goto":
                pc = labels[operand]
            elif op.startswith("invoke-"):
                registers, target = operand.split("}, ", 1)
                values = [regs[r] for r in registers[1:].split(", ") if r]
                name = target.split("->")[1].split("(")[0]
                if name in ("checkNotNullParameter", "checkNotNullExpressionValue"):
                    assert values[0] is not None
                elif name == "getId":
                    result = values[0]["id"]
                elif name == "getViewingHistoryPositionSec":
                    result = values[0]["history"]
                elif name == "get":
                    result = values[0].get(values[1])
                elif name == "intValue":
                    result = int(values[0])
                elif name == "valueOf":
                    result = Box(values[0])
                elif name == "coerceAtLeast":
                    result = max(values)
                elif name == "isLoggedIn":
                    result = self.logged_in
                elif name == "isBlank":
                    result = not values[0].strip()
                elif name == "updateCachedLastWatchedPosition":
                    self.cache[values[1]] = Box(values[2])
                elif name == "putLastWatchedPositionForVideo":
                    self.sent.append(tuple(values[1:]))
                    result = "complete"
                elif name == "complete":
                    result = "complete"
                else:
                    raise AssertionError(target)
            elif op.startswith("return"):
                value = regs.get(operand)
                return None if op == "return-object" and type(value) is int and value == 0 else value
            else:
                raise AssertionError(line)
        raise AssertionError("No return")


class Box(int):
    """Distinguish boxed zero from a null object register."""


def check(source):
    fetcher = Fetcher(source)
    read = lambda history=None: fetcher.run("getLastWatchedPositionInSecondsForVod",
                                           {"id": "vod", "history": history})
    for position in (0, 1, 15, 29, 30, 31, 300, 3600, 86400):
        fetcher.cache["vod"] = Box(position)  # VOD playback polling path
        assert read(9000) == position, (position, read(9000))
        fetcher.run("putLastWatchedPositionForVideo", 123, "vod", position, False)
        assert read() == position
        assert fetcher.sent[-1] == (123, "vod", position, "VOD")
        fetcher.run("putLastWatchedPositionForVideo", 123, "vod", position, True)
        assert read() == max(position - 30, 0)
        assert fetcher.sent[-1] == (123, "vod", position, "LIVE")
    # Rewinding must replace history, rather than taking the largest position.
    fetcher.run("putLastWatchedPositionForVideo", 123, "vod", 15, False)
    assert read(9000) == 15
    fetcher.cache.clear()
    assert read(7200) == 7200
    assert read(-1) == 0
    assert read() is None
    fetcher.logged_in = False
    sent = len(fetcher.sent)
    fetcher.run("putLastWatchedPositionForVideo", 123, "vod", 100, False)
    assert not fetcher.cache and len(fetcher.sent) == sent
    fetcher.logged_in = True
    for invalid_id in (None, "", " "):
        fetcher.run("putLastWatchedPositionForVideo", 123, invalid_id, 100, False)
    assert not fetcher.cache and len(fetcher.sent) == sent
    print("PASS: VOD positions, live offset, API payloads, rewind, cloud fallback and guards")


if __name__ == "__main__":
    check(Path(sys.argv[1]).read_text(encoding="utf-8"))
