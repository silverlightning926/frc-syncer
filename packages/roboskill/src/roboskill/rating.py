import numpy as np
from typing import Optional


class Rating:

    def __init__(
        self,
        mu: np.float32 = np.float32(25.0),
        sigma: np.float32 = np.float32(25.0 / 3.0),
        name: Optional[str] = None,
    ):
        self.mu: np.float32 = np.float32(mu)
        self.sigma: np.float32 = np.float32(sigma)
        self.name: Optional[str] = name

    def ordinal(
        self,
        z: np.float32 = np.float32(3.0),
    ) -> np.float32:
        return np.float32(self.mu - z * self.sigma)

    @property
    def mu(self) -> np.float32:
        return self._mu

    @mu.setter
    def mu(self, value: np.float32) -> None:
        self._mu = np.float32(value)

    @property
    def sigma(self) -> np.float32:
        return self._sigma

    @sigma.setter
    def sigma(self, value: np.float32) -> None:
        self._sigma = np.float32(value)

    def __str__(self) -> str:
        return f"Rating(name={self.name}, mu={self.mu}, sigma={self.sigma}, ordinal={self.ordinal()})"

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other) -> bool:
        if not isinstance(other, Rating):
            return False
        return self.mu == other.mu and self.sigma == other.sigma

    def __hash__(self) -> int:
        return hash((self.mu, self.sigma, self.name))
