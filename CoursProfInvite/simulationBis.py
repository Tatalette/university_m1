import numpy as np
import random
import matplotlib.pyplot as plt
from modelisation import init_grid, growth_step
import itertools

# ------------------------------------------------------------
# Simulation unique sans affichage
# ------------------------------------------------------------
def run_simulation_no_plot(params, t_max=365, grid_size=10, B_init=200, random_seed=42):
    """Exécute une simulation avec des paramètres donnés, sans affichage."""
    random.seed(random_seed)
    np.random.seed(random_seed)

    grid = init_grid(size=grid_size, B_max_init=B_init, seed=random_seed)

    # Création des bateaux
    boats = []
    for _ in range(params['nb_pro']):
        boats.append({
            'pos': [random.randint(0, grid_size-1), random.randint(0, grid_size-1)],
            'type': 'pro',
            'percent': params['pro_percent'],
            'max_harvest': params['pro_max'],
            'active': True,
            'cooldown': 0,
            'cargo': 0.0,
            'capacity': params['pro_capacity'],
            'cooldown_min': params['pro_cooldown_min'],
            'cooldown_max': params['pro_cooldown_max']
        })
    for _ in range(params['nb_loisir']):
        boats.append({
            'pos': [random.randint(0, grid_size-1), random.randint(0, grid_size-1)],
            'type': 'loisir',
            'percent': params['loisir_percent'],
            'max_harvest': params['loisir_max'],
            'active': True,
            'cooldown': 0,
            'cooldown_min': params['loisir_cooldown_min'],
            'cooldown_max': params['loisir_cooldown_max']
        })

    for _ in range(t_max):
        # Croissance
        grid = growth_step(grid, params['r'], params['K'])

        for boat in boats:
            if not boat['active']:
                boat['cooldown'] -= 1
                if boat['cooldown'] <= 0:
                    boat['active'] = True
                    boat['pos'] = [random.randint(0, grid_size-1), random.randint(0, grid_size-1)]
                    if boat['type'] == 'pro':
                        boat['cargo'] = 0.0
                continue

            # Déplacement aléatoire
            i, j = boat['pos']
            direction = random.randint(0, 4)
            if direction == 1 and i > 0:
                i -= 1
            elif direction == 2 and i < grid_size-1:
                i += 1
            elif direction == 3 and j > 0:
                j -= 1
            elif direction == 4 and j < grid_size-1:
                j += 1
            boat['pos'] = [i, j]

            # Pêche
            current = grid[i, j]
            harvest = min(current * boat['percent'], boat['max_harvest'])
            grid[i, j] = max(0, current - harvest)

            if boat['type'] == 'pro':
                boat['cargo'] += harvest
                if boat['cargo'] >= boat['capacity']:
                    boat['active'] = False
                    boat['cooldown'] = random.randint(boat['cooldown_min'], boat['cooldown_max'])
                    boat['pos'] = None
                    boat['cargo'] = 0.0
            else:  # loisir
                boat['active'] = False
                boat['cooldown'] = random.randint(boat['cooldown_min'], boat['cooldown_max'])
                boat['pos'] = None

    return np.sum(grid)


# ------------------------------------------------------------
# Plan factoriel complet à 3 niveaux
# ------------------------------------------------------------
def main():
    t_max = 365
    grid_size = 10
    B_init = 200
    nb_pro_fixed = 10
    nb_loisir_fixed = 50

    # Paramètres fixes
    pro_max = 200
    loisir_max = 10
    pro_cooldown_min = 2
    loisir_cooldown_min = 4

    # Paramètres variables : (valeur basse, moyenne, haute)
    param_levels = {
        'r': (0.01, 0.205, 0.4),
        'K': (800, 1100, 1400),
        'pro_percent': (0.1, 0.2, 0.3),
        'pro_capacity': (4000, 5000, 6000),
        'loisir_percent': (0.01, 0.03, 0.05),
        'pro_cooldown_max': (2, 4, 7),
        'loisir_cooldown_max': (4, 9, 15),
    }

    # Génération de toutes les combinaisons (3^7 = 2187)
    keys = list(param_levels.keys())
    values = [param_levels[k] for k in keys]
    combos = list(itertools.product(*values))

    final_biomasses = []

    for idx, combo in enumerate(combos, 1):
        params = dict(zip(keys, combo))
        # Ajout des paramètres fixes
        params.update({
            'nb_pro': nb_pro_fixed,
            'nb_loisir': nb_loisir_fixed,
            'pro_max': pro_max,
            'loisir_max': loisir_max,
            'pro_cooldown_min': pro_cooldown_min,
            'loisir_cooldown_min': loisir_cooldown_min
        })

        biomass_end = run_simulation_no_plot(params, t_max, grid_size, B_init, random_seed=42)
        final_biomasses.append(biomass_end)

        if idx % 100 == 0:
            print(f"Combinaison {idx}/{len(combos)} terminée")

    # Histogramme des biomasses finales
    plt.figure(figsize=(10, 6))
    plt.hist(final_biomasses, bins=20, edgecolor='black', alpha=0.7)
    plt.xlabel('Biomasse totale finale')
    plt.ylabel('Fréquence')
    plt.title(f'Histogramme sur {len(combos)} combinaisons (3 niveaux par paramètre)')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.show()

    print(f"Biomasse moyenne : {np.mean(final_biomasses):.1f}")
    print(f"Écart-type : {np.std(final_biomasses):.1f}")
    print(f"Minimum : {np.min(final_biomasses):.1f}")
    print(f"Maximum : {np.max(final_biomasses):.1f}")


if __name__ == "__main__":
    main()