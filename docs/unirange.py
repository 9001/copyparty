v = "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD"
for v in v.split(","):
    if "+" in v:
        v = v.split("+")[1]
    if "-" in v:
        lo, hi = v.split("-")
    else:
        lo = hi = v
    for v in range(int(lo, 16), int(hi, 16) + 1):
        print("{:4x} [{}]".format(v, chr(v)))
