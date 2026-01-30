import math
import argparse
import time
import numpy as np
import json
from random import random, shuffle, sample

from client import Client
from plot import *


def load_data(filename):
    clients = []
    vehicle_capacity = 0

    with open(filename, 'r') as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if "CAPACITY" in line:
            capacity_line = lines[i + 1].strip()
            parts = capacity_line.split()
            if len(parts) >= 2:
                vehicle_capacity = int(parts[1])
                print(f"Znaleziono pojemność pojazdu: {vehicle_capacity}")
            break

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

    print(f"Wczytano {len(clients)} punktów (1 Depot + {len(clients) - 1} Klientów).")
    return vehicle_capacity, clients

def calculate_distance(c1, c2):
    return math.hypot(c1.x - c2.x, c1.y - c2.y)

def create_distance_matrix(clients):
    num_clients = len(clients)
    matrix = [[0.0] * num_clients for _ in range(num_clients)]

    for i in range(num_clients):
        for j in range(num_clients):
            if i == j:
                matrix[i][j] = 0.0
            else:
                dist = calculate_distance(clients[i], clients[j])
                matrix[i][j] = dist

    print("Macierz odległości wygenerowana.")
    return matrix


def calculate_routes(client_ids, clients, dist_matrix, capacity):
    routes = []
    current_route = [] 
    current_load = 0
    current_time = 0.0
    prev_id = 0

    depot = clients[0]
    total_dist = 0.0 

    for client_id in client_ids:
        client = clients[client_id]

        dist_from_prev = dist_matrix[prev_id][client_id]
        arrival_time = current_time + dist_from_prev

        start_service = max(arrival_time, client.ready_time)
        finish_time = start_service + client.service_time

        dist_home = dist_matrix[client_id][0]
        arrival_at_depot = finish_time + dist_home

        is_feasible = True

        if current_load + client.demand > capacity:
            is_feasible = False

        elif arrival_time > client.due_date:
            is_feasible = False

        elif arrival_at_depot > depot.due_date:
            is_feasible = False

        if is_feasible:
            current_route.append(client_id)
            current_load += client.demand
            current_time = finish_time
            prev_id = client_id
            total_dist += dist_from_prev
        else:
            if current_route:
                return_dist = dist_matrix[prev_id][0]
                total_dist += return_dist
                routes.append(current_route)

            current_route = [client_id] 
            current_load = client.demand

            dist_from_depot = dist_matrix[0][client_id]
            total_dist += dist_from_depot

            arrival_time = 0.0 + dist_from_depot
            start_service = max(arrival_time, client.ready_time)
            current_time = start_service + client.service_time
            prev_id = client_id

    if current_route:
        return_dist = dist_matrix[prev_id][0]
        total_dist += return_dist
        routes.append(current_route)

    return routes, total_dist

def calculate_fitness(num_vehicles, distance):
    return (num_vehicles * 2000) + distance


def crossover(parent1, parent2):
    size = len(parent1)
    start, end = sorted(sample(range(size), 2))
    child = [-1] * size
    child[start:end] = parent1[start:end]

    current_pos = end
    for gene in parent2:
        if gene not in child:
            if current_pos >= size:
                current_pos = 0
            child[current_pos] = gene
            current_pos += 1

    return child


def mutate(genome):
    idx1, idx2 = sample(range(len(genome)), 2)
    genome[idx1], genome[idx2] = genome[idx2], genome[idx1]
    return genome


def check_route(route_ids, clients, dist_matrix, capacity):
    depot = clients[0]
    current_time = 0.0
    current_load = 0
    total_dist = 0.0
    prev_id = 0 

    for client_id in route_ids:
        client = clients[client_id]

        if current_load + client.demand > capacity:
            return False, 0.0, "Przeciążenie"

        dist = dist_matrix[prev_id][client_id]
        total_dist += dist
        arrival_time = current_time + dist

        if arrival_time > client.due_date:
            return False, 0.0, "Spóźnienie"

        start_service = max(arrival_time, client.ready_time)

        current_time = start_service + client.service_time
        current_load += client.demand
        prev_id = client_id

    dist_home = dist_matrix[prev_id][0]
    total_dist += dist_home
    arrival_at_depot = current_time + dist_home

    if arrival_at_depot > depot.due_date:
        return False, 0.0, "Spóźniony powrót"

    return True, total_dist, "OK"

