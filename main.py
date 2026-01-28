import math
from random import random, shuffle, sample

from client import Client


def load_data(filename):
    clients = []
    vehicle_capacity = 0

    with open(filename, 'r') as f:
        lines = f.readlines()

    # Wczytanie pojemności pojazdu
    for i, line in enumerate(lines):
        if "CAPACITY" in line:
            capacity_line = lines[i + 1].strip()
            parts = capacity_line.split()
            if len(parts) >= 2:
                vehicle_capacity = int(parts[1])
                print(f"Znaleziono pojemność pojazdu: {vehicle_capacity}")
            break

    # Wczytanie danych klientów oraz magazynu
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
    routes = []  # Tu będą gotowe trasy (lista list)
    current_route = []  # Trasa aktualnego pojazdu

    # Stan aktualnego pojazdu
    current_load = 0  # Ile ma towaru
    current_time = 0.0  # Która jest godzina
    prev_id = 0  # Gdzie jest teraz (0 = Depot)

    depot = clients[0]
    total_dist = 0.0  # Suma kilometrów całej floty

    for client_id in client_ids:
        client = clients[client_id]

        # Obliczamy parametry dojazdu do tego klienta
        dist_from_prev = dist_matrix[prev_id][client_id]
        arrival_time = current_time + dist_from_prev

        # Czekanie (jeśli przyjechaliśmy przed otwarciem)
        start_service = max(arrival_time, client.ready_time)
        finish_time = start_service + client.service_time

        # Sprawdzenie powrotu do bazy (czy po obsłudze zdążymy wrócić?)
        dist_home = dist_matrix[client_id][0]
        arrival_at_depot = finish_time + dist_home

        # --- SPRAWDZANIE OGRANICZEŃ ---
        is_feasible = True

        # 1. Czy towar się zmieści?
        if current_load + client.demand > capacity:
            is_feasible = False

        # 2. Czy nie spóźnimy się do klienta?
        elif arrival_time > client.due_date:
            is_feasible = False

        # 3. Czy zdążymy wrócić do bazy przed jej zamknięciem?
        elif arrival_at_depot > depot.due_date:
            is_feasible = False

        # --- DECYZJA ---
        if is_feasible:
            # Klient pasuje -> Wsiada
            current_route.append(client_id)
            current_load += client.demand
            current_time = finish_time
            prev_id = client_id
            total_dist += dist_from_prev
        else:
            # Klient nie pasuje -> To auto musi wracać do bazy
            if current_route:
                # Doliczamy powrót starego auta do bazy
                return_dist = dist_matrix[prev_id][0]
                total_dist += return_dist
                routes.append(current_route)

            # --- BIERZEMY NOWE AUTO ---
            current_route = [client_id]  # Pierwszy pasażer nowego auta
            current_load = client.demand

            # Nowe auto jedzie z depotu (0)
            dist_from_depot = dist_matrix[0][client_id]
            total_dist += dist_from_depot

            # Ustawiamy czas nowego auta
            arrival_time = 0.0 + dist_from_depot
            start_service = max(arrival_time, client.ready_time)
            current_time = start_service + client.service_time
            prev_id = client_id

    # Na koniec pętli: ostatnie auto też musi wrócić do bazy
    if current_route:
        return_dist = dist_matrix[prev_id][0]
        total_dist += return_dist
        routes.append(current_route)

    return routes, total_dist

def calculate_fitness(num_vehicles, distance):
    return (num_vehicles * 2000) + distance


def crossover(parent1, parent2):
    """
    Krzyżowanie (Ordered Crossover - OX).
    Bierze fragment trasy od rodzica 1 i uzupełnia brakujące miasta z rodzica 2.
    To zapewnia, że każdy klient występuje w trasie dokładnie raz.
    """
    size = len(parent1)
    # Losujemy punkt startu i końca wycinka
    start, end = sorted(sample(range(size), 2))

    # Tworzymy puste dziecko
    child = [-1] * size

    # Kopiujemy fragment od rodzica 1
    child[start:end] = parent1[start:end]

    # Resztę wypełniamy z rodzica 2 (w kolejności występowania)
    current_pos = end
    for gene in parent2:
        if gene not in child:
            if current_pos >= size:
                current_pos = 0
            child[current_pos] = gene
            current_pos += 1

    return child


def mutate(genome):
    """
    Mutacja: Zamienia miejscami dwóch losowych klientów.
    """
    idx1, idx2 = sample(range(len(genome)), 2)
    genome[idx1], genome[idx2] = genome[idx2], genome[idx1]
    return genome


