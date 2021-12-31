class PokemonStats:
    def __init__(self, hp = 0, attack = 0, defense = 0, sp_attack = 0, sp_defense = 0, speed = 0):
        self.hp = hp
        self.attack = attack
        self.defense = defense
        self.sp_atk = sp_attack
        self.sp_def = sp_defense
        self.speed = speed
        self.total = self.hp + self.attack + self.defense + self.sp_atk + self.sp_def + self.speed

    def __str__(self):
        return f'HP:  {self.hp}\nAttack:  {self.attack}\nDefense:  {self.defense}\nSp. Atk:  {self.sp_atk}\nSp. Def:  {self.sp_def}\nSpeed:  {self.speed}\n**Total:  {self.total}**'
