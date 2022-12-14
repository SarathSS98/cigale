"""
Periodic SFH in the form of rectangles, and decaying or delayed exponentials
============================================================================

# This module implements a periodic star formation history (SFH) formed by
regularly-spaced star formation events. Each even can either be rectangular, a
decaying exponential, or "delayed".

"""

import numpy as np

from . import SedModule

__category__ = "SFH"


class SfhPeriodic(SedModule):
    """Several regularly-spaced short delayed-SFH SF events

    This module sets the SED star formation history (SFH) as a combination of
    several regularly-spaced short SF events.

    """

    parameter_list = {
        "type_bursts": (
            "cigale_list(dtype=int, options=0. & 1. & 2.)",
            "Type of the individual star formation episodes. 0: exponential, "
            "1: delayed, 2: rectangle.",
            0
        ),
        "delta_bursts": (
            "cigale_list(dtype=int, minvalue=0.)",
            "Elapsed time between the beginning of each burst in Myr. The "
            "precision is 1 Myr.",
            50
        ),
        "tau_bursts": (
            "cigale_list()",
            "Duration (rectangle) or e-folding time of all short events in "
            "Myr. The precision is 1 Myr.",
            20.
        ),
        "age": (
            "cigale_list(dtype=int, minvalue=0.)",
            "Age of the main stellar population in the galaxy in Myr. The "
            "precision is 1 Myr.",
            1000
        ),
        "sfr_A": (
            "cigale_list(minvalue=0.)",
            "Multiplicative factor controlling the amplitude of SFR (valid "
            "for each event).",
            1.
        ),
        "normalise": (
            "boolean()",
            "Normalise the SFH to produce one solar mass.",
            True
        ),
    }

    def _init_code(self):
        self.type_bursts = int(self.parameters["type_bursts"])
        self.delta_bursts = int(self.parameters["delta_bursts"])
        self.tau_bursts = float(self.parameters["tau_bursts"])
        age = int(self.parameters["age"])
        sfr_A = float(self.parameters["sfr_A"])
        if isinstance(self.parameters["normalise"], str):
            normalise = self.parameters["normalise"].lower() == 'true'
        else:
            normalise = bool(self.parameters["normalise"])

        time_grid = np.arange(0, age)
        self.sfr = np.zeros_like(time_grid, dtype=np.float64)

        if self.type_bursts == 0:
            burst = np.exp(-time_grid / self.tau_bursts)
        elif self.type_bursts == 1:
            burst = np.exp(-time_grid / self.tau_bursts) * \
                time_grid / self.tau_bursts**2
        elif self.type_bursts == 2:
            burst = np.zeros_like(time_grid)
            burst[:int(self.tau_bursts) + 1] = 1.
        else:
            raise Exception(f"Burst type {self.type_bursts} unknown.")

        for _ in np.arange(0, age, self.delta_bursts):
            self.sfr += burst
            burst = np.roll(burst, self.delta_bursts)
            burst[:self.delta_bursts] = 0.

        # Compute the galaxy mass and normalise the SFH to 1 solar mass
        # produced if asked to.
        self.sfr_integrated = np.sum(self.sfr) * 1e6
        if normalise:
            self.sfr /= self.sfr_integrated
            self.sfr_integrated = 1.
        else:
            self.sfr *= sfr_A
            self.sfr_integrated *= sfr_A

    def process(self, sed):
        """Add a star formation history formed by several regularly-spaced SF
        events.

        ** Parameters **

        sed: pcigale.sed.SED object

        """

        sed.add_module(self.name, self.parameters)

        sed.sfh = self.sfr
        sed.add_info("sfh.integrated", self.sfr_integrated, True,
                     unit='solMass')
        sed.add_info("sfh.type_bursts", self.type_bursts)
        sed.add_info("sfh.delta_bursts", self.delta_bursts)
        sed.add_info("sfh.tau_bursts", self.tau_bursts, unit='Myr')


# SedModule to be returned by get_module
Module = SfhPeriodic
