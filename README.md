# iaaf
*Want to find cool ~audio~ Anything?  You need iaaf, af.*


## Installation
It is recommended to install with [uv](https://docs.astral.sh/uv/).
```
uv tool install git+https://github.com/karldreher/iaaf
```

## Usage

```sh
# Search by title (media type is required)
iaaf search "grateful dead" --type audio --min-size 100MB --max-size 2GB

# Treat the argument as a query against all metadata
iaaf search "jazz AND live" --type audio --query-all

# Configure Internet Archive credentials
iaaf configure

iaaf --version
iaaf --verbose search "title" --type texts
```
