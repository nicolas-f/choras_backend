# Getting Started

Here you will see what you need to do to run the backend application

## Pre-requisites

1. The latest version of git: <https://git-scm.com/downloads>
2. Conda: <https://www.anaconda.com/download>

## Initialising this repository

1. Clone this repository to a location of your choice. If you have issues with cloning this repository (and its submodules), you can download the zipped repository via the releases page of this repository: <https://github.com/choras-org/backend/releases>
2. In the command window / terminal, navigate (`cd`) to the repository.
3. Run the following line of code to check out the correct versions of the (nested) submodules:

``` shell
git submodule update --init --recursive
```

4. The repository should now have the latest (correct) state.
5. Every time you make changes to submodules, remember to run

``` shell
git submodule update --recursive
```

to include the correct commits of all the submodules.

## Setting up the environment

1. In the command window, run ```cd backend``` to navigate to the backend folder.
2. Create a new environment and install all the requirements by running the following (this will take a minute)

```shell
conda create -n choras python=3.10
conda activate choras
pip install -r requirements.txt
```