def check_route(route_ids, clients, dist_matrix, capacity):
    """
    Symuluje przejazd trasą, aby sprawdzić poprawność (okna czasowe, pojemność)
    i obliczyć dokładny dystans.

    Argumenty:
    - route_ids: lista ID klientów (np. [5, 12, 1])
    - clients: lista obiektów Client
    - dist_matrix: macierz odległości
    - capacity: pojemność pojazdu

    Zwraca: (czy_poprawna, dystans, komunikat)
    """
    depot = clients[0]
    current_time = 0.0
    current_load = 0
    total_dist = 0.0
    prev_id = 0  # Startujemy z Depotu (ID 0)

    for client_id in route_ids:
        client = clients[client_id]

        # 1. Sprawdzenie pojemności
        if current_load + client.demand > capacity:
            return False, 0.0, "Przeciążenie"

        # 2. Jazda do klienta
        dist = dist_matrix[prev_id][client_id]
        total_dist += dist
        arrival_time = current_time + dist

        # 3. Sprawdzenie okna czasowego (Czy nie za późno?)
        if arrival_time > client.due_date:
            return False, 0.0, "Spóźnienie"

        # 4. Obsługa czekania (Czy nie za wcześnie?)
        # Jeśli przybyliśmy przed otwarciem, czekamy.
        start_service = max(arrival_time, client.ready_time)

        # 5. Wykonanie usługi
        current_time = start_service + client.service_time
        current_load += client.demand
        prev_id = client_id

    # 6. Powrót do bazy
    dist_home = dist_matrix[prev_id][0]
    total_dist += dist_home
    arrival_at_depot = current_time + dist_home

    # Czy zdążyliśmy wrócić przed zamknięciem magazynu?
    if arrival_at_depot > depot.due_date:
        return False, 0.0, "Spóźniony powrót"

    return True, total_dist, "OK"

def optimize_route_2opt(route, clients, dist_matrix, capacity):
    """
    Próbuje ulepszyć pojedynczą trasę metodą 2-opt.
    Jeśli znajdzie lepsze ułożenie (krótsze i poprawne), zamienia trasę.
    """
    best_route = route[:]
    # Musimy obliczyć koszt obecnej trasy, żeby mieć punkt odniesienia
    # Używamy check_route z Kroku 3, które zwraca (valid, dist, msg)
    _, best_dist, _ = check_route(best_route, clients, dist_matrix, capacity)

    improved = True
    while improved:
        improved = False
        # Pętla po wszystkich krawędziach
        for i in range(len(best_route) - 1):
            for j in range(i + 1, len(best_route)):
                if j - i == 1: continue  # Nie zamieniamy sąsiadów, bo to nic nie zmienia

                # Tworzymy nową trasę: odwracamy fragment od i do j
                new_route = best_route[:i] + best_route[i:j + 1][::-1] + best_route[j + 1:]

                # SPRAWDZAMY CZY JEST LEPIEJ I CZY POPRAWNIE
                # 1. Czy jest szybciej? (Szybka wstępna ocena na podstawie macierzy)
                # Ale w VRPTW czas to nie tylko odległość, ale też czekanie.
                # Więc najlepiej od razu puścić pełną symulację check_route.

                valid, new_dist, _ = check_route(new_route, clients, dist_matrix, capacity)

                if valid and new_dist < best_dist - 0.01:  # 0.01 to margines błędu float
                    best_route = new_route
                    best_dist = new_dist
                    improved = True
                    break  # Jak znaleźliśmy poprawę, wracamy do początku while (First Improvement)
            if improved: break

    return best_route, best_dist


