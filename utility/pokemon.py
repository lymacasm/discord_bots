class PokemonStatsError(Exception):
    pass

class PokemonStats:
    def __init__(self, hp = 0, attack = 0, defense = 0, sp_attack = 0, sp_defense = 0, speed = 0, min_val = 0, max_val = 10000, max_total = 60000):
        self.set_stats(hp, attack, defense, sp_attack, sp_defense, speed)
        self.set_min_stat_val(min_val)
        self.set_max_stat_val(max_val)
        self.set_max_total_val(max_total)

    @classmethod
    def from_obj(cls, obj):
        return cls(obj.hp, obj.attack, obj.defense, obj.sp_atk, obj.sp_def, obj.speed, obj.__min_val, obj.__max_val, obj.__max_total)

    @classmethod
    def from_dict(cls, in_dict, min_val=0, max_val = 10000, max_total = 60000):
        return cls(in_dict['hp'], in_dict['attack'], in_dict['defense'], in_dict['sp_atk'], in_dict['sp_def'], in_dict['speed'], min_val=min_val, max_val=max_val, max_total=max_total)

    def __str__(self):
        return f'HP:  {self.hp}\nAttack:  {self.attack}\nDefense:  {self.defense}\nSp. Atk:  {self.sp_atk}\nSp. Def:  {self.sp_def}\nSpeed:  {self.speed}\n**Total:  {self.total}**'

    def __add__(self, other):
        new = PokemonStats.from_obj(self)
        for stat in ['hp', 'attack', 'defense', 'sp_atk', 'sp_def', 'speed']:
            new_val = getattr(new, stat)
            other_val = getattr(other, stat)
            new_val += other_val
            inc = other_val
            if new_val > new.__max_val:
                inc -= new_val - new.__max_val
                new_val = new.__max_val
            elif new_val < new.__min_val:
                inc -= new_val - new.__min_val
                new_val = new.__min_val
            new.total += inc
            if new.total > new.__max_total:
                new_val -= new.total - new.__max_total
                new.total = new.__max_total
            setattr(new, stat, new_val)
        return new

    def to_dict(self):
        return {
            'hp': self.hp,
            'attack': self.attack,
            'defense': self.defense,
            'sp_atk': self.sp_atk,
            'sp_def': self.sp_def,
            'speed': self.speed
        }

    def set_stats(self, hp, attack, defense, sp_attack, sp_defense, speed):
        self.hp = hp
        self.attack = attack
        self.defense = defense
        self.sp_atk = sp_attack
        self.sp_def = sp_defense
        self.speed = speed
        self.compute_total()

    def set_min_stat_val(self, min_stat_val):
        self.__min_val = min_stat_val
        for stat in ['hp', 'attack', 'defense', 'sp_atk', 'sp_def', 'speed']:
            stat_val = getattr(self, stat)
            if stat_val < min_stat_val:
                raise PokemonStatsError(f'The {stat} stat value of {stat_val} is below the minimum of {min_stat_val}.')

    def set_max_stat_val(self, max_stat_val):
        self.__max_val = max_stat_val
        for stat in ['hp', 'attack', 'defense', 'sp_atk', 'sp_def', 'speed']:
            stat_val = getattr(self, stat)
            if stat_val > max_stat_val:
                raise PokemonStatsError(f'The {stat} stat value of {stat_val} exceeds the maximum of {max_stat_val}.')

    def set_max_total_val(self, max_total_val):
        self.__max_total = max_total_val
        if self.total > max_total_val:
            raise PokemonStatsError(f'The stats total of {self.total} exceeds the maximum of {max_total_val}.')

    def compute_total(self):
        self.total = self.hp + self.attack + self.defense + self.sp_atk + self.sp_def + self.speed

    def to_csv(self):
        return f'{self.hp},{self.attack},{self.defense},{self.sp_atk},{self.sp_def},{self.speed}'

def _get_val_range_str(val_low, val_high):
    return f'{val_low} - {val_high}' if val_low != val_high else f'{val_low}'

def get_stat_range_str(stats_min : PokemonStats, stats_max: PokemonStats):
    return f'HP: {_get_val_range_str(stats_min.hp, stats_max.hp)}\nAttack: {_get_val_range_str(stats_min.attack, stats_max.attack)}\n' \
        f'Defense: {_get_val_range_str(stats_min.defense, stats_max.defense)}\nSp. Atk: {_get_val_range_str(stats_min.sp_atk, stats_max.sp_atk)}\n' \
        f'Sp. Def: {_get_val_range_str(stats_min.sp_def, stats_max.sp_def)}\nSpeed: {_get_val_range_str(stats_min.speed, stats_max.speed)}\n' \
        f'**Total: {_get_val_range_str(stats_min.total, stats_max.total)}**\n'

def _compute_hp_stat(hp_base: int, hp_evs: int, hp_ivs, level: int):
    return int(((2*hp_base + hp_ivs + int(hp_evs / 4)) * level) / 100) + level + 10

def _compute_other_stat(base: int, evs: int, ivs: int, nature: float, level: int):
    return int( float(int( ((2*base + ivs + int(evs / 4)) * level) / 100 ) + 5) * nature )

def compute_stats(base_stats : PokemonStats, evs : PokemonStats, ivs: PokemonStats, nature: PokemonStats, level: int):
    return PokemonStats(
        _compute_hp_stat(base_stats.hp, evs.hp, ivs.hp, level),
        _compute_other_stat(base_stats.attack, evs.attack, ivs.attack, nature.attack, level),
        _compute_other_stat(base_stats.defense, evs.defense, ivs.defense, nature.defense, level),
        _compute_other_stat(base_stats.sp_atk, evs.sp_atk, ivs.sp_atk, nature.sp_atk, level),
        _compute_other_stat(base_stats.sp_def, evs.sp_def, ivs.sp_def, nature.sp_def, level),
        _compute_other_stat(base_stats.speed, evs.speed, ivs.speed, nature.speed, level)
    )