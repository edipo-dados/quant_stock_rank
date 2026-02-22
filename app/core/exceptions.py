"""Exceções customizadas para o sistema de ranking quantitativo."""


class QuantRankerException(Exception):
    """Exceção base para o sistema."""
    pass


class DataFetchError(QuantRankerException):
    """Erro ao buscar dados de API externa."""
    pass


class InsufficientDataError(QuantRankerException):
    """Dados insuficientes para cálculo de fator."""
    pass


class CalculationError(QuantRankerException):
    """Erro durante cálculo de fator ou score."""
    pass


class ConfigurationError(QuantRankerException):
    """Erro de configuração."""
    pass
