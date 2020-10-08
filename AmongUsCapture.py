from enum import Enum
from ProcessMemory import ProcessMemory
from PlayerInfo import PlayerInfo
from time import sleep
import struct

class AmongUsCapture():
    class GameState(Enum):
            NONE = 0
            LOBBY = 1
            TASKS = 2
            DISCUSSION = 3

    def __init__(self):
        self.muteAfterExile = True
        
        self.GameAssemblyPtr = 0
        self.UnityPlayerPtr = 0
        self.oldState = self.GameState.LOBBY

        self.playerColors = ["red", "blue", "green", "pink", "orange", "yellow", "black", "white", "purple", "brown", "cyan", "lime"]
        
        self.ProcessMemory = ProcessMemory()

    def main(self):
        while True:
            if not self.ProcessMemory.IsHooked:
                if not self.ProcessMemory.HookProcess("Among Us"):
                    sleep(1)
                    continue
                else:
                    print(f"Connected to Among Us process ({self.ProcessMemory.processPid})")

                    modulesLeft = 2
                    for module in self.ProcessMemory.modules:
                        if modulesLeft == 0:
                            break
                        elif module.Name.lower() == "GameAssembly.dll".lower():
                            self.GameAssemblyPtr = module.BaseAddress
                            modulesLeft -= 1
                        elif module.Name.lower() == "UnityPlayer.dll".lower():
                            self.UnityPlayerPtr = module.BaseAddress
                            modulesLeft -= 1

            state = self.GameState.NONE
            # inGame = bool(self.ProcessMemory.ReadPointer(self.UnityPlayerPtr, [0x127B310, 0xF4, 0x18, 0xA8], 1)[0])
            gameState = self.ProcessMemory.ReadPointer(self.GameAssemblyPtr, [0x5C, 0, 0x64], 1)[0]
            meetingHudState = self.ProcessMemory.ReadPointer(self.GameAssemblyPtr, [0x14686A0, 0x5C, 0, 0x84], 1)[0]
            
            allPlayersPtr = struct.unpack("<L", self.ProcessMemory.ReadPointer(self.GameAssemblyPtr, [0x1468864, 0x5C, 0, 0x24], 4))[0]
            if not allPlayersPtr:
                sleep(0.25)
                continue
            allPlayers = struct.unpack("<L", self.ProcessMemory.ReadPointer(allPlayersPtr, [0x8], 4))[0]
            playerCount = self.ProcessMemory.ReadPointer(allPlayersPtr, [0xC], 1)[0]

            playerAddrPtr = allPlayers + 0x10

            if not gameState or (meetingHudState > 2 and self.ExileEndsGame()):
                state = self.GameState.LOBBY
            elif meetingHudState < 4:
                state = self.GameState.DISCUSSION
            else:
                state = self.GameState.TASKS
            
            allPlayerInfos = []

            for i in range(playerCount):
                playerAddr = struct.unpack("<L", self.ProcessMemory.Read(playerAddrPtr, 4))[0]
                pi = PlayerInfo(struct.unpack("<xxxxxxxxBxxxLBxxxLLLBxxxLBBxxxL", self.ProcessMemory.Read(playerAddr, 49)))
                allPlayerInfos.append(pi)
                playerAddrPtr += 4

            print("\033[H\033[J")
            for pi in allPlayerInfos:
                print(f"Player ID {pi.PlayerId}; Name: {self.ProcessMemory.ReadString(pi.PlayerName)}; Color: {self.playerColors[pi.ColorId]}; Dead: " + ("yes" if pi.IsDead > 0 else "no") + "; Imposter: " + ("yes" if pi.IsImposter > 0 else "no"))

            # if state != self.oldState:
            #     print(f"State Changed to {state}")
            print(f"State: {state}")

            self.oldState = state
            sleep(0.25)

    def ExileEndsGame(self):
        return False

if __name__ == '__main__':
    AmongUsCapture().main()
