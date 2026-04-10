import numpy as np
import random
import matplotlib.pyplot as plt
from modelisation import init_grid, growth_step
import itertools

# ------------------------------------------------------------
# Simulation unique sans affichage (version complète)
# ------------------------------------------------------------
def run_simulation_no_plot(params, t_max=1000, grid_size=10, B_init=200, random_seed=None):
    if random_seed is not None:
        random.seed(random_seed)
        np.random.seed(random_seed)

    grid = init_grid(size=grid_size, B_max_init=B_init, seed=random_seed)

    # Bateaux professionnels
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

    # Bateaux loisirs
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
            'active_days_total': params['loisir_active_days'],   # période de pêche
            'active_days_left': params['loisir_active_days']     # jours restants dans la période active
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
                    else:  # loisir
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
            else:  # loisir
                boat['cargo'] += harvest
                boat['active_days_left'] -= 1
                # Vérifier si capacité atteinte ou fin de période active
                if boat['cargo'] >= boat['capacity'] or boat['active_days_left'] == 0:
                    boat['active'] = False
                    boat['cooldown'] = random.randint(boat['cooldown_min'], boat['cooldown_max'])
                    boat['pos'] = None
                    boat['cargo'] = 0.0

    return np.sum(grid)


# ------------------------------------------------------------
# Plan factoriel à 3 niveaux (sous-intervalles)
# ------------------------------------------------------------
def main():
    t_max = 365
    grid_size = 10
    B_init = 2000
    nb_pro_fixed = 10
    nb_loisir_fixed = 50

    # Paramètres fixes (non variables)
    pro_max = 200           # max prélèvement pro (pas d'intervalle donné)
    loisir_max = 10         # max prélèvement loisir
    pro_cooldown_min = 2    # repos min pro
    loisir_cooldown_min = 4 # repos min loisir

    # Intervalles complets pour chaque paramètre variable
    intervals = {
        'r': (0.01, 0.4),
        'K': (800, 1400),
        'pro_percent': (0.1, 0.3),
        'pro_capacity': (4000, 6000),
        'loisir_percent': (0.01, 0.05),
        'loisir_capacity': (500, 1000),
        'pro_cooldown_max': (2, 7),        # repos max pro
        'loisir_cooldown_max': (4, 15),    # repos max loisir
        'loisir_active_days': (2, 6)       # période de pêche des loisirs
    }

    # Découpage en 3 sous-intervalles pour chaque paramètre
    tiers = {}
    for param, (low, high) in intervals.items():
        step = (high - low) / 3.0
        tiers[param] = [
            (low, low + step),
            (low + step, low + 2*step),
            (low + 2*step, high)
        ]

    # Toutes les combinaisons de choix de tiers (3^9)
    param_names = list(intervals.keys())
    # Chaque combinaison est un tuple d'indices (0,1,2) pour chaque paramètre
    all_combinations = list(itertools.product([0,1,2], repeat=len(param_names)))

    final_biomasses = []   # stocke toutes les biomasses finales (3 répétitions par combinaison)

    for combo_index, tier_choice in enumerate(all_combinations):
        # tier_choice = (indice pour param1, indice pour param2, ...)
        # On tire 3 fois aléatoirement dans chaque sous-intervalle
        for rep in range(3):
            params = {}
            for i, param in enumerate(param_names):
                low, high = tiers[param][tier_choice[i]]
                # Tirage uniforme dans le sous-intervalle
                val = random.uniform(low, high)
                # Les cooldown_max doivent être des entiers (arrondis)
                if 'cooldown_max' in param:
                    val = int(round(val))
                params[param] = val
            # Ajout des paramètres fixes
            params.update({
                'nb_pro': nb_pro_fixed,
                'nb_loisir': nb_loisir_fixed,
                'pro_max': pro_max,
                'loisir_max': loisir_max,
                'pro_cooldown_min': pro_cooldown_min,
                'loisir_cooldown_min': loisir_cooldown_min
            })

            biomass_end = run_simulation_no_plot(params, t_max, grid_size, B_init, random_seed=42+combo_index*3+rep)
            final_biomasses.append(biomass_end)

        if (combo_index+1) % 100 == 0:
            print(f"Combinaison {combo_index+1}/{len(all_combinations)} - 3 répétitions effectuées")

    # Histogramme final
    plt.figure(figsize=(10, 6))
    plt.hist(final_biomasses, bins=20, edgecolor='black', alpha=0.7)
    plt.xlabel('Biomasse totale finale')
    plt.ylabel('Fréquence')
    plt.title(f'Histogramme sur {len(final_biomasses)} simulations (plan factoriel 3^9 × 3 répétitions)')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.show()

    print(f"Biomasse moyenne : {np.mean(final_biomasses):.1f}")
    print(f"Écart-type : {np.std(final_biomasses):.1f}")
    print(f"Minimum : {np.min(final_biomasses):.1f}")
    print(f"Maximum : {np.max(final_biomasses):.1f}")


if __name__ == "__main__":
    main()