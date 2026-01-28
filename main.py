import math

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



capacity, clients = load_data("data/c101.txt")

dist_matrix = create_distance_matrix(clients)

depot = clients[0]
cust1 = clients[1]

print(f"\nDepot: ({depot.x}, {depot.y})")
print(f"Klient 1: ({cust1.x}, {cust1.y})")

calculated = dist_matrix[0][1]
print(f"Odległość w macierzy: {calculated:.2f}")
