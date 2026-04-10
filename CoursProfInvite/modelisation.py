import matplotlib.pyplot as plt
import numpy as np
import random
from equation import biomass

# ------------------------------------------------------------
# Paramètres pour la satisfaction des bateaux pros
# ------------------------------------------------------------
SATISFACTION_WINDOW = 30          # fenêtre glissante (en ticks)
SATISFACTION_MAX_HARVEST = 2000   # biomasse nécessaire pour satisfaction = 10

# ------------------------------------------------------------
# Fonctions de base
# ------------------------------------------------------------
def init_grid(size=5, B_max_init=1000, seed=None):
    """Initialise une grille size x size avec des valeurs aléatoires."""
    if seed is not None:
        np.random.seed(seed)
    return np.random.uniform(0, B_max_init, (size, size))

def init_boats_v2(nb_pro, nb_loisir, size=5,
                  pro_percent=0.3, pro_max=200, pro_capacity=500,
                  loisir_percent=0.1, loisir_max=50):
    """
    Crée la liste des bateaux.
    Pour les pros : attributs : pos, type, percent, max_harvest, active, cooldown,
    cargo, capacity, recent_harvests, satisfaction.
    Pour les loisirs : pos, type, percent, max_harvest, active, cooldown.
    """
    boats = []
    for _ in range(nb_pro):
        boats.append({
            'pos': [random.randint(0, size-1), random.randint(0, size-1)],
            'type': 'pro',
            'percent': pro_percent,
            'max_harvest': pro_max,
            'active': True,
            'cooldown': 0,
            'cargo': 0.0,
            'capacity': pro_capacity,
            'recent_harvests': [],
            'satisfaction': 0.0
        })
    for _ in range(nb_loisir):
        boats.append({
            'pos': [random.randint(0, size-1), random.randint(0, size-1)],
            'type': 'loisir',
            'percent': loisir_percent,
            'max_harvest': loisir_max,
            'active': True,
            'cooldown': 0
        })
    return boats

def get_boats_pro(boats):
    """Retourne la liste des bateaux professionnels (sans les loisirs)."""
    return [boat for boat in boats if boat['type'] == 'pro']

def update_loisirs(boats_pro, nb_loisirs, grid_size, loisir_percent, loisir_max):
    """Recrée les bateaux loisirs avec des positions aléatoires et actifs."""
    new_boats = boats_pro.copy()
    for _ in range(nb_loisirs):
        new_boats.append({
            'pos': [random.randint(0, grid_size-1), random.randint(0, grid_size-1)],
            'type': 'loisir',
            'percent': loisir_percent,
            'max_harvest': loisir_max,
            'active': True,
            'cooldown': 0
        })
    return new_boats

def growth_step(grid, r, K):
    """Applique un pas de croissance logistique sur chaque cellule."""
    new_grid = grid.copy()
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            b = grid[i, j]
            new_grid[i, j] = b + biomass(b, K, r)
    return new_grid

def move_boat(pos, size=5):
    """Déplace aléatoirement un bateau (reste sur la grille)."""
    i, j = pos
    direction = random.randint(0, 4)  # 0=rester, 1=haut, 2=bas, 3=gauche, 4=droite
    if direction == 1 and i > 0:
        i -= 1
    elif direction == 2 and i < size-1:
        i += 1
    elif direction == 3 and j > 0:
        j -= 1
    elif direction == 4 and j < size-1:
        j += 1
    return [i, j]

def harvest_cell_percent(grid, pos, percent, max_harvest):
    """Retire un pourcentage (limité) de biomasse et retourne la quantité prélevée."""
    i, j = pos
    current = grid[i, j]
    harvest = min(current * percent, max_harvest)
    grid[i, j] = max(0, current - harvest)
    return harvest

