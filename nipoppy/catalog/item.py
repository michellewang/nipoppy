"""Catalog pipeline validation function."""

import logging
from functools import cached_property
from pathlib import Path
from typing import Optional

import boutiques
from typing_extensions import Self

from nipoppy.base import Base
from nipoppy.config.pipeline import BasePipelineConfig
from nipoppy.config.pipeline_step import ProcPipelineStepConfig
from nipoppy.config.tracker import TrackerConfig
from nipoppy.layout import DatasetLayout
from nipoppy.utils import StrOrPathLike, load_json


def validate_config_files(
    pipeline_config: BasePipelineConfig,
    logger: Optional[logging.Logger] = None,
    log_level=logging.DEBUG,
) -> list[Path]:
    def log_msg(msg: str) -> None:
        if logger is not None:
            logger.log(level=log_level, msg=msg)

    fpaths = []

    for step in pipeline_config.STEPS:
        log_msg(f"Validating files for step: {step.NAME}")

        if step.DESCRIPTOR_FILE is not None:
            log_msg(f"Checking descriptor file: {step.DESCRIPTOR_FILE}")
            descriptor_str = step.DESCRIPTOR_FILE.read_text()
            boutiques.validate(descriptor_str)
            fpaths.append(step.DESCRIPTOR_FILE)

            if step.INVOCATION_FILE is not None:
                log_msg(
                    f"Checking invocation file: {step.INVOCATION_FILE}",
                )
                boutiques.invocation(
                    "--invocation", step.INVOCATION_FILE.read_text(), descriptor_str
                )
                fpaths.append(step.INVOCATION_FILE)

        if isinstance(step, ProcPipelineStepConfig):
            if step.TRACKER_CONFIG_FILE is not None:
                log_msg(f"Checking tracker config file: {step.TRACKER_CONFIG_FILE}")
                TrackerConfig(**load_json(step.TRACKER_CONFIG_FILE))
                fpaths.append(step.TRACKER_CONFIG_FILE)
            if step.PYBIDS_IGNORE_FILE is not None:
                log_msg(
                    f"Checking PyBIDS ignore patterns file: {step.PYBIDS_IGNORE_FILE}"
                )
                load_json(step.PYBIDS_IGNORE_FILE)
                fpaths.append(step.PYBIDS_IGNORE_FILE)

        return fpaths


class PipelineBundle(Base):
    """Class for pipeline catalog items."""

    def __init__(self, dpath: StrOrPathLike) -> None:
        """Initialize the PipelineBundle object from a directory path."""
        self.dpath_bundle: Path = Path(dpath).resolve()
        self.fpath_config = self.dpath_bundle / DatasetLayout.fname_pipeline_config

    @cached_property
    def config(self) -> BasePipelineConfig:
        """Main pipeline configuration."""
        if not self.fpath_config.exists():
            raise FileNotFoundError(
                f"No pipeline configuration file found at {self.fpath_config}"
            )
        return BasePipelineConfig(**load_json(self.fpath_config))

    def validate(self) -> Self:
        """Validate the pipeline configuration files."""
        # check that file contents are valid
        fpaths = validate_config_files(self.config)

        # check that all files are within the bundle directory
        for fpath in fpaths:
            if not any(
                [
                    dpath_parent.resolve() == self.dpath_bundle
                    for dpath_parent in fpath.parents
                ]
            ):
                raise ValueError(
                    f"Path {fpath} is not within the bundle directory "
                    f"{self.dpath_bundle}"
                )

        return self
