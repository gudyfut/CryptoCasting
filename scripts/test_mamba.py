import torch

print(f"torch:   {torch.__version__}")
print(f"CUDA:    {torch.cuda.is_available()}")
print(f"GPU:     {torch.cuda.get_device_name(0)}")
print()

from mamba_ssm import Mamba
print("mamba-ssm: OK (oficial CUDA)")
print()

batch, length, dim = 2, 512, 64
x = torch.randn(batch, length, dim).to("cuda")
model = Mamba(d_model=dim, d_state=16, d_conv=4, expand=2).to("cuda")

y = model(x)
print(f"Forward pass OK — input {x.shape} -> output {y.shape}")

print("TUDO FUNCIONANDO!")