def step_boats_and_harvest(boats, grid, grid_size=5):
    """
    Gère le déplacement, la pêche, l'inactivité et la satisfaction.
    Retourne (total_harvest_pro, total_harvest_loisir) pour ce pas de temps.
    """
    total_pro = 0.0
    total_loisir = 0.0

    for boat in boats:
        if not boat['active']:
            boat['cooldown'] -= 1
            if boat['cooldown'] <= 0:
                boat['active'] = True
                boat['pos'] = [random.randint(0, grid_size-1), random.randint(0, grid_size-1)]
                if boat['type'] == 'pro':
                    boat['cargo'] = 0.0
                    # On réinitialise l'historique des pêches pour ne pas fausser la satisfaction
                    boat['recent_harvests'] = []
                    boat['satisfaction'] = 0.0
            continue

        # Bateau actif : se déplace et pêche
        boat['pos'] = move_boat(boat['pos'], grid_size)
        harvested = harvest_cell_percent(grid, boat['pos'], boat['percent'], boat['max_harvest'])

        if boat['type'] == 'pro':
            total_pro += harvested
            boat['cargo'] += harvested
            # Mise à jour de l'historique glissant pour la satisfaction
            boat['recent_harvests'].append(harvested)
            if len(boat['recent_harvests']) > SATISFACTION_WINDOW:
                boat['recent_harvests'].pop(0)
            total_window = sum(boat['recent_harvests'])
            sat = (total_window / SATISFACTION_MAX_HARVEST) * 10.0
            boat['satisfaction'] = min(10.0, sat)

            if boat['cargo'] >= boat['capacity']:
                boat['active'] = False
                boat['cooldown'] = random.randint(2, 5)
                boat['pos'] = None
                boat['cargo'] = 0.0
                # On conserve l'historique des pêches pour la satisfaction (il continuera après réactivation)
        else:  # loisir
            total_loisir += harvested
            boat['active'] = False
            boat['cooldown'] = random.randint(2, 7)
            boat['pos'] = None

    return total_pro, total_loisir

def update_plot(ax1, ax2, grid, boats, total_biomass, ticks, history,
                total_harvest_pro, total_harvest_loisir, satisfaction_history,
                K, pause_time=0.01):
    """
    Met à jour l'affichage : heatmap + bateaux + courbe biomasse + courbe satisfaction.
    """
    ax1.clear()
    ax1.imshow(grid, cmap='viridis', vmin=0, vmax=K)
    nb_pro = sum(1 for b in boats if b['type'] == 'pro' and b['active'])
    nb_loisir = sum(1 for b in boats if b['type'] == 'loisir' and b['active'])
    ax1.set_title(f"Biomasse totale = {total_biomass:.1f}\n"
                  f"Pro actifs: {nb_pro} (cumul pêche: {total_harvest_pro:.0f}) | "
                  f"Loisir actifs: {nb_loisir} (cumul pêche: {total_harvest_loisir:.0f})")
    ax1.set_xticks(np.arange(grid.shape[1]))
    ax1.set_yticks(np.arange(grid.shape[0]))
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            ax1.text(j, i, f"{grid[i, j]:.1f}", ha='center', va='center',
                     color='white', fontsize=8)
    for idx, boat in enumerate(boats):
        if not boat['active']:
            continue
        i, j = boat['pos']
        if boat['type'] == 'pro':
            ax1.plot(j, i, 'rs', markersize=12, markeredgecolor='white')
            ax1.text(j, i, str(idx+1), ha='center', va='center',
                     color='white', fontsize=8, fontweight='bold')
        else:
            ax1.plot(j, i, 'y^', markersize=12, markeredgecolor='black')
            ax1.text(j, i, str(idx+1), ha='center', va='center',
                     color='black', fontsize=8, fontweight='bold')

    # Sous-figure du bas : biomasse totale (axe gauche) et satisfaction (axe droit)
    ax2.clear()
    ax2.plot(ticks, history, 'b-', linewidth=2, label='Biomasse totale')
    ax2.set_xlabel('Temps')
    ax2.set_ylabel('Biomasse totale', color='b')
    ax2.tick_params(axis='y', labelcolor='b')
    ax2.grid(True)

    ax2_twin = ax2.twinx()
    ax2_twin.plot(ticks, satisfaction_history, 'r--', linewidth=1.5, label='Satisfaction pro (moy.)')
    ax2_twin.set_ylabel('Satisfaction (0-10)', color='r')
    ax2_twin.tick_params(axis='y', labelcolor='r')
    ax2_twin.set_ylim(0, 10)

    plt.pause(pause_time)

# À ajouter dans modelisation.py (après les autres fonctions)

def run_simulation_simple(params, seed=None):
    """
    Exécute une simulation complète avec les paramètres donnés.
    params doit contenir toutes les clés nécessaires, y compris:
        t_max, grid_size, B_init, nb_pro, nb_loisir, pro_max, loisir_max,
        pro_cooldown_min, loisir_cooldown_min, et tous les paramètres variables.
    Retourne la biomasse totale finale (float).
    """
    if seed is not None:
        random.seed(int(seed))
        np.random.seed(int(seed))

    t_max = params['t_max']
    grid_size = params['grid_size']
    B_init = params['B_init']

    grid = init_grid(size=grid_size, B_max_init=B_init, seed=seed)

    # Création des bateaux
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