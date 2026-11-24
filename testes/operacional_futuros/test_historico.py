import io
import unittest
import zipfile
import numpy as np
import pandas as pd
from mercado_futuros.historico_operacional import ler_zip, COLUNAS, associar_funding, agregar_horas, intervalos_faltantes, validar_cobertura_funding


class Historico(unittest.TestCase):
    def test_milissegundos_no_settlement_nao_sao_lacuna(self):
        a = pd.DataFrame({'calc_time':[2,28800006,57600003],'funding_interval_hours':[8,8,8]})
        validar_cobertura_funding(a,0,86400000)
        with self.assertRaises(ValueError):
            validar_cobertura_funding(a.iloc[1:],0,86400000)
        with self.assertRaises(AssertionError):
            validar_cobertura_funding(a.iloc[[0,2]],0,86400000)

    def test_paginacao_nao_pula_lacunas_nem_sobrescreve_presentes(self):
        f = np.r_[np.arange(2000)*60000, np.arange(3000, 3100)*60000]
        partes = list(intervalos_faltantes(f))
        self.assertEqual([x[2] for x in partes], [1500, 500, 100])
        np.testing.assert_array_equal(np.concatenate([np.arange(a,b+1,60000) for a,b,n in partes]),f)
        self.assertEqual(list(intervalos_faltantes(np.array([],dtype='int64'))), [])

    def zip(self, texto):
        b = io.BytesIO()
        with zipfile.ZipFile(b, 'w') as z:
            z.writestr('dados.csv', texto)
        return b.getvalue()

    def test_primeiro_minuto_preservado_com_e_sem_cabecalho(self):
        linha = '1609459200000,100,105,95,101,3,1609459259999,303,2,1,101,0\n'
        a = ler_zip(self.zip(linha), 'klines')
        b = ler_zip(self.zip(','.join(COLUNAS) + '\n' + linha), 'klines')
        pd.testing.assert_frame_equal(a, b)
        self.assertEqual(len(a), 1)
        self.assertEqual(a.open_time.iloc[0], 1609459200000)

    def test_esquema_desconhecido_rejeitado(self):
        with self.assertRaises(ValueError):
            ler_zip(self.zip('x,y\n1,2\n'), 'klines')

    def test_volume_invalido_rejeitado(self):
        for valor in ['inf', '-2', 'nan']:
            with self.assertRaises(ValueError):
                ler_zip(self.zip(f'0,100,101,99,100,{valor},59999,0,2,0,0,0\n'), 'klines')

    def dados_funding(self):
        api = pd.DataFrame({'fundingTime': [2, 480*60000+6], 'fundingRate': ['.001', '-.001'], 'markPrice': ['', '120']})
        arquivo = pd.DataFrame({'calc_time': [0, 480*60000], 'funding_interval_hours': [8, 8], 'last_funding_rate': [.001, -.001]})
        marca = pd.DataFrame({'open_time': [0, 480*60000], 'open': [100, 120], 'high': [102, 122], 'low': [98, 118]})
        return api, arquivo, marca

    def test_funding_ausente_nao_vira_exato(self):
        a, b, c = self.dados_funding()
        f = associar_funding(a, b, c)
        self.assertTrue(np.isnan(f.markPrice.iloc[0]))
        self.assertFalse(f.markPrice_exato_disponivel.iloc[0])
        self.assertEqual(f.marca_minuto_high.iloc[0], 102)
        self.assertEqual(f.markPrice.iloc[1], 120)
        self.assertTrue(f.markPrice_exato_disponivel.iloc[1])

    def test_funding_invalido_nao_e_ocultado(self):
        for valor in ['erro', '-1', 'inf']:
            a, b, c = self.dados_funding()
            a.loc[0, 'markPrice'] = valor
            with self.assertRaises(ValueError):
                associar_funding(a, b, c)

    def test_divergencia_taxa_ou_cobertura_rejeitada(self):
        a, b, c = self.dados_funding()
        b.loc[0, 'last_funding_rate'] = .5
        with self.assertRaises(AssertionError):
            associar_funding(a, b, c)
        a, b, c = self.dados_funding()
        with self.assertRaises(ValueError):
            associar_funding(a, b, c.iloc[1:])

    def test_hora_fechada_e_volume_somado(self):
        q = pd.DataFrame({'open_time': np.arange(60)*60000, 'close_time': np.arange(60)*60000+59999,
            'open': np.arange(60)+100, 'high': np.arange(60)+102, 'low': np.arange(60)+99,
            'close': np.arange(60)+101, 'volume': np.ones(60)*2})
        h = agregar_horas(q)
        self.assertEqual(h.close.iloc[0], 160)
        self.assertEqual(h.high.iloc[0], 161)
        self.assertEqual(h.volume.iloc[0], 120)
        with self.assertRaises(ValueError):
            agregar_horas(q.iloc[:-1])


if __name__ == '__main__':
    unittest.main()
