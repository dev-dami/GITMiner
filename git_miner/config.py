from pathlib import Path
from typing import Any

try:
    import tomllib  # type: ignore
except ImportError:
    import tomli as tomllib  # type: ignore


class Config:
    """Configuration management for Git-Miner."""

    def __init__(self, config_path: str | Path | None = None) -> None:
        self.config_path = (
            Path(config_path) if config_path and isinstance(config_path, (str, Path)) else None
        )
        self._config: dict[str, Any] = {}

        if self.config_path and self.config_path.exists():
            self.load()

    def load(self) -> None:
        """Load configuration from file."""
        if not self.config_path:
            raise ValueError("No config path specified")

        with open(self.config_path, "rb") as f:
            self._config = tomllib.load(f)  # type: ignore[assignment]

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key (supports nested keys with dots)
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value.

        Args:
            key: Configuration key (supports nested keys with dots)
            value: Value to set
        """
        keys = key.split(".")
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self) -> None:
        """Save configuration to file."""
        if not self.config_path:
            raise ValueError("No config path specified")

        with open(self.config_path, "w") as f:
            toml.dump(self._config, f)

    @property
    def github_token(self) -> str | None:
        token = self.get("github.token")
        return token if isinstance(token, str) else None

    @github_token.setter
    def github_token(self, value: str) -> None:
        self.set("github.token", value)

    @property
    def output_dir(self) -> str:
        value = self.get("output.dir", ".")
        return value if isinstance(value, str) else "."

    @output_dir.setter
    def output_dir(self, value: str) -> None:
        self.set("output.dir", value)

    @property
    def default_format(self) -> str:
        value = self.get("output.format", "csv")
        return value if isinstance(value, str) else "csv"

    @default_format.setter
    def default_format(self, value: str) -> None:
        self.set("output.format", value)

    @property
    def max_retries(self) -> int:
        value = self.get("api.max_retries", 3)
        return value if isinstance(value, int) else 3

    @max_retries.setter
    def max_retries(self, value: int) -> None:
        self.set("api.max_retries", value)

    @property
    def timeout(self) -> float:
        value = self.get("api.timeout", 30.0)
        return value if isinstance(value, (int, float)) else 30.0

    @timeout.setter
    def timeout(self, value: float) -> None:
        self.set("api.timeout", value)
