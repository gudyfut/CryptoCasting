import math

import torch
import torch.nn as nn
import torch.nn.functional as F


class Mamba(nn.Module):
    """Bloco Mamba (SSM seletivo) em PyTorch puro.

    Fallback sem kernels CUDA — funciona em CPU e em qualquer SO (incl. Windows).
    Tem a MESMA assinatura da classe oficial mamba_ssm.Mamba para que sejam
    intercambiáveis. Baseado na reimplementação de referência do paper.

    Paper: Gu & Dao, "Mamba: Linear-Time Sequence Modeling with Selective
    State Spaces" (arXiv:2312.00752).
    """

    def __init__(
        self,
        d_model: int = 512,
        d_state: int = 16,
        d_conv: int = 4,
        expand: int = 2,
    ):
        super().__init__()
        self.d_model = d_model
        self.d_state = d_state
        self.d_conv = d_conv
        self.expand = expand
        self.d_inner = self.expand * self.d_model
        self.dt_rank = math.ceil(self.d_model / 16)

        self.in_proj = nn.Linear(self.d_model, self.d_inner * 2, bias=False)

        self.conv1d = nn.Conv1d(
            in_channels=self.d_inner,
            out_channels=self.d_inner,
            bias=True,
            kernel_size=self.d_conv,
            padding=self.d_conv - 1,
            groups=self.d_inner,
            padding_mode="zeros",
        )

        self.x_proj = nn.Linear(
            self.d_inner, self.dt_rank + self.d_state * 2, bias=False
        )
        self.dt_proj = nn.Linear(
            self.dt_rank, self.d_inner, bias=True, dtype=torch.float32
        )

        A = torch.arange(1, self.d_state + 1, dtype=torch.float32).repeat(
            self.d_inner, 1
        )
        self.A_log = nn.Parameter(torch.log(A))
        self.D = nn.Parameter(torch.ones(self.d_inner))

        self.out_proj = nn.Linear(self.d_inner, self.d_model, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        (b, l, _) = x.shape

        x_and_res = self.in_proj(x)
        (x, res) = x_and_res.split(
            split_size=[self.d_inner, self.d_inner], dim=-1
        )

        x = x.transpose(1, 2)
        x = self.conv1d(x)[:, :, :l]
        x = x.transpose(1, 2)

        x = F.silu(x)

        y = self.ssm(x)

        y = y * F.silu(res)

        return self.out_proj(y)

    def ssm(self, x: torch.Tensor) -> torch.Tensor:
        (b, l, d_inner) = x.shape

        A = -torch.exp(self.A_log.float())
        D = self.D.float()

        x_dbl = self.x_proj(x)
        (delta, B, C) = x_dbl.split(
            split_size=[self.dt_rank, self.d_state, self.d_state], dim=-1
        )
        delta = F.softplus(self.dt_proj(delta))

        return self.selective_scan(x, delta, A, B, C, D)

    def selective_scan(
        self,
        u: torch.Tensor,
        delta: torch.Tensor,
        A: torch.Tensor,
        B: torch.Tensor,
        C: torch.Tensor,
        D: torch.Tensor,
    ) -> torch.Tensor:
        (b, l, d_inner) = u.shape
        n = A.shape[1]

        deltaA = torch.exp(delta.unsqueeze(-1) * A)
        deltaB_u = torch.einsum("bld,bln,bld->bldn", delta, B, u)

        h = torch.zeros(
            (b, d_inner, n), device=u.device, dtype=u.dtype
        )
        ys = []
        for i in range(l):
            h = deltaA[:, i] * h + deltaB_u[:, i]
            y = torch.einsum("bdn,bn->bd", h, C[:, i])
            ys.append(y)
        y = torch.stack(ys, dim=1)
        y = y + u * D

        return y
