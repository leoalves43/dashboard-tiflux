"""De-para of Tiflux default names (English) to pt-BR, applied before rows reach the database.

Tiflux ships some system statuses/stages/priorities with English names; custom ones are already
in Portuguese and pass through unchanged. `raw` keeps the original payload.
"""

TRANSLATED_COLUMNS = ("status_name", "stage_name", "priority_name")

PT_BR_NAMES: dict[str, str] = {
    "Opened": "Aberto",
    "Closed": "Fechado",
    "Canceled": "Cancelado",
    "Pending": "Pendente",
    "Low": "Baixa",
    "Medium": "Média",
    "High": "Alta",
    "Urgent": "Urgente",
    "Critical": "Crítica",
}


def translate_name(name: str | None) -> str | None:
    """Example: translate_name("Opened") -> "Aberto"; translate_name("Em Atendimento") -> unchanged."""
    if name is None:
        return None
    return PT_BR_NAMES.get(name, name)
