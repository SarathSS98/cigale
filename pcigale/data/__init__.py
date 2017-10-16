# -*- coding: utf-8 -*-
# Copyright (C) 2012, 2013 Centre de données Astrophysiques de Marseille
# Licensed under the CeCILL-v2 licence - see Licence_CeCILL_V2-en.txt
# Author: Yannick Roehlly

"""
This is the database where we store some data used by pcigale.

The classes for these various objects are described in pcigale.data
sub-packages. The corresponding underscored classes here are used by the
SqlAlchemy ORM to store the data in a unique SQLite3 database.

"""

import pkg_resources
from sqlalchemy import create_engine, exc, Column, String,  Float, PickleType
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import class_mapper, sessionmaker
import numpy as np

from .filters import Filter
from .bc03 import BC03
from .dl2014 import DL2014
from .fritz2006 import Fritz2006
from .schreiber2016 import Schreiber2016

DATABASE_FILE = pkg_resources.resource_filename(__name__, 'data.db')

ENGINE = create_engine('sqlite:///' + DATABASE_FILE, echo=False)
BASE = declarative_base()
SESSION = sessionmaker(bind=ENGINE)


class DatabaseLookupError(Exception):
    """
    A custom exception raised when a search in the database does not find a
    result.
    """


class DatabaseInsertError(Exception):
    """
    A custom exception raised when one tries to insert in the database
    something that is already in it.
    """


class _Filter(BASE):
    """ Storage for filters
    """

    __tablename__ = 'filters'

    name = Column(String, primary_key=True)
    description = Column(String)
    trans_table = Column(PickleType)
    effective_wavelength = Column(Float)

    def __init__(self, f):
        self.name = f.name
        self.description = f.description
        self.trans_table = f.trans_table
        self.effective_wavelength = f.effective_wavelength


class _BC03(BASE):
    """Storage for Bruzual and Charlot 2003 SSP
    """

    __tablename__ = "bc03"

    imf = Column(String, primary_key=True)
    metallicity = Column(Float, primary_key=True)
    time_grid = Column(PickleType)
    wavelength_grid = Column(PickleType)
    info_table = Column(PickleType)
    spec_table = Column(PickleType)

    def __init__(self, ssp):
        self.imf = ssp.imf
        self.metallicity = ssp.metallicity
        self.time_grid = ssp.time_grid
        self.wavelength_grid = ssp.wavelength_grid
        self.info_table = ssp.info_table
        self.spec_table = ssp.spec_table


class _DL2014(BASE):
    """Storage for the updated Draine and Li (2007) IR models
    """

    __tablename__ = 'DL2014_models'
    qpah = Column(Float, primary_key=True)
    umin = Column(Float, primary_key=True)
    umax = Column(Float, primary_key=True)
    alpha = Column(Float, primary_key=True)
    wave = Column(PickleType)
    lumin = Column(PickleType)

    def __init__(self, model):
        self.qpah = model.qpah
        self.umin = model.umin
        self.umax = model.umax
        self.alpha = model.alpha
        self.wave = model.wave
        self.lumin = model.lumin


class _Fritz2006(BASE):
    """Storage for Fritz et al. (2006) models
    """

    __tablename__ = 'fritz2006'
    r_ratio = Column(Float, primary_key=True)
    tau = Column(Float, primary_key=True)
    beta = Column(Float, primary_key=True)
    gamma = Column(Float, primary_key=True)
    opening_angle = Column(Float, primary_key=True)
    psy = Column(Float, primary_key=True)
    wave = Column(PickleType)
    lumin_therm = Column(PickleType)
    lumin_scatt = Column(PickleType)
    lumin_agn = Column(PickleType)

    def __init__(self, agn):
        self.r_ratio = agn.r_ratio
        self.tau = agn.tau
        self.beta = agn.beta
        self.gamma = agn.gamma
        self.opening_angle = agn.opening_angle
        self.psy = agn.psy
        self.wave = agn.wave
        self.lumin_therm = agn.lumin_therm
        self.lumin_scatt = agn.lumin_scatt
        self.lumin_agn = agn.lumin_agn


