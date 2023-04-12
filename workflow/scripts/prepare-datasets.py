# Example script
import logging
from pathlib import Path

import yaml
from astropy import units as u
from astropy.coordinates import SkyCoord
from gammapy.catalog import SourceCatalog3FHL, SourceCatalog4FGL
from gammapy.datasets import Datasets
from gammapy.estimators import TSMapEstimator
from gammapy.maps import Maps
from gammapy.modeling import Fit
from gammapy.modeling.models import Models, SkyModel
from regions import CircleSkyRegion

FERMI_3FHL = SourceCatalog3FHL()
VELA_JUNIOR_3FHL = FERMI_3FHL["RX J0852.0-4622"]

log = logging.getLogger(__name__)


def read_datasets(filename_datasets):
    """Read datasets from file."""
    datasets_input = Datasets.read(filename_datasets)

    datasets = Datasets()

    for dataset in datasets_input:
        dataset.psf.psf_map.data = dataset.psf.psf_map.data.astype(float)
        dataset.mask_safe = None
        datasets.append(dataset)

    return datasets


def read_and_prepare_model(filename_models):
    """Read models from file."""
    fermi_4fgl = SourceCatalog4FGL()

    path = Path(filename_models)

    with path.open("r") as fh:
        data = yaml.safe_load(fh)

    for component in data["components"]:
        if component["name"] == "diffuse-iem":
            filename_fits = Path(component["spatial"]["filename"])
            component["spatial"]["filename"] = path.parent / filename_fits.name

    models = Models.from_dict(data)
    models.remove("3FHL J0851.9-4620e")
    models.freeze()

    models["diffuse-iem"].unfreeze()

    model_J0854 = fermi_4fgl["4FGL J0854.8-4504"].sky_model()
    model_J0854.freeze()
    models.append(model_J0854)
    return models


def prepare_background_model(datasets):
    """Prepare background model."""
    geom = datasets[0].counts.geom

    exclusion_region = CircleSkyRegion(
        center=VELA_JUNIOR_3FHL.position, radius=1.05 * u.deg
    )
    mask = ~geom.region_mask(exclusion_region)

    fit = Fit()

    for d in datasets:
        d.mask_fit = mask

    fit.run(datasets)


def get_ts_map_estimator():
    """Get reference model."""
    model = SkyModel.create("pl", "point")
    model.spectral_model.amplitude.quantity = "1e-14 cm-2 s-1 TeV-1"
    model.spectral_model.index.value = 1.7
    return TSMapEstimator(model=model, sum_over_energy_groups=True)


def cutout_maps(maps, position, width):
    """Cutout maps using dict comprehension."""
    cutout_kwargs = {"position": position, "width": width}
    return Maps(**{k: v.cutout(**cutout_kwargs) for k, v in maps.items()})


def reduce_datasets(datasets):
    """Reduce datasets."""
    datasets_jolideco = {}

    est = get_ts_map_estimator()

    position = SkyCoord.from_name("Vela Junior")

    for dataset in datasets:
        dataset.mask_fit = None
        dataset = dataset.to_image(name=dataset.name)
        dataset.models = models

        maps = Maps(**est.estimate_fit_input_maps(dataset=dataset))
        maps["psf"] = maps.pop("kernel")

        maps.pop("norm")
        maps.pop("mask")

        cutout_kwargs = {"position": position, "width": 3.0 * u.deg}

        datasets_jolideco[dataset.name] = cutout_maps(maps, **cutout_kwargs)

    return datasets_jolideco


if __name__ == "__main__":
    datasets = read_datasets(snakemake.input.filename_datasets)
    models = read_and_prepare_model(snakemake.input.filename_model)

    datasets.models = models

    prepare_background_model(datasets)

    datasets_jolideco = reduce_datasets(datasets)

    for maps, filename in zip(datasets_jolideco.values(), snakemake.output):
        log.info(f"Writing {filename}")
        maps.write(filename, overwrite=True)
