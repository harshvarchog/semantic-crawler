import numpy as np
from scipy import stats

ALPHA = 0.05
BETA = 0.20
LOWER = np.log(BETA / (1 - ALPHA))
UPPER = np.log((1 - BETA) / ALPHA)
MIN_HISTORY = 10

def run_sprt(history, current_score, log_sum):
    if len(history) < MIN_HISTORY:
        return "collecting", log_sum

    mu0 = np.mean(history)
    sigma0 = np.std(history) or 0.01

    mu1 = mu0 - 2 * sigma0
    sigma1 = 2 * sigma0

    p_h0 = stats.norm.pdf(current_score, mu0, sigma0)
    p_h1 = stats.norm.pdf(current_score, mu1, sigma1)

    if p_h0 == 0:
        return "collecting", log_sum

    log_sum += float(np.log(p_h1 / p_h0))

    if log_sum <= LOWER:
        return "no_change", 0.0
    elif log_sum >= UPPER:
        return "change_detected", log_sum
    else:
        return "accumulating", log_sum
