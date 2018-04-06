# Docketeer

Simulation for testing Board of Veterans' Appeals docket auto-assignment algorithms

## Setup

This instructions assume you have installed [pyenv](https://github.com/pyenv/pyenv).

```sh
pyenv install $(cat .python-version)
pip install virtualenv
virtualenv env
source env/bin/activate
pip install -r requirements.txt
```

## Running the notebook

```sh
source env/bin/activate
jupyter notebook
```

And open `docketeer.ipynb`

## What is all this crap?

Chris needs to document it. The main things to pay attention to are the `select_cases_for_judge()` function, which contains the current draft auto-assignment algorithm, and the pretty, pretty charts down at the bottom.
