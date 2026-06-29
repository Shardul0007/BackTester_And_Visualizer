from utils.strike import nearest_strike
print(nearest_strike(
    18126,
    [
        18050,
        18100,
        18150,
        18200,
    ],
) == 18150)