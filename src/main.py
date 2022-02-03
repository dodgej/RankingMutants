import wx
import torch
from UI.MNKFrame import MNKFrame
from settings import settings


print("CUDA available? ", torch.cuda.is_available())
torch.set_printoptions(sci_mode=False)
app = wx.App()
appTitle = 'Rank some agents and stuff!'
settings.frame = MNKFrame(title=appTitle)
settings.frame.Show()

app.MainLoop()
app.Destroy()
