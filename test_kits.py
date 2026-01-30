# WARTOŚCI BAZOWE
BASE_POP = 50          # liczba osobników
BASE_GEN = 1000       # liczba pokoleń
BASE_TOURN = 5         # wielkość turnieju
BASE_MUT = 0.05        # prawdopodobieństwo mutacji

EXPERIMENTS_GA = [
    # --- GRUPA 1: zmienna populacja ---
    {"population_size": 20,  "generations": BASE_GEN, "tournament_size": BASE_TOURN, "mutation_rate": BASE_MUT},
    {"population_size": BASE_POP, "generations": BASE_GEN, "tournament_size": BASE_TOURN, "mutation_rate": BASE_MUT},
    {"population_size": 100, "generations": BASE_GEN, "tournament_size": BASE_TOURN, "mutation_rate": BASE_MUT},
    {"population_size": 200, "generations": BASE_GEN, "tournament_size": BASE_TOURN, "mutation_rate": BASE_MUT},

    # --- GRUPA 2: zmienne prawdopodobieństwo mutacji ---
    {"population_size": BASE_POP, "generations": BASE_GEN, "tournament_size": BASE_TOURN, "mutation_rate": 0.0},
    {"population_size": BASE_POP, "generations": BASE_GEN, "tournament_size": BASE_TOURN, "mutation_rate": 0.1},
    {"population_size": BASE_POP, "generations": BASE_GEN, "tournament_size": BASE_TOURN, "mutation_rate": 0.2},

    # --- GRUPA 3: zmienna wielkość turnieju ---
    {"population_size": BASE_POP, "generations": BASE_GEN, "tournament_size": 2, "mutation_rate": BASE_MUT},
    {"population_size": BASE_POP, "generations": BASE_GEN, "tournament_size": 5, "mutation_rate": BASE_MUT},
    {"population_size": BASE_POP, "generations": BASE_GEN, "tournament_size": 10, "mutation_rate": BASE_MUT},

    # --- GRUPA 4: zmienna liczba pokoleń ---
    {"population_size": BASE_POP, "generations": 100, "tournament_size": BASE_TOURN, "mutation_rate": BASE_MUT},
    {"population_size": BASE_POP, "generations": 500, "tournament_size": BASE_TOURN, "mutation_rate": BASE_MUT},
    {"population_size": BASE_POP, "generations": 10000, "tournament_size": BASE_TOURN, "mutation_rate": BASE_MUT},
]
