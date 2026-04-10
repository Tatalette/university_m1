import numpy as np
import random
import matplotlib.pyplot as plt
import itertools
import multiprocessing as mp
from functools import partial
from modelisation import init_grid, growth_step   # vos fonctions CPU d'origine (sans GPU)

# ------------------------------------------------------------
# Simulation unique (identique à avant, mais sans GPU)
# ------------------------------------------------------------
def run_one_simulation(params, t_max=1000, grid_size=10, B_init=200, seed=None):
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    grid = init_grid(size=grid_size, B_max_init=B_init, seed=seed)

    # Création des bateaux (identique à votre version CPU)
    boats = []
    # Pros
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
    # Loisirs
    for _ in range(params['nb_loisir']):
        boats.append({
            'pos': [random.randint(0, grid_size-1), random.randint(0, grid_size-1)],
            'type': 'loisir',
            'percent': params['loisir_percent'],
            'max_harvest': params['loisir_max'],
            'active': True,
            'cooldown': 0,
            'cargo': 0.0,
            'capacity': params['loisir_capacity'],
            'cooldown_min': params['loisir_cooldown_min'],
            'cooldown_max': params['loisir_cooldown_max'],
            'active_days_total': params['loisir_active_days'],
            'active_days_left': params['loisir_active_days']
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
                    else:
                        boat['cargo'] = 0.0
                        boat['active_days_left'] = boat['active_days_total']
                continue

            # Déplacement
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
            else:
                boat['cargo'] += harvest
                boat['active_days_left'] -= 1
                if boat['cargo'] >= boat['capacity'] or boat['active_days_left'] == 0:
                    boat['active'] = False
                    boat['cooldown'] = random.randint(boat['cooldown_min'], boat['cooldown_max'])
                    boat['pos'] = None
                    boat['cargo'] = 0.0

    return float(np.sum(grid))


# ------------------------------------------------------------
# Gestion du parallélisme
# ------------------------------------------------------------
def worker(args):
    """Fonction appelée par chaque processus : (combo_index, rep, t_max, grid_size, B_init, fixed_params, tiers, param_names)"""
    combo_index, rep, t_max, grid_size, B_init, fixed_params, tiers, param_names = args
    tier_choice = combo_index   # ici combo_index est le tuple d'indices (0,1,2) pour chaque param
    params = {}
    for i, param in enumerate(param_names):
        low, high = tiers[param][tier_choice[i]]
        val = random.uniform(low, high)
        if 'cooldown_max' in param or 'active_days' in param:
            val = int(round(val))
        params[param] = val
    params.update(fixed_params)
    seed = 42 + combo_index[0]*3 + rep  # hash simple
    return run_one_simulation(params, t_max, grid_size, B_init, seed)


def main():
    t_max = 1000
    grid_size = 10
    B_init = 200
    nb_pro_fixed = 10
    nb_loisir_fixed = 50
    pro_max = 200
    loisir_max = 10
    pro_cooldown_min = 2
    loisir_cooldown_min = 4

    # Intervalles complets
    intervals = {
        'r': (0.01, 0.4),
        'K': (800, 1400),
        'pro_percent': (0.1, 0.3),
        'pro_capacity': (4000, 6000),
        'loisir_percent': (0.01, 0.05),
        'loisir_capacity': (500, 1000),
        'pro_cooldown_max': (2, 7),
        'loisir_cooldown_max': (4, 15),
        'loisir_active_days': (2, 6)
    }

    # Découpage en 3 sous-intervalles
    tiers = {}
    for param, (low, high) in intervals.items():
        step = (high - low) / 3.0
        tiers[param] = [
            (low, low + step),
            (low + step, low + 2*step),
            (low + 2*step, high)
        ]

    param_names = list(intervals.keys())
    all_combinations = list(itertools.product([0,1,2], repeat=len(param_names)))   # 3^9 = 19683
    print(f"Nombre total de combinaisons : {len(all_combinations)}")

    # Préparer les arguments pour chaque tâche : (combo_tuple, rep, t_max, grid_size, B_init, fixed_params, tiers, param_names)
    fixed_params = {
        'nb_pro': nb_pro_fixed,
        'nb_loisir': nb_loisir_fixed,
        'pro_max': pro_max,
        'loisir_max': loisir_max,
        'pro_cooldown_min': pro_cooldown_min,
        'loisir_cooldown_min': loisir_cooldown_min
    }
    tasks = []
    for combo_tuple in all_combinations:
        for rep in range(3):
            tasks.append((combo_tuple, rep, t_max, grid_size, B_init, fixed_params, tiers, param_names))

    print(f"Nombre total de simulations : {len(tasks)}")
    # Lancer en parallèle (utilise tous les cœurs)
    with mp.Pool() as pool:
        results = pool.map(worker, tasks)

    final_biomasses = results

    # Histogramme
    plt.figure(figsize=(10,6))
    plt.hist(final_biomasses, bins=20, edgecolor='black', alpha=0.7)
    plt.xlabel('Biomasse totale finale')
    plt.ylabel('Fréquence')
    plt.title(f'Parallélisme CPU – {len(final_biomasses)} simulations')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.show()

    print(f"Biomasse moyenne : {np.mean(final_biomasses):.1f}")
    print(f"Écart-type : {np.std(final_biomasses):.1f}")
    print(f"Min : {np.min(final_biomasses):.1f} / Max : {np.max(final_biomasses):.1f}")

if __name__ == "__main__":
    main()