def run_genetic_algorithm(clients, dist_matrix, capacity):
    # --- PARAMETRY ---
    POPULATION_SIZE = 200  # Rozmiar populacji
    GENERATIONS = 300  # Liczba pokoleń (zmniejszyłem do 100, bo 2-opt trwa dłużej)
    TOURNAMENT_SIZE = 5  # Rozmiar turnieju
    MUTATION_RATE = 0.1  # Szansa na mutację

    # ID klientów (bez bazy 0)
    customer_ids = list(range(1, len(clients)))

    # 1. Inicjalizacja populacji (50 losowych rozwiązań)
    population = []
    for _ in range(POPULATION_SIZE):
        shuffled = customer_ids[:]
        shuffle(shuffled)
        population.append(shuffled)

    best_overall_genome = None
    best_overall_fitness = float('inf')
    best_vehicles_count = float('inf')
    best_distance_val = float('inf')

    print(f"\nSTART HYBRYDOWEGO GENETYKA (Max pokoleń: {GENERATIONS})")
    print("To może chwilę potrwać, bo 2-opt intensywnie liczy...")

    for gen in range(GENERATIONS):
        scored_population = []

        # --- OCENA POPULACJI (TUTAJ JEST ZMIANA) ---
        for genome in population:
            # A. Dekodowanie (dzielenie na pojazdy - wersja surowa)
            raw_routes, _ = calculate_routes(genome, clients, dist_matrix, capacity)

            # B. KROK HYBRYDYZACJI (Local Search / 2-opt)
            # Każdą surową trasę przepuszczamy przez optymalizator
            optimized_routes = []
            total_optimized_dist = 0.0

            for route in raw_routes:
                # Jeśli trasa jest bardzo krótka (np. 1-2 klientów), 2-opt nic nie da
                if len(route) > 2:
                    opt_route, opt_dist = optimize_route_2opt(route, clients, dist_matrix, capacity)
                    optimized_routes.append(opt_route)
                    total_optimized_dist += opt_dist
                else:
                    # Dla krótkich tras tylko liczymy dystans
                    _, d, _ = check_route(route, clients, dist_matrix, capacity)
                    optimized_routes.append(route)
                    total_optimized_dist += d

            # C. Obliczanie Fitness na podstawie ULEPSZONEGO rozwiązania
            num_vehicles = len(optimized_routes)
            fitness = calculate_fitness(num_vehicles, total_optimized_dist)

            # Zapisujemy wynik (UWAGA: Zapisujemy oryginalny genom, ale ocenę po optymalizacji)
            # To tzw. Ewolucja Baldwina - osobnik jest oceniany za swój potencjał do nauki (optymalizacji)
            scored_population.append((fitness, genome, num_vehicles, total_optimized_dist))

            # Sprawdzamy czy to rekord
            if fitness < best_overall_fitness:
                best_overall_fitness = fitness
                best_overall_genome = genome[:]  # Kopia genomu
                best_vehicles_count = num_vehicles
                best_distance_val = total_optimized_dist
                print(f"Gen {gen}: REKORD! Auta: {num_vehicles}, Dystans: {total_optimized_dist:.2f}")

        # --- SELEKCJA I NOWA POPULACJA (STANDARD GA) ---
        new_population = []

        # Elityzm: Przenosimy 2 najlepszych
        scored_population.sort(key=lambda x: x[0])  # Sortuj po fitness (rosnąco)
        new_population.append(scored_population[0][1])
        new_population.append(scored_population[1][1])

        while len(new_population) < POPULATION_SIZE:
            # Turniej dla Rodzica 1
            tournament = sample(scored_population, TOURNAMENT_SIZE)
            parent1 = min(tournament, key=lambda x: x[0])[1]

            # Turniej dla Rodzica 2
            tournament = sample(scored_population, TOURNAMENT_SIZE)
            parent2 = min(tournament, key=lambda x: x[0])[1]

            # Krzyżowanie
            child = crossover(parent1, parent2)

            # Mutacja
            if random() < MUTATION_RATE:
                child = mutate(child)

            new_population.append(child)

        population = new_population

    return best_overall_genome, best_vehicles_count


capacity, clients = load_data("data/c101.txt")

dist_matrix = create_distance_matrix(clients)

# 3. Uruchomienie GA
best_genome, best_vehicles = run_genetic_algorithm(clients, dist_matrix, capacity)

# 4. Wyświetlenie wyniku końcowego
print("\n--- KONIEC OBLICZEŃ ---")

# 1. Najpierw dekodujemy zwycięski genom na surowe trasy
raw_routes, _ = calculate_routes(best_genome, clients, dist_matrix, capacity)

# 2. Potem aplikujemy 2-opt (bo genom przechowuje tylko kolejność, a nie optymalizację lokalną)
final_routes = []
final_dist = 0.0
for r in raw_routes:
    opt_r, opt_d = optimize_route_2opt(r, clients, dist_matrix, capacity)
    final_routes.append(opt_r)
    final_dist += opt_d

print(f"Najlepszy wynik (z 2-opt):")
print(f"Liczba pojazdów: {len(final_routes)}")
print(f"Całkowity dystans: {final_dist:.2f}")

for i, route in enumerate(final_routes):
    print(f"Pojazd {i + 1}: {route}")