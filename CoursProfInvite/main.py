import argparse
import matplotlib.pyplot as plt
import numpy as np
import modelisation as md

def run_simulation(args):
    # Initialisation de la grille
    grid = md.init_grid(args.grid_size, args.B_max_init, seed=args.random_seed)
    # Initialisation des bateaux (avec le premier nombre de loisirs)
    boats = md.init_boats_v2(
        args.nb_pro, args.nb_loisir_1,
        size=args.grid_size,
        pro_percent=args.pro_percent,
        pro_max=args.pro_max,
        pro_capacity=args.pro_capacity,
        loisir_percent=args.loisir_percent,
        loisir_max=args.loisir_max
    )
    # Sauvegarde des pros (pour pouvoir les réutiliser lors des alternances)
    boats_pro = md.get_boats_pro(boats)

    ticks = []
    total_history = []
    satisfaction_history = []
    total_harvest_pro_cumul = 0.0
    total_harvest_loisir_cumul = 0.0

    # Configuration de l'affichage interactif
    plt.ion()
    fig = plt.figure(figsize=(10, 8))
    ax1 = plt.subplot(2, 1, 1)
    ax2 = plt.subplot(2, 1, 2)

    # Gestion de l'alternance du nombre de loisirs
    current_nb_loisirs = args.nb_loisir_1
    phase = 0  # 0 = phase avec nb_loisir_1, 1 = avec nb_loisir_2
    next_change = args.alternance_period

    for tick in range(1, args.t_max + 1):
        ticks.append(tick)

        # Alternance du nombre de bateaux de loisir
        if tick >= next_change:
            if phase == 0:
                current_nb_loisirs = args.nb_loisir_2
                phase = 1
            else:
                current_nb_loisirs = args.nb_loisir_1
                phase = 0
            # Reconstruire les bateaux : on garde les pros (avec leur état actuel) et on crée de nouveaux loisirs
            boats = md.update_loisirs(boats_pro, current_nb_loisirs, args.grid_size,
                                      args.loisir_percent, args.loisir_max)
            next_change += args.alternance_period

        # Croissance de la biomasse
        grid = md.growth_step(grid, args.r, args.K)

        # Déplacement, pêche, et mise à jour des états (retourne les quantités pêchées ce tick)
        harvest_pro, harvest_loisir = md.step_boats_and_harvest(boats, grid, args.grid_size)
        total_harvest_pro_cumul += harvest_pro
        total_harvest_loisir_cumul += harvest_loisir

        # Calcul de la satisfaction moyenne des pros
        pro_boats = [b for b in boats if b['type'] == 'pro']
        if pro_boats:
            avg_sat = sum(b['satisfaction'] for b in pro_boats) / len(pro_boats)
        else:
            avg_sat = 0.0
        satisfaction_history.append(avg_sat)

        total = np.sum(grid)
        total_history.append(total)

        # Mise à jour de l'affichage
        md.update_plot(ax1, ax2, grid, boats, total, ticks, total_history,
                       total_harvest_pro_cumul, total_harvest_loisir_cumul,
                       satisfaction_history, args.K, args.pause_time)

    plt.ioff()
    plt.show()
    return ticks, total_history, grid, boats, total_harvest_pro_cumul, total_harvest_loisir_cumul

def parse_args():
    parser = argparse.ArgumentParser(description="Simulation biomasse avec deux types de bateaux, alternance et cycles d'activité")
    parser.add_argument("--r", type=float, default=0.2)
    parser.add_argument("--K", type=float, default=1200)
    parser.add_argument("--B_max_init", type=float, default=200)
    parser.add_argument("--t_max", type=int, default=360)
    parser.add_argument("--grid_size", type=int, default=5)
    parser.add_argument("--random_seed", type=int, default=42)
    parser.add_argument("--pause_time", type=float, default=0.01)

    parser.add_argument("--nb_pro", type=int, default=3)
    parser.add_argument("--pro_percent", type=float, default=0.3)
    parser.add_argument("--pro_max", type=float, default=200)
    parser.add_argument("--pro_capacity", type=float, default=500)

    parser.add_argument("--nb_loisir_1", type=int, default=2)
    parser.add_argument("--nb_loisir_2", type=int, default=5)
    parser.add_argument("--alternance_period", type=int, default=180)
    parser.add_argument("--loisir_percent", type=float, default=0.1)
    parser.add_argument("--loisir_max", type=float, default=50)

    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    run_simulation(args)