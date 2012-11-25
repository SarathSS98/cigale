# -*- coding: utf-8 -*-
"""
Copyright (C) 2012 Centre de données Astrophysiques de Marseille
Licensed under the CeCILL-v2 licence - see Licence_CeCILL_V2-en.txt

@author: Yannick Roehlly <yannick.roehlly@oamp.fr>

"""

import itertools
import collections


def param_dict_combine(dictionary):
    """Given a dictionary associating to each key an array, returns all the
    possible dictionaries associating a single element to each key.

    Parametres
    ----------
    dictionary : dict
        Dictionary associating an array to its (or some of its) keys.

    Returns
    -------
    combination_list : list of dictionaries
        List of dictionaries with the same keys but associating one element
        to each.

    """
    # We make a copy of the dictionary as we are modifying it.
    dictionary = dict(dictionary)

    # First, we must ensure that all values are lists; when a value is a
    # single element, we put it in a list.
    # We must take a special care of strings, because they are iterable.
    for key, value in dictionary.items():
        if ((not isinstance(value, collections.Iterable)) or
                isinstance(value, basestring)):
            dictionary[key] = [value]

    # We use itertools.product to make all the possible combinations from the
    # value lists.
    key_list = dictionary.keys()
    value_array_list = [dictionary[key] for key in key_list]
    combination_list = [dict(zip(key_list, combination)) for combination in
                        itertools.product(*value_array_list)]

    return combination_list
