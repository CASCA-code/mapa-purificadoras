"""Constantes y funcion de la formula B4 (compartidas por build_b4.py y banda_confianza_b4.py). Ver docs/B4_FORMULA.md."""
# score_b4 = 100 x (W_D*Demanda* + W_A*Anclas* + W_C*Comp_bonus*)
W_D, W_A, W_C = 0.45, 0.45, 0.10        # pedido Nicolas 2026-10-03 (peso de competencia bajo: solo suma)
CAP_P = 0.80                            # SUPUESTO: tope del bonus en el percentil 80 de purificadoras/1,000 viv
CORTES = (60, 50, 40)                   # Excelente >=60, Buena >=50, Regular >=40, Baja <40 (SUPUESTO de presentacion)
# Casa (Violeta 116, Los Colorines, San Pedro Garza Garcia): pin aproximado ya usado en index.html (HOME) / docs/RUTA_CAMPO.md
CASA = (25.63028, -100.34602)           # (lat, lon) aprox. calle Violeta (OSM); no es geocodificacion exacta del numero 116

def comp_bonus(c_star, n_comp):
    """Bonus de competencia 0..1 (solo si hay competidores detectados). None si n_comp == 0 (componente EXCLUIDO)."""
    return None if n_comp == 0 else min(c_star, CAP_P) / CAP_P

def score(d, a, c_star, n_comp):
    """0 competidores detectados -> competencia EXCLUIDA, score renormalizado = 100*(wd*D+wa*A)/(wd+wa) (sin penalizar ni neutro: 'mercado sin atender').
    Con competidores -> max(renormalizado, 100*(wd*D+wa*A+wc*Cb)): el bono solo suma (nunca resta) y vale <= 10 pts."""
    base = 100 * (W_D * d + W_A * a) / (W_D + W_A)
    if n_comp == 0: return round(base, 2)
    return round(max(base, 100 * (W_D * d + W_A * a + W_C * comp_bonus(c_star, n_comp))), 2)
