from VSFA import VSFA
import torch

model = VSFA()
model.load_state_dict(torch.load("VSFA.pt"))
print(model)