"""visual-codec implementation"""

#################
# Bit expansion #
#################


def bit_vector_expand(vector: str, exp: int) -> str:
    """Expands each bit in the `vector` by `exp`"""
    e = ""

    for b in vector:
        for _ in range(exp):
            e += b

    return e


def bit_vector_shrink(vector: str, exp: int) -> str:
    """Shrink expanded vector into original bit vector"""

    def find_most_bit(l: list[str]) -> str:
        return str(max(l, key=l.count))

    s = ""
    for i in range(0, len(vector), exp):
        s += find_most_bit(list(vector[i : i + exp]))
    return s


########################
# Codec implementation #
########################


def __pad_vector(binstr: str, color_size: int) -> tuple[str, int, int]:
    """Apply 0/1 padding to color vector"""
    binlst = list(binstr)

    zeros, ones = 0, 0

    diff_index = -1
    first = binstr[-1]

    for i in range(len(binstr) - 1, -1, -1):

        if binstr[i] != first:
            if diff_index != -1:
                break
            diff_index = i
            first = binstr[i]

        if binstr[i] == "0":
            zeros += 1
        if binstr[i] == "1":
            ones += 1

    zpad, opad = 0, 0
    if first == "0":
        while ones % color_size != 0:
            binlst.append("1")
            opad += 1
            ones += 1
        while zeros % color_size != 0:
            binlst.insert(diff_index, "0")
            zpad += 1
            zeros += 1
    elif first == "1":
        while zeros % color_size != 0:
            binlst.append("0")
            zpad += 1
            zeros += 1
        while ones % color_size != 0:
            binlst.insert(diff_index, "1")
            opad += 1
            ones += 1

    return "".join(binlst), zpad, opad


def __depad_vector(vector: str, zpad: int, opad: int) -> list[str]:
    """Remove padding from grouped binstring given padding dimensions"""

    # Works on bit list and returns bit list
    vector = list(vector)

    i = 1
    while opad > 0 or zpad > 0:
        if vector[-i] == "1":
            # Remove Zeros padding
            if opad > 0:
                del vector[-i]
                opad -= 1
                continue
        elif zpad > 0:
            # Remove Ones padding
            del vector[-i]
            zpad -= 1
            continue

        i += 1

    return vector


def group_binstring(
    binstr: str, color_bitsize: int
) -> tuple[str, int, int, list[tuple[int, int]]]:
    """Group binary string with each bit moved to form evenly chunks

    Returns a tuple with these objects in order:

    - `str` object with the grouped binary string
    - `int` with the number of 0 padding applied
    - `int` with the number of 1 padding applied
    - `list[int]` object storing the conversion keys
    """

    key = []

    new = list(binstr)
    l = len(new)

    prev_i, prev_j = 0, 0

    j = -1
    for i in range(0, l - 1):
        if new[i] != new[i + 1]:

            if j == -1 or (j + 1) % color_bitsize == 0:
                j = i
                continue

            key.append((i - prev_i, j - prev_j))
            prev_i, prev_j = i, j

            new[i + 1], new[j + 1] = new[j + 1], new[i + 1]
            j += 1

    key.append((l - prev_i, l - prev_j))

    # Apply padding and return
    binstr, zpad, opad = __pad_vector("".join(new), color_bitsize)
    return binstr, zpad, opad, key


def ungroup_binstring(binstr: str, zpad: int, opad: int, key_list: list[int]) -> str:
    """Deconvert grouped binary string into its original form
    by using the provided conversion keys

    Returns the original binary string object
    """

    # Removes padding from binary string
    binstr = __depad_vector(binstr, zpad, opad)

    # Perform deconversion using key
    new = list(binstr)
    l = len(new)
    i, j = l, l
    for ki, kj in key_list[::-1]:
        i -= ki
        j -= kj
        new[j + 1], new[i + 1] = new[i + 1], new[j + 1]

    # Return original bistring
    return "".join(new)
