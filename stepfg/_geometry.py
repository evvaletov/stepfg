import math
import operator
from numbers import Number


def rotate(list_in, x):
    return list_in[-x:] + list_in[:-x]


def normalize(vector_in):
    if len(vector_in) != 3:
        raise ValueError("normalize: coordinates must be 3D")
    magnitude = math.sqrt(sum(i ** 2 for i in vector_in))
    if magnitude == 0:  # in some cases vector_in has zeros only
        return [0 for _ in vector_in]
    return [x / magnitude for x in vector_in]


def cross_product(x, y):
    return [
        -x[2] * y[1] + x[1] * y[2],
        x[2] * y[0] - x[0] * y[2],
        -x[1] * y[0] + x[0] * y[1],
    ]


def convert_3d(element_in):
    if (isinstance(element_in, list) and len(element_in) == 2
            and isinstance(element_in[0], Number)
            and isinstance(element_in[1], Number)):
        return [element_in[0], element_in[1], 0]
    return element_in


def convert_to_clockwise(part_list):
    pol_sum = sum(
        (x2[0] - x1[0]) * (x2[1] + x1[1])
        for x1, x2 in zip(part_list, rotate(part_list, 1))
    )
    if pol_sum == 0:
        raise ValueError("Polygon is neither clockwise nor counter-clockwise")
    elif pol_sum > 0:
        return list(reversed(part_list))
    else:
        return list(part_list)
