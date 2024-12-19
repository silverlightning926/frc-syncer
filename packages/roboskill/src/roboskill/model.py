from roboskill.rating import Rating
from typing import List
import numpy as np
from statistics import NormalDist

LEARNING_RATE: np.float32 = np.float32(0.1)
DECAY_RATE: np.float32 = np.float32(0.99)


class Model:

    _normal = NormalDist(mu=0, sigma=1)

    def _calculate_team_rating(self, ratings: np.ndarray) -> Rating:
        mus = np.array([r.mu for r in ratings], dtype=np.float32)
        sigmas = np.array([r.sigma for r in ratings], dtype=np.float32)

        return Rating(
            mu=np.sum(mus, dtype=np.float32),
            sigma=np.sqrt(np.sum(sigmas**2, dtype=np.float32)),
        )

    def predict_win(
        self,
        red_alliance: np.ndarray,
        blue_alliance: np.ndarray,
    ) -> np.ndarray:
        red_rating = self._calculate_team_rating(red_alliance)
        blue_rating = self._calculate_team_rating(blue_alliance)

        delta_mu = np.float32(red_rating.mu - blue_rating.mu)
        delta_sigma = np.sqrt(
            red_rating.sigma**2 + blue_rating.sigma**2, dtype=np.float32
        )

        red_win_probability = np.float32(self._normal.cdf(delta_mu / delta_sigma))
        blue_win_probability = np.float32(1.0 - red_win_probability)

        return np.array([red_win_probability, blue_win_probability], dtype=np.float32)

    def rate(
        self,
        red_alliance: np.ndarray,
        blue_alliance: np.ndarray,
        red_score: np.float32,
        blue_score: np.float32,
    ) -> tuple[np.ndarray, np.ndarray]:
        red_score = np.float32(red_score)
        blue_score = np.float32(blue_score)

        red_win_probability, blue_win_probability = self.predict_win(
            red_alliance, blue_alliance
        )

        outcome = np.float32(1) if red_score > blue_score else np.float32(0)

        prediction_error = np.abs(outcome - red_win_probability, dtype=np.float32)

        margin_of_victory = np.abs(red_score - blue_score, dtype=np.float32)

        mov_scaling_factor = np.log1p(margin_of_victory) + np.float32(1.0)

        red_team_rating = self._calculate_team_rating(red_alliance)
        blue_team_rating = self._calculate_team_rating(blue_alliance)

        new_red_ratings = []
        for r in red_alliance:
            performance_change = mov_scaling_factor * (outcome - red_win_probability)
            new_mu = (
                r.mu
                + (r.sigma**2 / (r.sigma**2 + red_team_rating.sigma**2))
                * performance_change
            )
            new_sigma = r.sigma * DECAY_RATE + np.sqrt(
                LEARNING_RATE * prediction_error**2, dtype=np.float32
            )
            new_red_ratings.append(Rating(mu=new_mu, sigma=new_sigma, name=r.name))

        new_blue_ratings = []
        for r in blue_alliance:
            performance_change = mov_scaling_factor * (
                (1 - outcome) - blue_win_probability
            )
            new_mu = (
                r.mu
                + (r.sigma**2 / (r.sigma**2 + blue_team_rating.sigma**2))
                * performance_change
            )
            new_sigma = r.sigma * DECAY_RATE + np.sqrt(
                LEARNING_RATE * prediction_error**2, dtype=np.float32
            )
            new_blue_ratings.append(Rating(mu=new_mu, sigma=new_sigma, name=r.name))

        return (
            np.array(
                new_red_ratings, dtype=object
            ),
            np.array(new_blue_ratings, dtype=object),
        )
