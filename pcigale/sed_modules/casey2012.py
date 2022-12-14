"""
Casey (2012) IR models module
=============================

This module implements the Casey (2012) infra-red models.

"""

import numpy as np
import scipy.constants as cst

from . import SedModule

__category__ = "dust emission"


class Casey2012(SedModule):
    """Casey (2012) templates IR re-emission

    Given an amount of attenuation (e.g. resulting from the action of a dust
    attenuation module) this module normalises the Casey (2012) template
    corresponding to a given α to this amount of energy and add it to the SED.

    """

    parameter_list = {
        "temperature": (
            "cigale_list(minvalue=0.)",
            "Temperature of the dust in K.",
            35.
        ),
        "beta": (
            "cigale_list(minvalue=0.)",
            "Emissivity index of the dust.",
            1.6
        ),
        "alpha": (
            "cigale_list(minvalue=0.)",
            "Mid-infrared powerlaw slope.",
            2.
        )
    }

    def _init_code(self):
        """Build the model for a given set of parameters."""
        # To compactify the following equations we only assign them to self at
        # the end of the method
        T = float(self.parameters["temperature"])
        beta = float(self.parameters["beta"])
        alpha = float(self.parameters["alpha"])

        # We define various constants necessary to compute the model. For
        # consistency, we define the speed of light in nm s¯¹ rather than in
        # m s¯¹.
        c = cst.c * 1e9
        b1 = 26.68
        b2 = 6.246
        b3 = 1.905e-4
        b4 = 7.243e-5
        lambda_c = 0.75e3 / ((b1 + b2 * alpha) ** -2. + (b3 + b4 * alpha) * T)
        lambda_0 = 200e3
        Npl = ((1. - np.exp(-(lambda_0 / lambda_c) ** beta)) * (c / lambda_c)
               ** 3. / (np.exp(cst.h * c / (lambda_c * cst.k * T)) - 1.))

        self.wave = np.logspace(3., 6., 1000)
        conv = c / (self.wave * self.wave)

        self.lumin_blackbody = (conv * (1. - np.exp(-(lambda_0 / self.wave)
                                ** beta)) * (c / self.wave) ** 3. / (np.exp(
                                    cst.h * c / (self.wave * cst.k * T)) - 1.))
        self.lumin_powerlaw = (conv * Npl * (self.wave / lambda_c) ** alpha *
                               np.exp(-(self.wave / lambda_c) ** 2.))

        # TODO, save the right normalisation factor to retrieve the dust mass
        norm = np.trapz(self.lumin_powerlaw + self.lumin_blackbody,
                        x=self.wave)
        self.lumin_powerlaw /= norm
        self.lumin_blackbody /= norm
        self.lumin = self.lumin_powerlaw + self.lumin_blackbody

        self.temperature = T
        self.beta = beta
        self.alpha = alpha

    def process(self, sed):
        """Add the IR re-emission contributions.

        Parameters
        ----------
        sed: pcigale.sed.SED object

        """
        if 'dust.luminosity' not in sed.info:
            sed.add_info('dust.luminosity', 1., True, unit='W')
        luminosity = sed.info['dust.luminosity']

        sed.add_module(self.name, self.parameters)
        sed.add_info("dust.temperature", self.temperature, unit='K')
        sed.add_info("dust.beta", self.beta)
        sed.add_info("dust.alpha", self.alpha)

        sed.add_contribution('dust.powerlaw', self.wave,
                             luminosity * self.lumin_powerlaw)
        sed.add_contribution('dust.blackbody', self.wave,
                             luminosity * self.lumin_blackbody)


# SedModule to be returned by get_module
Module = Casey2012
