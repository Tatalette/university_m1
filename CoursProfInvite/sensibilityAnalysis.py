import numpy as np
import random
import matplotlib.pyplot as plt
from modelisation import run_simulation_simple

# Paramètres fixes de la simulation
FIXED_PARAMS = {
    't_max': 1000,
    'grid_size': 10,
    'B_init': 200,
    'nb_pro': 10,
    'nb_loisir': 50,
    'pro_max': 200,
    'loisir_max': 10,
    'pro_cooldown_min': 2,
    'loisir_cooldown_min': 4
}

# Intervalles des paramètres à analyser (min, max)
PARAM_BOUNDS = {
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

P = 4  # nombre de niveaux

def run_simulation_from_normalized(x_norm, param_names, fixed_params, seed):
    params = fixed_params.copy()
    for i, name in enumerate(param_names):
        low, high = PARAM_BOUNDS[name]
        val = low + x_norm[i] * (high - low)
        if name in ['pro_cooldown_max', 'loisir_cooldown_max', 'loisir_active_days']:
            val = int(round(val))
        params[name] = val
    return run_simulation_simple(params, seed=seed)

def morris_screening(n_trajectories=100, random_seed=42):
    random.seed(random_seed)
    np.random.seed(random_seed)

    param_names = list(PARAM_BOUNDS.keys())
    k = len(param_names)
    delta = P / (2 * (P - 1))

    all_ees = {p: [] for p in param_names}

    for traj in range(n_trajectories):
        x_star = np.random.uniform(0, 1, k)
        order = np.random.permutation(k)

        x_base = x_star.copy()
        outputs = []
        y0 = run_simulation_from_normalized(x_base, param_names, FIXED_PARAMS, seed=traj*100 + 0)
        outputs.append(y0)

        current = x_base.copy()
        for idx in order:
            new_point = current.copy()
            new_point[idx] += delta
            if new_point[idx] > 1:
                new_point[idx] -= delta
            y_new = run_simulation_from_normalized(new_point, param_names, FIXED_PARAMS, seed=traj*100 + idx+1)
            ee = (y_new - outputs[-1]) / delta
            all_ees[param_names[idx]].append(ee)
            current = new_point.copy()
            outputs.append(y_new)

    results = {}
    for p in param_names:
        ees = np.array(all_ees[p])
        results[p] = {
            'mean': np.mean(ees),
            'std': np.std(ees),
            'mean_abs': np.mean(np.abs(ees))
        }
    return results

def plot_morris_results(results):
    param_names = list(results.keys())
    means_abs = [results[p]['mean_abs'] for p in param_names]
    stds = [results[p]['std'] for p in param_names]

    plt.figure(figsize=(10, 6))
    plt.scatter(means_abs, stds, s=80, c='blue', alpha=0.7)
    for i, name in enumerate(param_names):
        plt.annotate(name, (means_abs[i], stds[i]), xytext=(5, 5), textcoords='offset points', fontsize=9)
    plt.xlabel('Moyenne des |effets élémentaires| (influence moyenne)')
    plt.ylabel('Écart-type des effets (non-linéarité / interactions)')
    plt.title('Analyse de sensibilité de Morris')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()

def main():
    print("Lancement de l'analyse de Morris...")
    n_trajectories = 100   # ou 500
    results = morris_screening(n_trajectories=n_trajectories, random_seed=42)
    print("\nRésultats :")
    for p, stats in results.items():
        print(f"{p}: mean_EE = {stats['mean']:.2f}, std_EE = {stats['std']:.2f}, mean_abs_EE = {stats['mean_abs']:.2f}")
    plot_morris_results(results)

if __name__ == "__main__":
    main()