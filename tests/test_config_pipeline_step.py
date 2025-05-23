"""Tests for the pipeline step configuration class."""

from contextlib import nullcontext
from typing import Type

import pytest
from pydantic import BaseModel, ValidationError

from nipoppy.config.pipeline_step import (
    AnalysisLevelType,
    BasePipelineStepConfig,
    BidsPipelineStepConfig,
    ExtractionPipelineStepConfig,
    ProcPipelineStepConfig,
)

FIELDS_STEP_BASE = [
    "NAME",
    "DESCRIPTOR_FILE",
    "INVOCATION_FILE",
    "HPC_CONFIG_FILE",
    "CONTAINER_CONFIG",
    "ANALYSIS_LEVEL",
]

FIELDS_STEP_PROC = FIELDS_STEP_BASE + [
    "PYBIDS_IGNORE_FILE",
    "TRACKER_CONFIG_FILE",
    "GENERATE_PYBIDS_DATABASE",
]
FIELDS_STEP_BIDS = FIELDS_STEP_BASE + ["UPDATE_STATUS"]
FIELDS_STEP_EXTRACTION = FIELDS_STEP_BASE


@pytest.mark.parametrize(
    "step_class,fields,data_list",
    [
        (
            BasePipelineStepConfig,
            FIELDS_STEP_BASE,
            [
                {"NAME": "step_name"},
                {
                    "DESCRIPTOR_FILE": "PATH_TO_DESCRIPTOR_FILE",
                    "INVOCATION_FILE": "PATH_TO_INVOCATION_FILE",
                },
                {"CONTAINER_CONFIG": {}},
            ],
        ),
        (
            BidsPipelineStepConfig,
            FIELDS_STEP_BIDS,
            [{"UPDATE_STATUS": True}],
        ),
        (
            ProcPipelineStepConfig,
            FIELDS_STEP_PROC,
            [{"PYBIDS_IGNORE_FILE": "PATH_TO_PYBIDS_IGNORE_FILE"}],
        ),
        (
            ExtractionPipelineStepConfig,
            FIELDS_STEP_EXTRACTION,
            [],
        ),
    ],
)
def test_field_base(step_class: type[BaseModel], fields, data_list):
    for data in data_list:
        pipeline_step_config = step_class(**data)
        for field in fields:
            assert hasattr(pipeline_step_config, field)

        assert len(set(pipeline_step_config.model_dump())) == len(fields)


@pytest.mark.parametrize(
    "model_class",
    [ProcPipelineStepConfig, BidsPipelineStepConfig, ExtractionPipelineStepConfig],
)
def test_no_extra_field(model_class):
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        model_class(not_a_field="a")


@pytest.mark.parametrize(
    "analysis_level", ["participant_session", "participant", "session", "group"]
)
def test_analysis_level(analysis_level):
    assert BasePipelineStepConfig(ANALYSIS_LEVEL=analysis_level)


def test_analysis_level_invalid():
    with pytest.raises(ValidationError):
        BasePipelineStepConfig(ANALYSIS_LEVEL="invalid")


@pytest.mark.parametrize(
    "step_class",
    [ProcPipelineStepConfig, BidsPipelineStepConfig, ExtractionPipelineStepConfig],
)
def test_substitutions(step_class: Type[BasePipelineStepConfig]):
    step_config = step_class(
        NAME="step_name",
        DESCRIPTOR_FILE="descriptor-[[STEP_NAME]].json",
        INVOCATION_FILE="invocation-[[STEP_NAME]].json",
    )
    assert str(step_config.DESCRIPTOR_FILE) == "descriptor-step_name.json"
    assert str(step_config.INVOCATION_FILE) == "invocation-step_name.json"


@pytest.mark.parametrize(
    "descriptor_file,invocation_file,expect_error",
    [
        (None, None, False),
        ("descriptor.json", "invocation.json", False),
        ("descriptor.json", None, True),
        (None, "invocation.json", True),
    ],
)
def test_descriptor_invocation_fields(descriptor_file, invocation_file, expect_error):
    with (
        pytest.raises(
            ValidationError,
            match=(
                "DESCRIPTOR_FILE and INVOCATION_FILE must both be defined "
                "or both be None, "
            ),
        )
        if expect_error
        else nullcontext()
    ):
        BasePipelineStepConfig(
            DESCRIPTOR_FILE=descriptor_file, INVOCATION_FILE=invocation_file
        )


@pytest.mark.parametrize(
    "data,pipeline_class,expect_error",
    [
        (
            {
                "DESCRIPTOR_FILE": "/descriptor.json",
                "INVOCATION_FILE": "invocation.json",
            },
            BasePipelineStepConfig,
            True,
        ),
        (
            {
                "DESCRIPTOR_FILE": "descriptor.json",
                "INVOCATION_FILE": "/invocation.json",
            },
            BasePipelineStepConfig,
            True,
        ),
        (
            {"PYBIDS_IGNORE_FILE": "/pybids_ignore.json"},
            ProcPipelineStepConfig,
            True,
        ),
        (
            {"TRACKER_CONFIG_FILE": "/tracker_config.json"},
            ProcPipelineStepConfig,
            True,
        ),
        (
            {
                "DESCRIPTOR_FILE": "descriptor.json",
                "INVOCATION_FILE": "invocation.json",
                "PYBIDS_IGNORE_FILE": "pybids_ignore.json",
                "TRACKER_CONFIG_FILE": "tracker_config.json",
            },
            ProcPipelineStepConfig,
            False,
        ),
    ],
)
def test_absolute_paths(data, pipeline_class, expect_error):
    with (
        pytest.raises(ValidationError, match=".* must be a relative path, got")
        if expect_error
        else nullcontext()
    ):
        pipeline_class(**data)


@pytest.mark.parametrize(
    "analysis_level,expect_error",
    [
        (AnalysisLevelType.participant_session, False),
        (AnalysisLevelType.participant, True),
        (AnalysisLevelType.session, True),
        (AnalysisLevelType.group, True),
    ],
)
def test_tracker_config_analysis_level(analysis_level, expect_error):
    with (
        pytest.raises(
            ValidationError,
            match=(
                "cannot be set if ANALYSIS_LEVEL is not "
                f"{AnalysisLevelType.participant_session}"
            ),
        )
        if expect_error
        else nullcontext()
    ):
        ProcPipelineStepConfig(
            TRACKER_CONFIG_FILE="tracker_config.json",
            ANALYSIS_LEVEL=analysis_level,
        )


@pytest.mark.parametrize(
    "update_status,analysis_level,expect_error",
    [
        (True, AnalysisLevelType.participant_session, False),
        (True, AnalysisLevelType.participant, True),
        (True, AnalysisLevelType.session, True),
        (True, AnalysisLevelType.group, True),
        (False, AnalysisLevelType.participant_session, False),
        (False, AnalysisLevelType.participant, False),
        (False, AnalysisLevelType.session, False),
        (False, AnalysisLevelType.group, False),
    ],
)
def test_update_status_analysis_level(update_status, analysis_level, expect_error):
    with (
        pytest.raises(
            ValidationError,
            match=(
                "cannot be True if ANALYSIS_LEVEL is not "
                f"{AnalysisLevelType.participant_session}"
            ),
        )
        if expect_error
        else nullcontext()
    ):
        BidsPipelineStepConfig(
            UPDATE_STATUS=update_status,
            ANALYSIS_LEVEL=analysis_level,
        )
