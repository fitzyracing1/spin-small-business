"""spin-small-business: Summarize a bookkeeping CSV by category and estimate quarterly tax from a rate you supply"""
import sys

INTRO = (
    "spin-small-business by Joshua Almeida.\n"
    "The bookkeeper ships in a pull request. You supply the tax rate. It is a math helper, not tax advice.\n"
    "Sponsor: https://github.com/sponsors/fitzyracing1"
)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    print(INTRO)
    if argv and argv[0] in ("-h", "--help", "help"):
        print()
        print("Usage: python small_business.py")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
