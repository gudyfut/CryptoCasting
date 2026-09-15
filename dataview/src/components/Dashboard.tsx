const MOEDAS = ["BTC", "ETH", "XRP"];
const CANDLES = ["15 min", "1 hora", "4 horas", "1 dia"];

export default function Dashboard() {
  return (
    <main className="min-h-screen bg-gray-950 px-6 py-12 text-gray-100">
      <div className="mx-auto max-w-5xl space-y-8">
        <header className="space-y-3">
          <p className="text-sm text-blue-400">CryptoCasting · TCC</p>
          <h1 className="text-3xl font-semibold">Previsibilidade por moeda e candle</h1>
          <p className="max-w-3xl text-gray-400">
            Fundação experimental em preparação. A tabela apresentará a comparação
            do Mamba com referências random walk, prevalência, momentum e AR(1)
            para prever a direção das próximas 24 horas.
          </p>
        </header>
        <div className="overflow-x-auto rounded-xl border border-gray-800">
          <table className="w-full text-left text-sm">
            <caption className="p-4 text-left text-gray-400">
              Matriz planejada · resultados ainda não produzidos
            </caption>
            <thead className="bg-gray-900">
              <tr>
                <th scope="col" className="p-4">Moeda / candle</th>
                {CANDLES.map((candle) => <th scope="col" className="p-4" key={candle}>{candle}</th>)}
              </tr>
            </thead>
            <tbody>
              {MOEDAS.map((moeda) => (
                <tr key={moeda} className="border-t border-gray-800">
                  <th scope="row" className="p-4">{moeda}</th>
                  {CANDLES.map((candle) => (
                    <td key={candle} className="p-4 text-gray-500">Pendente</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-sm text-gray-400">
          Protocolo: docs/protocolo_experimental.md. O estudo utiliza OHLCV,
          classificação direcional e validação temporal walk-forward.
          Acurácia preditiva não constitui evidência de rentabilidade de trading.
        </p>
      </div>
    </main>
  );
}
