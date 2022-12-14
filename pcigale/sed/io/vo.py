from astropy.io.votable.tree import VOTableFile, Resource, Table, Field, Info
import numpy as np


def save_sed_to_vo(sed, filename, norm=1.):
    """
    Save a SED object to a VO-Table file

    Parameters
    ----------
    sed: a pcigale.sed.SED object
        The SED to save.
    filename: string
        Name of the file to save the SED to.
    norm: float
        Normalisation factor of the SED

    """
    votable = VOTableFile()

    spectra_resource = Resource(id="Spectra")
    votable.resources.append(spectra_resource)

    # Total F_nu
    fnu_table = Table(votable, name="Fnu", id="Fnu")
    spectra_resource.tables.append(fnu_table)
    fnu_table.fields.extend([
        Field(votable, name="wavelength", datatype="double", unit="nm",
              ucd="em.wl"),
        Field(votable, name="F_nu", datatype="double", unit="mJy",
              ucd="phot.flux")
    ])
    fnu_table.create_arrays(len(sed.wavelength_grid))
    fnu_table.array["wavelength"] = sed.wavelength_grid
    fnu_table.array["F_nu"] = norm * sed.fnu

    # L_lambda contributions and total
    Llambda_table = Table(votable, name="Llambda", id="Llambda")
    spectra_resource.tables.append(Llambda_table)
    Llambda_fields = [
        Field(votable, name="wavelength", datatype="double", unit="nm",
              ucd="em.wl"),
        Field(votable, name="L_lambda_total", datatype="double", unit="W/nm",
              ucd="phot.flux")]
    for name in sed.luminosities:
        Llambda_fields.append(Field(votable, name=name, datatype="double",
                                    unit="W/nm", ucd="phot.flux"))
    Llambda_table.fields.extend(Llambda_fields)
    Llambda_table.create_arrays(len(sed.wavelength_grid))
    Llambda_table.array["wavelength"] = sed.wavelength_grid
    Llambda_table.array["L_lambda_total"] = norm * sed.luminosity
    for name in sed.luminosities:
        Llambda_table.array[name] = norm * sed.luminosities(name)

    # SFH
    if sed.sfh is not None:
        sfh_resource = Resource(id="Star_Formation_History")
        votable.resources.append(sfh_resource)
        sfh_table = Table(votable, name="SFH", id="SFH")
        sfh_resource.tables.append(sfh_table)
        sfh_table.fields.extend([
            Field(votable, name="time", datatype="double", unit="Myr",
                  ucd="time.age"),
            Field(votable, name="SFR", datatype="double", unit="Msun/yr",
                  ucd="phys.SFR")
        ])
        sfh_table.create_arrays(sed.sfh.size)
        sfh_table.array["time"] = np.arange(sed.sfh.size)
        sfh_table.array["SFR"] = norm * sed.sfh

    # SED information to keywords
    if sed.sfh is not None:
        # If there is a stellar population then the norm factor is the stellar
        # mass.
        votable.infos.append(Info(name="Galaxy mass in Msun", value=norm))

    for name, value in sorted(sed.info.items()):
        if name in sed.mass_proportional_info:
            votable.infos.append(Info(name=name, value=norm * value))
        else:
            votable.infos.append(Info(name=name, value=value))

    votable.set_all_tables_format('binary')
    votable.to_xml(filename)
