# mamba_conquer

This small tool is meant to help with solving big conda environments.

It uses mamba and libmambapy for solving.

The solver uses mamba's internal functions, so the functionality might
break if mamba changes the functionality of said functions.

## Installation

1. Download and install [mamba-forge](https://github.com/conda-forge/miniforge#mambaforge).
   Alternatively, you can install environment from the included environment.yaml.

2. Test `mamba-conquer` with:

```sh
  python mamba_conquer.py --env test-env.yaml 'python=3.9.*'
```

## Usage

`mamba_conquer` does the following:

- Given an environment file with various dependencies, `mamba_conquer` will split the
  required solve to multiple solves (by default, to 5 packages each).
- `mamba_conquer` will try to solve each of these small environments.
- If given important packages from a command line, `mamba_conquer` will add these packages to
  every solve.

See

```sh
python mamba_conquer.py --help
```

for all flags.

## Example

The included environment in `test-env.yaml` does not solve with Python 3.9, as `gurobi` is
only supported for Python<3.9. However, the environment solve never finishes.

Trying
```sh
  python mamba_conquer.py --env test-env.yaml 'python=3.9.*'
```
will reveal that `gurobi` is the problematic package.

Testing another build with
```sh
  python mamba_conquer.py --env test-env.yaml 'python=3.8.*'
```
shows that with Python 3.8, the solve would work.
