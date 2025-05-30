```{attention}
This is the **legacy** user guide and may contain information that is out-of-date.
```

# Understanding the global configuration file

This guide goes over [required/optional fields](#fields-in-the-global-configuration-file) in the global configuration file. It also includes some notes on [substitution and template string replacement logic](#substitutions-and-template-string-replacements) in {term}`JSON` configuration files.

See {ref}`here<config-schema>` for the auto-generated schema for the global configuration file.

## Fields in the global configuration file

### Dataset information

Fields containing general information about the dataset.

```{glossary}
`DATASET_NAME`
    **Required** -- The name of the dataset, for documentation purposes.

`VISITS`
    **Required** -- List of unique {term}`visit IDs <Visit ID>` in the manifest. The Nipoppy CLI will raise an error if the manifest contains visits that are not in this list.

`SESSIONS`
    List of unique BIDS-compliant {term}`session IDs <Session ID>` (labels) in the manifest. If not specified, this will be inferred to be the same as the visits. The Nipoppy CLI will raise an error if the manifest contains sessions that are not in this list.
```

### Imaging data organization

Fields for specifying the path to participant-session data directories in {{dpath_pre_reorg}}. Note that these two options are mutually exclusive (cannot both be specified).

```{note}
By default, BIDS prefixes (i.e., `sub-` and `ses-`) are not expected in {{dpath_pre_reorg}} subdirectory names, though this can be customized if needed (see {ref}`here <dicom-dir-map-schema>` for more information).
```

```{glossary}
`DICOM_DIR_PARTICIPANT_FIRST`
    Can be set to `false` to indicate that the data is organized in subdirectories following the {{dpath_pre_reorg}}`/<SESSION_ID>/<PARTICIPANT_ID>` pattern. Otherwise, setting to `true` is equivalent to the default (files in `{{dpath_pre_reorg}}/<PARTICIPANT_ID>/<SESSION_ID>` directories).

`DICOM_DIR_MAP_FILE`
    Explicit mapping file for more custom directory names. See {ref}`here <dicom-dir-map-example>` for an example and {ref}`here <dicom-dir-map-schema>` for the auto-generated schema.
```

### Imaging data processing

Fields for configuring image processing pipelines and container runtimes.

```{glossary}
`CONTAINER_CONFIG`
    Configuration options for the container runtime. This is the top-level configuration, which will be inherited by any downstream container configurations unless they set the `INHERIT` to `false`.

    The configuration options include the command to call the container executable, command-line arguments, and environment variables. See [here](<config-schema>) for the auto-generated schema.

`PROC_PIPELINES`
    **Required** -- A list of configurations for the pipelines to be run on the dataset. See the [auto-generated schemas](<config-schema>) for pipeline configurations and pipeline step configurations for more information.

    Each pipeline must be uniquely identifiable by its name-version combination. Each pipeline is typically associated with a container image file. A pipeline can have multiple steps, each with its own Boutiques descriptor and invocation files (which are still using the same container).

    Both pipeline configurations and pipeline step configurations can have their own container configuration, similar to the {term}`root-level container configuration <CONTAINER_CONFIG>`. By default, these container configurations will be propagated (root -> pipeline -> pipeline step), but this can be disabled by setting `INHERIT` to `false` in a child container configuration.

`BIDS_PIPELINES`
    A list of pipeline configurations for the BIDS converters to be run on the dataset. Note that these have exactly the same fields as the configurations in {term}`PROC_PIPELINES`, though not all fields are relevant for BIDS conversion (e.g., `PYBIDS_IGNORE_FILE` can be set but will never be used).
```

### Other

Miscellaneous fields.

```{glossary}
`SUBSTITUTIONS`
    A user-defined string replacement mapping. For each key-value pair, every instance of the key will be replaced by its corresponding value when the global configuration file is loaded. These substitutions will also be applied to downstream configuration files (e.g., invocation files). See also: <project:#substitutions-and-template-string-replacements>.

`CUSTOM`
    Free field (though must be a dictionary). The global configuration file does not allow custom fields (i.e. that are not part of the schema) at the top level of the file, but users who wish to include additional fields may do so under `CUSTOM`.
```

## Substitutions and template string replacements

Substitutions are static and *user-defined*. They are not mandatory: their sole purpose is to minimize the number of times the same value has to be manually copied into the default global configuration file. They are applied when the configuration file is loaded, before the template string replacement.

Strings or substrings surrounded by double square brackets and starting with the `NIPOPPY_` prefix (e.g., `[[NIPOPPY_PIPELINE_NAME]]`) are template strings whose values are dynamically generated by Nipoppy at runtime. They can be found for example in the default global configuration file's pipeline configurations, as well as in files referenced within pipeline configurations (e.g., invocation files, tracker configuration files).

(global-config-template-strings)=
```{note}
Recognized template strings for the global configuration file are:
- `[[NIPOPPY_<LAYOUT_PROPERTY>]]`, where `<LAYOUT_PROPERTY>` is a property in the Nipoppy {ref}`dataset layout configuration file <layout-schema>` (all uppercase): any path defined in the Nipoppy dataset layout
- `[[NIPOPPY_PIPELINE_NAME]]` and `[[NIPOPPY_PIPELINE_VERSION]]`: the name/version of the BIDS or processing pipeline being run
    - **Note**: These will only be replaced in if the command-line interface subcommand (or the Python API workflow class) accepts pipeline-related arguments
```
