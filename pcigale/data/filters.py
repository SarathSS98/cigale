# -*- coding: utf-8 -*-
# Copyright (C) 2012 Centre de données Astrophysiques de Marseille
# Licensed under the CeCILL-v2 licence - see Licence_CeCILL_V2-en.txt
# Author: Yannick Roehlly

import numpy as np
from scipy.constants import c


class Filter:
    """A photometric filter with associated transmission data.
    """

    def __init__(self, name, description=None, trans_table=None,
                 pivot_wavelength=None):
        """Create a new filter. If the transmission type, the description
        the transmission table or the pivot wavelength are not specified,
        their value is set to None.

        Parameters
        ----------
        name: string
            Name of the filter
        description: string
            Description of the filter
        trans_table: array
            trans_table[0] is the wavelength in nm,
            trans_table[1] is the transmission)
        pivot_wavelength: float
            Pivot wavelength of the filter
        """

        self.name = name
        self.description = description
        self.trans_table = trans_table
        self.pivot_wavelength = pivot_wavelength

    def __str__(self):
        """Pretty print the filter information
        """
        result = ""
        result += ("Filter name: %s\n" % self.name)
        result += ("Description: %s\n" % self.description)
        result += ("Pivot wavelength: %s nm\n" %
                   self.pivot_wavelength)
        return result
