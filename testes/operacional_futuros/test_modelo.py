import io
import unittest
try:
    import torch
except ImportError:
    torch = None


@unittest.skipUnless(torch is not None and torch.cuda.is_available(), 'Qualificação exige CUDA oficial no WSL.')
class ModeloOperacional(unittest.TestCase):
    def setUp(self):
        from modelos.mamba_operacional import EspecificacaoOperacional, RedeMambaOperacional
        self.E, self.R = EspecificacaoOperacional, RedeMambaOperacional
        self.p = {'largura':32,'estado':16,'camadas':2,'convolucao':4,'expansao':2,'dropout':.1}

    def spec(self, dois=False):
        return self.E('sintetico',('O','H','L','C','V'),24,
            ('payoff_compra','payoff_venda') if dois else ('log_retorno_24h',))

    def test_referencia_mesmos_pesos_mesma_saida(self):
        from modelos.mamba import RedeMamba
        torch.manual_seed(42)
        a = RedeMamba(self.spec(),self.p).cuda().eval()
        b = self.R(self.spec(),self.p).cuda().eval()
        b.load_state_dict(a.state_dict(),strict=True)
        x = torch.randn(4,24,5,device='cuda')
        torch.testing.assert_close(a(x),b(x)[:,0],rtol=0,atol=0)

    def test_duas_saidas_atualizacao_e_recarga(self):
        torch.manual_seed(42)
        a = self.R(self.spec(True),self.p).cuda()
        x,y = torch.randn(4,24,5,device='cuda'),torch.randn(4,2,device='cuda')
        grupos = [{'params':[p for p in a.parameters() if not getattr(p,'_no_weight_decay',False)],'weight_decay':.001},
                  {'params':[p for p in a.parameters() if getattr(p,'_no_weight_decay',False)],'weight_decay':0.}]
        opt = torch.optim.AdamW(grupos,lr=.0002)
        antes = a.saida.weight.detach().clone()
        z = a(x)
        self.assertEqual(z.shape,y.shape)
        torch.nn.functional.mse_loss(z,y).backward()
        torch.nn.utils.clip_grad_norm_(a.parameters(),1.,error_if_nonfinite=True)
        opt.step()
        self.assertFalse(torch.equal(antes,a.saida.weight))
        memoria=io.BytesIO();torch.save(a.state_dict(),memoria);memoria.seek(0)
        b = self.R(self.spec(True),self.p).cuda().eval()
        b.load_state_dict(torch.load(memoria,weights_only=True),strict=True)
        torch.testing.assert_close(a.eval()(x),b(x),rtol=0,atol=0)
        with self.assertRaises(ValueError):
            b(torch.randn(4,24,4,device='cuda'))

    def test_cpu_nao_e_fallback(self):
        a = self.R(self.spec(),self.p).cuda().eval()
        with self.assertRaises(ValueError):
            a(torch.randn(4,24,5))


if __name__=='__main__':
    unittest.main()
