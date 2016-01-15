# coding: utf-8
import re

# This regex adapted from one found at
# http://daringfireball.net/2010/07/improved_regex_for_matching_urls
URL_REGEX = re.compile(r"""(
(?xi)
\b
(?:
    (?:
        (?:https?|ftp|mailto):           # a few protocols we care about
        (?:
            /{1,3}                       # 1-3 slashes
                |                        # or
            [a-z0-9%]                    # Single letter or digit or "%"
                                         # (Trying not to match e.g. "URI::Escape")
        )
    )
        |                                # or
    www\d{0,3}[.]                        # "www.", "www1.", "www2." … "www999."
        |                                # or
    [a-z0-9.\-]+[.][a-z]{2,4}/           # looks like domain name followed by a slash
)
(?:                                      # One or more:
    [^\s()<>]+                           # Run of non-space, non-()<>
        |                                # or
    \(([^\s()<>]+|(\([^\s()<>]+\)))*\)   # balanced parens, up to 2 levels
)+
(?:                                      # End with:
    \(([^\s()<>]+|(\([^\s()<>]+\)))*\)   # balanced parens, up to 2 levels
        |                                # or
    [^\s`!()\[\]{};:\'".,<>?«»“”‘’]      # not a space or one of these punct chars
)
)""", re.VERBOSE)