class _Schreiber2016(BASE):
    """Storage for Schreiber et al (2016) infra-red templates
        """

    __tablename__ = 'schreiber2016_templates'
    type = Column(Float, primary_key=True)
    tdust = Column(String, primary_key=True)
    wave = Column(PickleType)
    lumin = Column(PickleType)

    def __init__(self, ir):
        self.type = ir.type
        self.tdust = ir.tdust
        self.wave = ir.wave
        self.lumin = ir.lumin


class Database(object):
    """Object giving access to pcigale database."""

    def __init__(self, writable=False):
        """
        Create a collection giving access to access the pcigale database.

        Parameters
        ----------
        writable: boolean
            If True the user will be able to write new data in the database
            (but he/she must have a writable access to the sqlite file). By
            default, False.
        """
        self.session = SESSION()
        self.is_writable = writable

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def upgrade_base(self):
        """ Upgrade the table schemas in the database
        """
        if self.is_writable:
            BASE.metadata.create_all(ENGINE)
        else:
            raise Exception('The database is not writable.')

    def close(self):
        """ Close the connection to the database

        TODO: It would be better to wrap the database use inside a context
        manager.
        """
        self.session.close_all()

    def add_bc03(self, ssp_bc03):
        """
        Add a Bruzual and Charlot 2003 SSP to pcigale database

        Parameters
        ----------
        ssp: pcigale.data.SspBC03

        """
        if self.is_writable:
            ssp = _BC03(ssp_bc03)
            self.session.add(ssp)
            try:
                self.session.commit()
            except exc.IntegrityError:
                self.session.rollback()
                raise DatabaseInsertError('The SSP is already in the base.')
        else:
            raise Exception('The database is not writable.')

    def get_bc03(self, imf, metallicity):
        """
        Query the database for the Bruzual and Charlot 2003 SSP corresponding
        to the given initial mass function and metallicity.

        Parameters
        ----------
        imf: string
            Initial mass function (salp for Salpeter, chab for Chabrier)
        metallicity: float
            0.02 for Solar metallicity
        Returns
        -------
        ssp: pcigale.data.BC03
            The BC03 object.

        Raises
        ------
        DatabaseLookupError: if the requested SSP is not in the database.

        """
        result = self.session.query(_BC03)\
            .filter(_BC03.imf == imf)\
            .filter(_BC03.metallicity == metallicity)\
            .first()
        if result:
            return BC03(result.imf, result.metallicity, result.time_grid,
                        result.wavelength_grid, result.info_table,
                        result.spec_table)
        else:
            raise DatabaseLookupError(
                "The BC03 SSP for imf <{0}> and metallicity <{1}> is not in "
                "the database.".format(imf, metallicity))

    def get_bc03_parameters(self):
        """Get parameters for the Bruzual & Charlot 2003 stellar models.

        Returns
        -------
        paramaters: dictionary
            dictionary of parameters and their values
        """
        return self._get_parameters(_BC03)

    def add_dl2014(self, models):
        """
        Add a list of updated Draine and Li (2007) models to the database.

        Parameters
        ----------
        models: list of pcigale.data.DL2014 objects

        """
        if self.is_writable:
            for model in models:
                self.session.add(_DL2014(model))
            try:
                self.session.commit()
            except exc.IntegrityError:
                self.session.rollback()
                raise DatabaseInsertError(
                    'The updated DL07 model is already in the base.')
        else:
            raise Exception('The database is not writable.')

    def get_dl2014(self, qpah, umin, umax, alpha):
        """
        Get the Draine and Li (2007) model corresponding to the given set of
        parameters.

        Parameters
        ----------
        qpah: float
            Mass fraction of PAH
        umin: float
            Minimum radiation field
        umin: float
            Maximum radiation field
        alpha: float
            Powerlaw slope dU/dM∝U¯ᵅ

        Returns
        -------
        model: pcigale.data.DL2014
            The updated Draine and Li (2007) model.

        Raises
        ------
        DatabaseLookupError: if the requested model is not in the database.

        """
        result = (self.session.query(_DL2014).
                  filter(_DL2014.qpah == qpah).
                  filter(_DL2014.umin == umin).
                  filter(_DL2014.umax == umax).
                  filter(_DL2014.alpha == alpha).
                  first())
        if result:
            return DL2014(result.qpah, result.umin, result.umax, result.alpha,
                          result.wave, result.lumin)
        else:
            raise DatabaseLookupError(
                "The DL2014 model for qpah <{0}>, umin <{1}>, umax <{2}>, and "
                "alpha <{3}> is not in the database."
                .format(qpah, umin, umax, alpha))

    def get_dl2014_parameters(self):
        """Get parameters for the DL2014 models.

        Returns
        -------
        paramaters: dictionary
            dictionary of parameters and their values
        """
        return self._get_parameters(_DL2014)

    def add_fritz2006(self, models):
        """
        Add a Fritz et al. (2006) AGN model to the database.

        Parameters
        ----------
        models: list of pcigale.data.Fritz2006 objects

        """
        if self.is_writable:
            for model in models:
                self.session.add(_Fritz2006(model))
            try:
                self.session.commit()
            except exc.IntegrityError:
                self.session.rollback()
                raise DatabaseInsertError(
                    'The agn model is already in the base.')
        else:
            raise Exception('The database is not writable.')

    def get_fritz2006(self, r_ratio, tau, beta, gamma, opening_angle, psy):
        """
        Get the Fritz et al. (2006) AGN model corresponding to the number.

        Parameters
        ----------
        r_ratio: float
            Ratio of the maximum and minimum radii of the dust torus.
        tau: float
            Tau at 9.7µm
        beta: float
            Beta
        gamma: float
            Gamma
        opening_angle: float
            Opening angle of the dust torus.
        psy: float
            Angle between AGN axis and line of sight.
        wave: array of float
            Wavelength grid in nm.
        lumin_therm: array of float
            Luminosity density of the dust torus at each wavelength in W/nm.
        lumin_scatt: array of float
            Luminosity density of the scattered emission at each wavelength
            in W/nm.
        lumin_agn: array of float
            Luminosity density of the central AGN at each wavelength in W/nm.


        Returns
        -------
        agn: pcigale.data.Fritz2006
            The AGN model.

        Raises
        ------
        DatabaseLookupError: if the requested template is not in the database.

        """
        result = (self.session.query(_Fritz2006).
                  filter(_Fritz2006.r_ratio == r_ratio).
                  filter(_Fritz2006.tau == tau).
                  filter(_Fritz2006.beta == beta).
                  filter(_Fritz2006.gamma == gamma).
                  filter(_Fritz2006.opening_angle == opening_angle).
                  filter(_Fritz2006.psy == psy).
                  first())
        if result:
            return Fritz2006(result.r_ratio, result.tau, result.beta,
                             result.gamma, result.opening_angle, result.psy,
                             result.wave, result.lumin_therm,
                             result.lumin_scatt, result.lumin_agn)
        else:
            raise DatabaseLookupError(
                "The Fritz2006 model is not in the database.")

    def get_fritz2006_parameters(self):
        """Get parameters for the Fritz 2006 AGN models.

        Returns
        -------
        paramaters: dictionary
            dictionary of parameters and their values
        """
        return self._get_parameters(_Fritz2006)

    def add_schreiber2016(self, models):
        """
        Add Schreiber et al (2016) templates the collection.

        Parameters
        ----------
        models: list of pcigale.data.Schreiber2016 objects

        """

        if self.is_writable:
            for model in models:
                self.session.add(_Schreiber2016(model))
            try:
                self.session.commit()
            except exc.IntegrityError:
                self.session.rollback()
                raise DatabaseInsertError(
                  'The Schreiber2016 template is already in the base.')
        else:
            raise Exception('The database is not writable.')

    def get_schreiber2016(self, type, tdust):
        """
        Get the Schreiber et al (2016) template corresponding to the given set
        of parameters.

        Parameters
        ----------
        type: float
        Dust template or PAH template
        tdust: float
        Dust temperature

        Returns
        -------
        template: pcigale.data.Schreiber2016
        The Schreiber et al. (2016) IR template.

        Raises
        ------
        DatabaseLookupError: if the requested template is not in the database.

        """
        result = (self.session.query(_Schreiber2016).
                  filter(_Schreiber2016.type == type).
                  filter(_Schreiber2016.tdust == tdust).
                  first())
        if result:
            return Schreiber2016(result.type, result.tdust, result.wave,
                                 result.lumin)
        else:
            raise DatabaseLookupError(
                "The Schreiber2016 template for type <{0}> and tdust <{1}> "
                "is not in the database.".format(type, tdust))

    def get_schreiber2016_parameters(self):
        """Get parameters for the Scnreiber 2016 models.

        Returns
        -------
        paramaters: dictionary
        dictionary of parameters and their values
        """
        return self._get_parameters(_Schreiber2016)

    def _get_parameters(self, schema):
        """Generic function to get parameters from an arbitrary schema.

        Returns
        -------
        parameters: dictionary
            Dictionary of parameters and their values
        """

        return {k.name: np.sort(
                [v[0] for v in set(self.session.query(schema).values(k))])
                for k in class_mapper(schema).primary_key}

    def add_filter(self, pcigale_filter):
        """
        Add a filter to pcigale database.

        Parameters
        ----------
        pcigale_filter: pcigale.data.Filter
        """
        if self.is_writable:
            self.session.add(_Filter(pcigale_filter))
            try:
                self.session.commit()
            except exc.IntegrityError:
                self.session.rollback()
                raise DatabaseInsertError('The filter is already in the base.')
        else:
            raise Exception('The database is not writable.')

    def add_filters(self, pcigale_filters):
        """
        Add a list of filters to the pcigale database.

        Parameters
        ----------
        pcigale_filters: list of pcigale.data.Filter objects
        """
        if self.is_writable:
            for pcigale_filter in pcigale_filters:
                self.session.add(_Filter(pcigale_filter))
            try:
                self.session.commit()
            except exc.IntegrityError:
                self.session.rollback()
                raise DatabaseInsertError('The filter is already in the base.')
        else:
            raise Exception('The database is not writable.')

    def del_filter(self, name):
        """
        Delete a filter from the pcigale database.

        Parameters
        ----------
        name: name of the filter to be deleted
        """
        if self.is_writable:
            if name in self.get_filter_names():
                (self.session.query(_Filter).
                 filter(_Filter.name == name).delete())
                try:
                    self.session.commit()
                except exc.IntegrityError:
                    raise Exception('The database is not writable.')
        else:
            raise DatabaseLookupError(
                "The filter <{0}> is not in the database".format(name))

    def get_filter(self, name):
        """
        Get a specific filter from the collection

        Parameters
        ----------
        name: string
            Name of the filter

        Returns
        -------
        filter: pcigale.base.Filter
            The Filter object.

        Raises
        ------
        DatabaseLookupError: if the requested filter is not in the database.

        """
        result = (self.session.query(_Filter).
                  filter(_Filter.name == name).
                  first())
        if result:
            return Filter(result.name, result.description, result.trans_table,
                          result.effective_wavelength)
        else:
            raise DatabaseLookupError(
                "The filter <{0}> is not in the database".format(name))

    def get_filter_names(self):
        """Get the list of the name of the filters in the database.

        Returns
        -------
        names: list
            list of the filter names
        """
        return [n[0] for n in self.session.query(_Filter.name).all()]

    def parse_filters(self):
        """Generator to parse the filter database."""
        for filt in self.session.query(_Filter):
            yield Filter(filt.name, filt.description, filt.trans_table,
                         filt.effective_wavelength)
