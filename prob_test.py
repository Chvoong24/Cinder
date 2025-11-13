def range_exceedance_probability(hourly_probs):
    """
    Compute the probability that a temperature threshold is exceeded
    in at least one hour of the range.

    Args:
        hourly_probs: List of floats, each representing the probability
                      that the threshold is exceeded in that hour.

    Returns:
        Float: Probability that the threshold is exceeded in any hour.
    """
    prob_none = 1.0
    for p in hourly_probs:
        prob_none *= (1 - p)
    return 1 - prob_none


# Example usage
hourly_probs = [0.1, 0.1, 0.1, .1]
prob_range = range_exceedance_probability(hourly_probs)
print(f"Probability of exceeding threshold in range: {prob_range:.3f}")