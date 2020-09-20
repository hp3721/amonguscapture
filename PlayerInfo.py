class PlayerInfo():
    def __init__(self, playerInfo):
        self.PlayerId = playerInfo[0]
        self.PlayerName = playerInfo[1]
        self.ColorId = playerInfo[2]
        self.HatId = playerInfo[3]
        self.PetId = playerInfo[4]
        self.SkinId = playerInfo[5]
        self.Disconnected = playerInfo[6]
        self.Tasks = playerInfo[7]
        self.IsImposter = playerInfo[8]
        self.IsDead = playerInfo[9]
        self._object = playerInfo[10]