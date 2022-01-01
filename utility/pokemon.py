class PokemonStats:
    def __init__(self, hp = 0, attack = 0, defense = 0, sp_attack = 0, sp_defense = 0, speed = 0):
        self.set_stats(hp, attack, defense, sp_attack, sp_defense, speed)

    def __str__(self):
        return f'HP:  {self.hp}\nAttack:  {self.attack}\nDefense:  {self.defense}\nSp. Atk:  {self.sp_atk}\nSp. Def:  {self.sp_def}\nSpeed:  {self.speed}\n**Total:  {self.total}**'

    def __add__(self, other):
        return PokemonStats(
            self.hp + other.hp,
            self.attack + other.attack,
            self.defense + other.defense,
            self.sp_atk + other.sp_atk,
            self.sp_def + other.sp_def,
            self.speed + other.speed
        )

    def set_stats(self, hp, attack, defense, sp_attack, sp_defense, speed):
        self.hp = hp
        self.attack = attack
        self.defense = defense
        self.sp_atk = sp_attack
        self.sp_def = sp_defense
        self.speed = speed
        self.compute_total()

    def compute_total(self):
        self.total = self.hp + self.attack + self.defense + self.sp_atk + self.sp_def + self.speed

    def to_csv(self):
        return f'{self.hp},{self.attack},{self.defense},{self.sp_atk},{self.sp_def},{self.speed}'

def get_stat_range_str(stats_min : PokemonStats, stats_max: PokemonStats):
    return f'HP: {stats_min.hp} - {stats_max.hp}\nAttack: {stats_min.attack} - {stats_max.attack}\n' \
        f'Defense: {stats_min.defense} - {stats_max.defense}\nSp. Atk: {stats_min.sp_atk} - {stats_max.sp_atk}\n' \
        f'Sp. Def: {stats_min.sp_def} - {stats_max.sp_def}\nSpeed: {stats_min.speed} - {stats_max.speed}\n' \
        f'**Total: {stats_min.total} - {stats_max.total}**\n'

def _compute_hp_stat(hp_base: int, hp_evs: int, hp_ivs, level: int):
    return int(((2*hp_base + hp_ivs + int(hp_evs / 4)) * level) / 100) + level + 10

def _compute_other_stat(base: int, evs: int, ivs: int, nature: float, level: int):
    return int( float(int( ((2*base + ivs + int(evs / 4)) * level) / 100 )) * nature )

def compute_stats(base_stats : PokemonStats, evs : PokemonStats, ivs: PokemonStats, nature: PokemonStats, level: int):
    return PokemonStats(
        _compute_hp_stat(base_stats.hp, evs.hp, ivs.hp, level),
        _compute_other_stat(base_stats.attack, evs.attack, ivs.attack, nature.attack, level),
        _compute_other_stat(base_stats.defense, evs.defense, ivs.defense, nature.defense, level),
        _compute_other_stat(base_stats.sp_atk, evs.sp_atk, ivs.sp_atk, nature.sp_atk, level),
        _compute_other_stat(base_stats.sp_def, evs.sp_def, ivs.sp_def, nature.sp_def, level),
        _compute_other_stat(base_stats.speed, evs.speed, ivs.speed, nature.speed, level)
    )