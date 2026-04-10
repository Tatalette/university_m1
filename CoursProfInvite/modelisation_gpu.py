import cupy as cp
import random
from equation import biomass   # pour la croissance (mais on va la réécrire vectorisée)

def init_grid(size=5, B_max_init=200, seed=None):
    """Initialise une grille sur GPU avec des valeurs aléatoires."""
    if seed is not None:
        cp.random.seed(seed)
    return cp.random.uniform(0, B_max_init, (size, size))

def growth_step(grid, r, K):
    """
    Applique un pas de croissance logistique sur toute la grille (vectorisé GPU).
    grid : array GPU
    """
    # Formule : B + r * B * (1 - B/K)
    return grid + r * grid * (1 - grid / K)

def harvest_cell_gpu(grid, pos, percent, max_harvest):
    """
    Retire un pourcentage (limité) à une cellule.
    grid : array GPU (modifié sur place)
    pos : [i, j] en CPU
    Retourne la quantité prélevée (float CPU)
    """
    i, j = pos
    current = float(grid[i, j])          # transfert GPU -> CPU
    harvest = min(current * percent, max_harvest)
    new_val = max(0, current - harvest)
    grid[i, j] = new_val                 # assignation GPU
    return harvest

# Les fonctions de création de bateaux restent identiques (CPU)
def init_boats_v2(nb_pro, nb_loisir, size=5,
                  pro_percent=0.3, pro_max=200, pro_capacity=500,
                  loisir_percent=0.1, loisir_max=50,
                  pro_cooldown_min=2, pro_cooldown_max=7,
                  loisir_cooldown_min=4, loisir_cooldown_max=15,
                  loisir_active_days=3):
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
            'cooldown_min': pro_cooldown_min,
            'cooldown_max': pro_cooldown_max
        })
    for _ in range(nb_loisir):
        boats.append({
            'pos': [random.randint(0, size-1), random.randint(0, size-1)],
            'type': 'loisir',
            'percent': loisir_percent,
            'max_harvest': loisir_max,
            'active': True,
            'cooldown': 0,
            'cargo': 0.0,
            'capacity': loisir_capacity,
            'cooldown_min': loisir_cooldown_min,
            'cooldown_max': loisir_cooldown_max,
            'active_days_total': loisir_active_days,
            'active_days_left': loisir_active_days
        })
    return boats

def get_boats_pro(boats):
    return [b for b in boats if b['type'] == 'pro']

def update_loisirs(boats_pro, nb_loisirs, grid_size, loisir_percent, loisir_max,
                   loisir_capacity, loisir_cooldown_min, loisir_cooldown_max,
                   loisir_active_days):
    new_boats = boats_pro.copy()
    for _ in range(nb_loisirs):
        new_boats.append({
            'pos': [random.randint(0, grid_size-1), random.randint(0, grid_size-1)],
            'type': 'loisir',
            'percent': loisir_percent,
            'max_harvest': loisir_max,
            'active': True,
            'cooldown': 0,
            'cargo': 0.0,
            'capacity': loisir_capacity,
            'cooldown_min': loisir_cooldown_min,
            'cooldown_max': loisir_cooldown_max,
            'active_days_total': loisir_active_days,
            'active_days_left': loisir_active_days
        })
    return new_boats

def step_boats_and_harvest_gpu(boats, grid, grid_size=5):
    """
    Version GPU : déplace les bateaux, pêche avec harvest_cell_gpu.
    Retourne (total_pro, total_loisir) pour ce pas.
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

        # Pêche avec GPU
        harvested = harvest_cell_gpu(grid, [i, j], boat['percent'], boat['max_harvest'])

        if boat['type'] == 'pro':
            total_pro += harvested
            boat['cargo'] += harvested
            if boat['cargo'] >= boat['capacity']:
                boat['active'] = False
                boat['cooldown'] = random.randint(boat['cooldown_min'], boat['cooldown_max'])
                boat['pos'] = None
                boat['cargo'] = 0.0
        else:  # loisir
            total_loisir += harvested
            boat['cargo'] += harvested
            boat['active_days_left'] -= 1
            if boat['cargo'] >= boat['capacity'] or boat['active_days_left'] == 0:
                boat['active'] = False
                boat['cooldown'] = random.randint(boat['cooldown_min'], boat['cooldown_max'])
                boat['pos'] = None
                boat['cargo'] = 0.0
    return total_pro, total_loisir