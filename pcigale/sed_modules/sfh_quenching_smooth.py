"""
Star Formation History quenching (smooth) module
================================================

This module performs a smooth quenching on the Star Formation History. Below a
given age, the Star Formation Rate becomes linear to be multiplied by
1- quenching_factor at the end of the history.

"""

import numpy as np

from . import SedModule


class SfhQuenchSmooth(SedModule):
    """Star Formation History Quenching

    This module implements a quenching of the Star Formation History.

    """

    parameter_list = {
        "quenching_time": (
            "cigale_list(dtype=int, minvalue=0.)",
            "Look-back time when the quenching starts in Myr.",
            0
        ),
        "quenching_factor": (
            "cigale_list(minvalue=0., maxvalue=1.)",
            "Quenching factor applied to the SFH. After the quenching time, "
            "the SFR is multiplied by 1 - quenching factor and made constant. "
            "The factor must be between 0 (no quenching) and 1 (no more star "
            "formation).",
            0.
        ),
        "normalise": (
            "boolean()",
            "Normalise the SFH to produce one solar mass.",
            True
        )
    }

    def _init_code(self):
        self.quenching_age = int(self.parameters["quenching_time"])
        self.quenching_factor = float(self.parameters["quenching_factor"])
        if isinstance(self.parameters["normalise"], str):
            self.normalise = self.parameters["normalise"].lower() == 'true'
        else:
            self.normalise = bool(self.parameters["normalise"])

    def process(self, sed):
        """
        Parameters
        ----------
        sed : pcigale.sed.SED object

        """

        # Read the star formation history of the SED
        sfr = sed.sfh

        if self.quenching_age > sfr.size:
            raise Exception("[sfh_quenching] The quenching age is greater "
                            "than the galaxy age. Please fix your parameters.")

        # We assume the time in the star formation history is evenly spaced to
        # compute the reverse index (i.e. from the end of the array) of the SFH
        # step corresponding to the quenching age.
        # We make the computation only if the quenching age and the quenching
        # factor are not 0.
        if self.quenching_age > 0 and self.quenching_factor > 0.:
            sfr0 = sfr[-self.quenching_age]
            sfr1 = sfr[-self.quenching_age] * (1. - self.quenching_factor)
            sfr[-self.quenching_age:] = sfr0 + (sfr1 - sfr0) * np.linspace(
                0, 1, self.quenching_age)

            # Compute the galaxy mass and normalise the SFH to 1 solar mass
            # produced if asked to.
            sfr_integrated = np.sum(sfr) * 1e6
            if self.normalise:
                sfr /= sfr_integrated
                sfr_integrated = 1.

            sed.sfh = sfr
            sed.add_info("sfh.integrated", sfr_integrated, True, force=True,
                         unit='solMass')

        sed.add_module(self.name, self.parameters)

        sed.add_info("sfh.quenching_time", self.quenching_age, unit='Myr')
        sed.add_info("sfh.quenching_factor", self.quenching_factor)


# SedModule to be returned by get_module
Module = SfhQuenchSmooth
