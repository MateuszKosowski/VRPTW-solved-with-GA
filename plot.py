import os
import json
import re
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from glob import glob
from client import Client

def load_solomon_file(filename):
    clients = []
    with open(filename, 'r') as f:
        lines = f.readlines()

    start_parsing = False
    for line in lines:
        if not line.strip():
            continue
        if "CUST NO." in line:
            start_parsing = True
            continue
        if start_parsing:
            parts = line.split()
            if len(parts) >= 7:
                c = Client(
                    id=int(parts[0]),
                    x=int(parts[1]),
                    y=int(parts[2]),
                    demand=int(parts[3]),
                    ready_time=int(parts[4]),
                    due_date=int(parts[5]),
                    service_time=int(parts[6])
                )
                clients.append(c)

    points = [(c.x, c.y) for c in clients]
    return points

def load_json(file):
    with open(file) as f:
        return [json.loads(line) for line in f]

def plot_cost_history(output_dir, datasets_files, baseline_params, filename=None,
                               title="Długość trasy vs Generacje dla wszystkich datasetów"):
    all_files = glob(os.path.join(output_dir, "*.json"))
    
    plt.figure(figsize=(10,6))
    
    for ds_file in datasets_files:
        ds_name = os.path.splitext(os.path.basename(ds_file))[0]

        baseline_files = [
            f for f in all_files
            if ds_name in f
            and f"pop{baseline_params['population_size']}" in f
            and f"gen{baseline_params['generations']}" in f
            and f"tour{baseline_params['tournament_size']}" in f
            and f"mut{baseline_params['mutation_rate']}" in f
        ]
        if not baseline_files:
            print(f"No baseline files found for {ds_name}")
            continue

        all_runs = []
        for f in baseline_files:
            all_runs.extend(load_json(f))

        best_run = min(all_runs, key=lambda r: r["best_cost"])
        plt.plot(best_run["history"], label=ds_name)

    plt.xlabel("Generacja")
    plt.ylabel("Długość trasy")
    plt.title(title)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    if filename:
        plt.savefig(filename, dpi=200)
    else:
        plt.show()
    plt.close()


def draw_multiple_routes(points, routes, filename=None, title="Trasy pojazdów"):
    plt.figure(figsize=(6,6))
    depot = points[0]

    for route in routes:
        route_with_depot = [0] + route + [0]
        ordered = [points[i] for i in route_with_depot]
        xs, ys = zip(*ordered)
        plt.plot(xs, ys, marker="o")
        plt.scatter(xs, ys)

    plt.scatter(depot[0], depot[1], color='red', s=100, zorder=6, label='Depot')

    plt.title(title)
    plt.gca().set_aspect("equal")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(filename, dpi=200)

def generate_all_baseline_plots(output_dir, datasets_files, baseline_params, plots_dir="plots"):
    os.makedirs(plots_dir, exist_ok=True)
    all_files = glob(os.path.join(output_dir, "*.json"))

    for ds_file in datasets_files:
        ds_name = os.path.splitext(os.path.basename(ds_file))[0]
        points = load_solomon_file(ds_file)

        baseline_files = [
            f for f in all_files
            if ds_name in f
            and f"pop{baseline_params['population_size']}" in f
            and f"gen{baseline_params['generations']}" in f
            and f"tour{baseline_params['tournament_size']}" in f
            and f"mut{baseline_params['mutation_rate']}" in f
        ]
        if not baseline_files:
            print(f"No baseline files found for {ds_name}")
            continue

        all_runs = []
        for f in baseline_files:
            all_runs.extend(load_json(f))

        plot_cost_history(output_dir, datasets_files, baseline_params,
                           filename=f"{plots_dir}/all_datasets_cost_history.png")



        best_run = min(all_runs, key=lambda r: r["best_cost"])
        draw_multiple_routes(points, best_run["best_route"], f"{plots_dir}/{ds_name}_all_routes.png",
                             title=f"{ds_name} - Wszystkie trasy (baseline)")

def prepare_boxplot_df(output_dir):
    all_files = glob(f"{output_dir}/*.json")
    records = []

    params = ["pop", "gen", "tour", "mut"]

    for f in all_files:
        runs = load_json(f)
        if not runs:
            continue

        ds_name = os.path.basename(f).split("_")[1]  # results_<dataset>_...
        param_values = {}
        for param in params:
            match = re.search(f"{param}([0-9\.]+)", f)
            if match:
                param_values[param] = float(match.group(1))
            else:
                param_values[param] = None

        for r in runs:
            record = {"dataset": ds_name, "best_cost": r["best_cost"]}
            record.update(param_values)
            records.append(record)

    df = pd.DataFrame(records)
    return df

def plot_boxplots(df, output_dir="plots"):
    os.makedirs(output_dir, exist_ok=True)

    params = ["pop", "gen", "tour", "mut"]
    names_title = {
        "pop": "wielkośći populacji",
        "gen": "generacji",
        "tour": "rozmiaru turnieju",
        "mut": "szansy mutacji"
    }

    names_x = {
        "pop": "Rozmiar populacji",
        "gen": "Ilość generacji",
        "tour": "Rozmiar turnieju",
        "mut": "Szansa mutacji"
    }
    datasets = sorted(df["dataset"].unique())

    for param in params:
        df_param = df.copy()
        for other_param in params:
            if other_param != param:
                baseline_val = df_param[other_param].mode()[0]
                df_param = df_param[df_param[other_param] == baseline_val]

        if df_param.empty:
            print(f"No data to plot for {param}. Skipping.")
            continue

        plt.figure(figsize=(8,6))
        sns.boxplot(x=param, y="best_cost", hue="dataset", data=df_param)

        plt.title(f"Wpływ {names_title[param]} na długość trasy")
        plt.xlabel(names_x[param])
        plt.ylabel("Długość trasy")
        plt.legend(title="Dataset")
        plt.tight_layout()
        plt.savefig(f"{output_dir}/boxplot_{param}.png", dpi=200)
        plt.close()
        print(f"Saved boxplot for {param}")

if __name__ == "__main__":
    datasets_files = ["data/c101.txt", "data/r101.txt", "data/rc101.txt"]

    baseline_params = {
        "population_size": 50,
        "generations": 10000,
        "tournament_size": 5,
        "mutation_rate": 0.05
    }

    output_dir = "output"
    plots_dir = "plots"

    generate_all_baseline_plots(output_dir, datasets_files, baseline_params, plots_dir)

    df = prepare_boxplot_df(output_dir)
    plot_boxplots(df, plots_dir)

    print("Wykresy wygenerowane w katalogu 'plots'")
