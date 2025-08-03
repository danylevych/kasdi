from enum import Enum


class AgeRestrictionEnum(str, Enum):
    ALL = "all"
    WITHOUT_RESTRICTION = "without restriction"
    FORTEEN_PLUS = "14+"
    SIXTEEN_PLUS = "16+"
    EIGHTEEN_PLUS = "18+"


class GenreEnum(str, Enum):
    ALL = "All"
    FANTASY = "Фентезі"
    THRILLERS_AND_HORROR = "Трилери та жахи"
    DETECTIVES = "Детективи"
    ROMANTIC_PROSE = "Романтична проза"
    CLASSICAL_LITERATURE = "Класична література"
    MODERN_AUTHORS = "Сучасні автори"
    FICTION = "Фантастика"
    HISTORICAL_AND_ADVENTURE_PROSE = "Історична та пригодницька проза"
    COMICS_AND_MANGA = "Комікси та манґи"

