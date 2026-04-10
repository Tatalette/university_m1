def biomass(Bio: float, K: float, r: float) -> float:
    """
    Calcule l'accroissement de biomasse selon le modèle logistique.
    Accroissement = r * Bio * (1 - Bio/K)
    """
    if K == 0:
        raise ValueError("K ne peut pas être nul")
    return r * Bio * (1 - Bio / K)

def deltaBiomass(Bio: float, K: float, r: float, t: int) -> list:
    """Retourne la liste des biomasses pour t pas de temps."""
    lst = [Bio]
    current = Bio
    for _ in range(t):
        current = biomass(current, K, r)
        lst.append(current)
    return lst