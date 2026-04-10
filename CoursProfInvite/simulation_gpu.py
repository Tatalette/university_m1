import cupy as cp
import random
import matplotlib.pyplot as plt
import itertools
from modelisation_gpu import (
    init_grid, growth_step, step_boats_and_harvest_gpu,
    init_boats_v2, get_boats_pro, update_loisirs
)

def run_simulation_no_plot_gpu(params, t_max=1000, grid_size=10, B_init=200, random_seed=None):
    if random_seed is not None:
        random.seed(random_seed)
        cp.random.seed(random_seed)

    grid = init_grid(grid_size, B_init, seed=random_seed)

    # Création des bateaux
    boats = init_boats_v2(
        params['nb_pro'], params['nb_loisir'],
        size=grid_size,
        pro_percent=params['pro_percent'],
        pro_max=params['pro_max'],
        pro_capacity=params['pro_capacity'],
        loisir_percent=params['loisir_percent'],
        loisir_max=params['loisir_max'],
        loisir_capacity=params['loisir_capacity'],
        pro_cooldown_min=params['pro_cooldown_min'],
        pro_cooldown_max=params['pro_cooldown_max'],
        loisir_cooldown_min=params['loisir_cooldown_min'],
        loisir_cooldown_max=params['loisir_cooldown_max'],
        loisir_active_days=params['loisir_active_days']
    )

    for _ in range(t_max):
        grid = growth_step(grid, params['r'], params['K'])
        step_boats_and_harvest_gpu(boats, grid, grid_size)

    total_biomass = float(cp.sum(grid).get())
    return total_biomass

def main():
    t_max = 1000
    grid_size = 10
    B_init = 200
    nb_pro_fixed = 10
    nb_loisir_fixed = 50

    # Paramètres fixes
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

    # Découpage en 3 sous-intervalles égaux
    tiers = {}
    for param, (low, high) in intervals.items():
        step = (high - low) / 3.0
        tiers[param] = [
            (low, low + step),
            (low + step, low + 2*step),
            (low + 2*step, high)
        ]

    param_names = list(intervals.keys())
    all_combinations = list(itertools.product([0,1,2], repeat=len(param_names)))

    final_biomasses = []

    for combo_index, tier_choice in enumerate(all_combinations):
        for rep in range(3):  # 3 répétitions par combinaison
            params = {}
            for i, param in enumerate(param_names):
                low, high = tiers[param][tier_choice[i]]
                val = random.uniform(low, high)
                if 'cooldown_max' in param or 'active_days' in param:
                    val = int(round(val))
                params[param] = val
            params.update({
                'nb_pro': nb_pro_fixed,
                'nb_loisir': nb_loisir_fixed,
                'pro_max': pro_max,
                'loisir_max': loisir_max,
                'pro_cooldown_min': pro_cooldown_min,
                'loisir_cooldown_min': loisir_cooldown_min
            })

            biomass_end = run_simulation_no_plot_gpu(params, t_max, grid_size, B_init, random_seed=42+combo_index*3+rep)
            final_biomasses.append(biomass_end)

        if (combo_index+1) % 100 == 0:
            print(f"Combinaison {combo_index+1}/{len(all_combinations)} - 3 répétitions effectuées")

    # Histogramme
    plt.figure(figsize=(10,6))
    plt.hist(final_biomasses, bins=20, edgecolor='black', alpha=0.7)
    plt.xlabel('Biomasse totale finale')
    plt.ylabel('Fréquence')
    plt.title(f'GPU – {len(final_biomasses)} simulations (3^9 × 3 répétitions)')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.show()

    print(f"Biomasse moyenne : {np.mean(final_biomasses):.1f}")
    print(f"Écart-type : {np.std(final_biomasses):.1f}")
    print(f"Min : {np.min(final_biomasses):.1f} / Max : {np.max(final_biomasses):.1f}")

if __name__ == "__main__":
    main()