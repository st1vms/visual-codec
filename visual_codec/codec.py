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


def __pad_vector(binstr: str, color_bitsize: int) -> tuple[str, int, int]:
    """Apply padding to grouped binstring and return padding dimensions"""

    # Works on list of bits
    binstr = list(binstr)

    zeros, ones, zeros_ix, ones_ix = 0, 0, -1, -1
    for i in range(1, len(binstr)):
        # Traverse the bit string backwards counting 0 and 1
        if binstr[-i] == "0":
            zeros += 1
        elif binstr[-i] == "1":
            ones += 1

        # Check if the next bit differs
        if binstr[-i - 1] != binstr[-i]:
            if binstr[-i] == "0":
                # Register this index as padding offset for 0
                zeros_ix = i
            else:
                # Register this index as padding offset for 1
                ones_ix = i

            # End counting once both index were found
            if zeros_ix != -1 and ones_ix != -1:
                break

    # Apply Zeros padding
    if zeros % color_bitsize != 0:
        for _ in range(color_bitsize - (zeros % color_bitsize)):
            binstr.insert(-zeros_ix, "0")

    # Apply Ones padding
    if ones % color_bitsize != 0:
        for _ in range(color_bitsize - (ones % color_bitsize)):
            binstr.insert(-ones_ix, "1")

    # Return padded bit string along padding dimensions
    return "".join(binstr), zeros % color_bitsize, ones % color_bitsize


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
        elif zpad > 0:
            # Remove Ones padding
            del vector[-i]
            zpad -= 1

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
