# Getting Started

Here you will see what you need to do to run the backend application

## Pre-requisites

1. The latest version of git: https://git-scm.com/downloads
2. Conda: https://www.anaconda.com/download

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

## Creating the database

1. Create the database by running `flask create-db` (you only have to do this once).

## Running the backend processes

### Starting the database server

Run the application by running

``` shell
flask run
```

You have succeeded in running the backend if you see something like this in the command window:

``` shell
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:5001
Press CTRL+C to quit
 * Restarting with watchdog (fsevents)
 * Debugger is active!
 * Debugger PIN: 903-417-292
```

Note that in order to run the application correctly, this command window should remain open with the `flask run` process running.

### Running Celery (open a new command window)

Celery is a package that allows for distributed task queueing. In the case of CHORAS, it allows to offload the simulation to a separate "worker" so that other processes (such as queueing other tasks) will not be blocked.

To run Celery:

1. Open a new command window and navigate to the `backend` folder.
2. Activate the previously created environment by running `conda activate choras`.
3. Run Celery by running:

``` shell
celery -A app.celery worker --loglevel=info -P eventlet
```

4. You should see something like:

``` shell
 -------------- celery@TUE031950 v5.4.0 (opalescent)
--- ***** -----
-- ******* ---- Windows-10-10.0.19045-SP0 2025-02-02 14:47:11
- *** --- * ---
- ** ---------- [config]
- ** ---------- .> app:         ui_backend:0x2bc5d65f640
- ** ---------- .> transport:   sqla+sqlite:///C:\Users\20225896\repositories\CHORAS\backend\celerydb.sqlite
- ** ---------- .> results:     sqlite:///C:\Users\20225896\repositories\CHORAS\backend\celerydb.sqlite
- *** --- * --- .> concurrency: 12 (eventlet)
-- ******* ---- .> task events: OFF (enable -E to monitor tasks in this worker)
--- ***** -----
 -------------- [queues]
                .> celery           exchange=celery(direct) key=celery


[tasks]
  . app.services.simulation_service.run_solver

[2025-02-02 14:47:11,628: INFO/MainProcess] Connected to sqla+sqlite:///C:\Users\20225896\repositories\CHORAS\backend\celerydb.sqlite
[2025-02-02 14:47:11,645: INFO/MainProcess] celery@TUE031950 ready.
```