def optimize_route_2opt(route, clients, dist_matrix, capacity):
    best_route = route[:]
    _, best_dist, _ = check_route(best_route, clients, dist_matrix, capacity)

    improved = True
    while improved:
        improved = False
        for i in range(len(best_route) - 1):
            for j in range(i + 1, len(best_route)):
                if j - i == 1: continue

                new_route = best_route[:i] + best_route[i:j + 1][::-1] + best_route[j + 1:]

                valid, new_dist, _ = check_route(new_route, clients, dist_matrix, capacity)

                if valid and new_dist < best_dist - 0.01: 
                    best_route = new_route
                    best_dist = new_dist
                    improved = True
                    break
            if improved: break

    return best_route, best_dist


def run_genetic_algorithm(clients, dist_matrix, capacity, population_size, generations, tournament_size, mutation_rate):
    customer_ids = list(range(1, len(clients)))
    cost_history = []

    population = []
    for _ in range(population_size):
        shuffled = customer_ids[:]
        shuffle(shuffled)
        population.append(shuffled)

    best_overall_genome = None
    best_overall_fitness = float('inf')
    best_vehicles_count = float('inf')
    best_distance_val = float('inf')

    print(f"\nSTART HYBRYDOWEGO GENETYKA (Max pokoleń: {generations})")
    print("To może chwilę potrwać, bo 2-opt intensywnie liczy...")

    for gen in range(generations):
        scored_population = []

        for genome in population:
            raw_routes, _ = calculate_routes(genome, clients, dist_matrix, capacity)

            optimized_routes = []
            total_optimized_dist = 0.0

            for route in raw_routes:
                if len(route) > 2:
                    opt_route, opt_dist = optimize_route_2opt(route, clients, dist_matrix, capacity)
                    optimized_routes.append(opt_route)
                    total_optimized_dist += opt_dist
                else:
                    _, d, _ = check_route(route, clients, dist_matrix, capacity)
                    optimized_routes.append(route)
                    total_optimized_dist += d

            num_vehicles = len(optimized_routes)
            fitness = calculate_fitness(num_vehicles, total_optimized_dist)

            scored_population.append((fitness, genome, num_vehicles, total_optimized_dist))

            if fitness < best_overall_fitness:
                best_overall_fitness = fitness
                best_overall_genome = genome[:]
                best_vehicles_count = num_vehicles
                best_distance_val = total_optimized_dist

        best_gen_cost = min(x[3] for x in scored_population)
        cost_history.append(best_gen_cost)

        new_population = []

        scored_population.sort(key=lambda x: x[0])  
        new_population.append(scored_population[0][1])
        new_population.append(scored_population[1][1])

        while len(new_population) < population_size:
            tournament = sample(scored_population, tournament_size)
            parent1 = min(tournament, key=lambda x: x[0])[1]

            tournament = sample(scored_population, tournament_size)
            parent2 = min(tournament, key=lambda x: x[0])[1]

            child = crossover(parent1, parent2)

            if random() < mutation_rate:
                child = mutate(child)

            new_population.append(child)

        population = new_population

    return best_overall_genome, best_vehicles_count, cost_history

parser = argparse.ArgumentParser()

parser.add_argument("filename")
parser.add_argument("output")
parser.add_argument("population_size")
parser.add_argument("generations")
parser.add_argument("tournament_size")
parser.add_argument("mutation_rate")

args = parser.parse_args()

capacity, clients = load_data(args.filename)

dist_matrix = create_distance_matrix(clients)

start = time.perf_counter()
best_genome, best_vehicles, cost_history = run_genetic_algorithm(clients, dist_matrix, capacity, int(args.population_size), int(args.generations), int(args.tournament_size), float(args.mutation_rate))
elapsed = time.perf_counter() - start

print("\n--- KONIEC OBLICZEŃ ---")

raw_routes, _ = calculate_routes(best_genome, clients, dist_matrix, capacity)

final_routes = []
final_dist = 0.0
for r in raw_routes:
    opt_r, opt_d = optimize_route_2opt(r, clients, dist_matrix, capacity)
    final_routes.append(opt_r)
    final_dist += opt_d

result = {
    "dataset": args.filename,
    "population_size": args.population_size,
    "generations": args.generations,
    "tournament_size": args.tournament_size,
    "mutation_rate": args.mutation_rate,
    "best_cost": final_dist,
    "worst_cost": max(cost_history),
    "mean_cost": sum(cost_history)/len(cost_history),
    "std_cost": np.std(cost_history),
    "history": cost_history,
    "best_route": final_routes,
    "time": elapsed
}

with open(args.output, "a") as f:
    f.write(json.dumps(result) + "\n")

print(f"Najlepszy wynik (z 2-opt):")
print(f"Liczba pojazdów: {len(final_routes)}")
print(f"Całkowity dystans: {final_dist:.2f}")
print(f"Czas wykonania: {elapsed}")
print(len(cost_history))

for i, route in enumerate(final_routes):
    print(f"Pojazd {i + 1}: {route}")