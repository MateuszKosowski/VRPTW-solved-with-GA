import subprocess
import os
from concurrent.futures import ProcessPoolExecutor

from test_kits import *

def launch(params):
    ds_name = os.path.splitext(os.path.basename(params['file']))[0]
    output_file = f"output/results_{ds_name}_pop{params['population_size']}_gen{params['generations']}_tour{params['tournament_size']}_mut{params['mutation_rate']}_id{params['id']}.json"

    cmd = [
        'python', 'main.py',
        str(params['file']),
        output_file,
        str(params['population_size']),
        str(params['generations']),
        str(params['tournament_size']),
        str(params['mutation_rate'])
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Crash with parameters: {params}")
        print(f"Error: {e}")


def main():
    jobs = []

    datasets = ["data/c101.txt", "data/r101.txt", "data/rc101.txt"]

    for exp in EXPERIMENTS_GA:
        for ds in datasets:
            job = {
                "file": ds,
                "population_size": exp["population_size"],
                "generations": exp["generations"],
                "tournament_size": exp["tournament_size"],
                "mutation_rate": exp["mutation_rate"]
            }
            jobs.append(job)

    all_jobs = []
    for job in jobs:
        for r in range(5):
            new_job = job.copy()
            new_job['id'] = r
            all_jobs.append(new_job)

    print(f"Total jobs to run: {len(all_jobs)}")

    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        executor.map(launch, all_jobs)


if __name__ == '__main__':
    main()
