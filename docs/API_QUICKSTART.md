# API Quickstart - Como Chamar a API de Ranking

Guia rápido e direto para consumir a API do Quant Stock Ranker.

## 🔗 URL Base

```
http://seu-ec2-ip:8000
```

## 📊 Endpoints Principais

### 1. Obter Ranking Atual (Top 10)

```bash
# cURL
curl http://seu-ec2-ip:8000/api/v1/top?n=10
```

```python
# Python
import requests

response = requests.get("http://seu-ec2-ip:8000/api/v1/top?n=10")
data = response.json()

print(f"Data: {data['date']}")
for asset in data['top_assets']:
    print(f"{asset['rank']}. {asset['ticker']} - Score: {asset['final_score']:.3f}")
```

```javascript
// JavaScript/Node.js
const axios = require('axios');

async function getTopStocks() {
    const response = await axios.get('http://seu-ec2-ip:8000/api/v1/top?n=10');
    const data = response.data;
    
    console.log(`Data: ${data.date}`);
    data.top_assets.forEach(asset => {
        console.log(`${asset.rank}. ${asset.ticker} - Score: ${asset.final_score}`);
    });
}

getTopStocks();
```

**Resposta:**
```json
{
  "date": "2024-03-07",
  "top_assets": [
    {
      "ticker": "ITUB3",
      "date": "2024-03-07",
      "final_score": 0.85,
      "base_score": 0.87,
      "momentum_score": 0.90,
      "quality_score": 0.88,
      "value_score": 0.75,
      "confidence": 0.92,
      "rank": 1
    }
  ],
  "n": 10
}
```

---

### 2. Obter Ranking Completo

```bash
# cURL
curl http://seu-ec2-ip:8000/api/v1/ranking
```

```python
# Python
import requests

response = requests.get("http://seu-ec2-ip:8000/api/v1/ranking")
data = response.json()

print(f"Data: {data['date']}")
print(f"Total de ativos: {data['total_assets']}")

# Top 5
for asset in data['rankings'][:5]:
    print(f"{asset['rank']}. {asset['ticker']} - Score: {asset['final_score']:.3f}")
```

---

### 3. Obter Detalhes de uma Ação Específica

```bash
# cURL
curl http://seu-ec2-ip:8000/api/v1/asset/ITUB3
```

```python
# Python
import requests

ticker = "ITUB3"
response = requests.get(f"http://seu-ec2-ip:8000/api/v1/asset/{ticker}")
data = response.json()

print(f"Ticker: {data['ticker']}")
print(f"Score Final: {data['score']['final_score']:.3f}")
print(f"Rank: {data['score']['rank']}")
print(f"\nBreakdown:")
print(f"  Momentum: {data['score']['momentum_score']:.3f}")
print(f"  Quality: {data['score']['quality_score']:.3f}")
print(f"  Value: {data['score']['value_score']:.3f}")
print(f"\nExplicação:\n{data['explanation']}")
```

**Resposta:**
```json
{
  "ticker": "ITUB3",
  "score": {
    "ticker": "ITUB3",
    "date": "2024-03-07",
    "final_score": 0.85,
    "momentum_score": 0.90,
    "quality_score": 0.88,
    "value_score": 0.75,
    "confidence": 0.92,
    "rank": 1
  },
  "explanation": "ITUB3 está em 1º lugar com score de 0.850...",
  "raw_factors": {
    "return_1m": 0.05,
    "return_6m": 0.15,
    "roe": 0.18,
    "pe_ratio": 8.5
  }
}
```

---

### 4. Obter Ranking de Data Específica

```bash
# cURL
curl "http://seu-ec2-ip:8000/api/v1/ranking?date=2024-03-01"
```

```python
# Python
import requests

date = "2024-03-01"
response = requests.get(
    "http://seu-ec2-ip:8000/api/v1/ranking",
    params={"date": date}
)
data = response.json()

print(f"Ranking de {data['date']}")
for asset in data['rankings'][:10]:
    print(f"{asset['rank']}. {asset['ticker']} - {asset['final_score']:.3f}")
```

---

### 5. Health Check

```bash
# cURL
curl http://seu-ec2-ip:8000/health
```

```python
# Python
import requests

response = requests.get("http://seu-ec2-ip:8000/health")
print(response.json())
# {"status": "healthy", "version": "1.0.0"}
```

---

## 🐍 Exemplo Completo em Python

```python
import requests
from typing import List, Dict

class QuantRankerAPI:
    """Cliente simples para API do Quant Stock Ranker"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def get_top_stocks(self, n: int = 10) -> Dict:
        """Obtém top N ações"""
        response = requests.get(f"{self.base_url}/api/v1/top", params={"n": n})
        response.raise_for_status()
        return response.json()
    
    def get_ranking(self, date: str = None) -> Dict:
        """Obtém ranking completo"""
        params = {"date": date} if date else {}
        response = requests.get(f"{self.base_url}/api/v1/ranking", params=params)
        response.raise_for_status()
        return response.json()
    
    def get_stock_details(self, ticker: str) -> Dict:
        """Obtém detalhes de uma ação"""
        response = requests.get(f"{self.base_url}/api/v1/asset/{ticker}")
        response.raise_for_status()
        return response.json()
    
    def is_healthy(self) -> bool:
        """Verifica se API está saudável"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.json().get("status") == "healthy"
        except:
            return False

# Uso
if __name__ == "__main__":
    api = QuantRankerAPI("http://seu-ec2-ip:8000")
    
    # Verificar saúde
    if not api.is_healthy():
        print("API não está respondendo!")
        exit(1)
    
    # Top 5 ações
    print("=== TOP 5 AÇÕES ===")
    top = api.get_top_stocks(n=5)
    for asset in top['top_assets']:
        print(f"{asset['rank']}. {asset['ticker']} - Score: {asset['final_score']:.3f}")
    
    # Detalhes de uma ação
    print("\n=== DETALHES ITUB3 ===")
    details = api.get_stock_details("ITUB3")
    print(f"Score: {details['score']['final_score']:.3f}")
    print(f"Rank: {details['score']['rank']}")
    print(f"Momentum: {details['score']['momentum_score']:.3f}")
    print(f"Quality: {details['score']['quality_score']:.3f}")
    print(f"Value: {details['score']['value_score']:.3f}")
```

---

## 🌐 Exemplo em JavaScript/Node.js

```javascript
const axios = require('axios');

class QuantRankerAPI {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }
    
    async getTopStocks(n = 10) {
        const response = await axios.get(`${this.baseUrl}/api/v1/top`, {
            params: { n }
        });
        return response.data;
    }
    
    async getRanking(date = null) {
        const params = date ? { date } : {};
        const response = await axios.get(`${this.baseUrl}/api/v1/ranking`, {
            params
        });
        return response.data;
    }
    
    async getStockDetails(ticker) {
        const response = await axios.get(`${this.baseUrl}/api/v1/asset/${ticker}`);
        return response.data;
    }
    
    async isHealthy() {
        try {
            const response = await axios.get(`${this.baseUrl}/health`, {
                timeout: 5000
            });
            return response.data.status === 'healthy';
        } catch {
            return false;
        }
    }
}

// Uso
(async () => {
    const api = new QuantRankerAPI('http://seu-ec2-ip:8000');
    
    // Verificar saúde
    if (!await api.isHealthy()) {
        console.log('API não está respondendo!');
        return;
    }
    
    // Top 5 ações
    console.log('=== TOP 5 AÇÕES ===');
    const top = await api.getTopStocks(5);
    top.top_assets.forEach(asset => {
        console.log(`${asset.rank}. ${asset.ticker} - Score: ${asset.final_score.toFixed(3)}`);
    });
    
    // Detalhes de uma ação
    console.log('\n=== DETALHES ITUB3 ===');
    const details = await api.getStockDetails('ITUB3');
    console.log(`Score: ${details.score.final_score.toFixed(3)}`);
    console.log(`Rank: ${details.score.rank}`);
})();
```

---

## 📱 Exemplo em cURL (Terminal)

```bash
#!/bin/bash

API_URL="http://seu-ec2-ip:8000"

# Health check
echo "=== HEALTH CHECK ==="
curl -s "$API_URL/health" | jq

# Top 5 ações
echo -e "\n=== TOP 5 AÇÕES ==="
curl -s "$API_URL/api/v1/top?n=5" | jq '.top_assets[] | "\(.rank). \(.ticker) - Score: \(.final_score)"'

# Detalhes de ITUB3
echo -e "\n=== DETALHES ITUB3 ==="
curl -s "$API_URL/api/v1/asset/ITUB3" | jq '{ticker, score: .score.final_score, rank: .score.rank}'

# Ranking completo
echo -e "\n=== RANKING COMPLETO ==="
curl -s "$API_URL/api/v1/ranking" | jq '{date, total: .total_assets, top_5: .rankings[:5]}'
```

---

## 🔐 Com Autenticação (se implementada)

```python
import requests

headers = {
    "Authorization": "Bearer YOUR_API_KEY"
}

response = requests.get(
    "http://seu-ec2-ip:8000/api/v1/ranking",
    headers=headers
)
```

---

## ⚠️ Tratamento de Erros

```python
import requests

def get_ranking_safe(api_url: str):
    """Obtém ranking com tratamento de erros"""
    try:
        response = requests.get(f"{api_url}/api/v1/ranking", timeout=10)
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.Timeout:
        print("Erro: Timeout ao conectar com a API")
        return None
    
    except requests.exceptions.ConnectionError:
        print("Erro: Não foi possível conectar com a API")
        return None
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print("Erro: Nenhum dado disponível")
        else:
            print(f"Erro HTTP: {e.response.status_code}")
        return None
    
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return None

# Uso
data = get_ranking_safe("http://seu-ec2-ip:8000")
if data:
    print(f"Ranking de {data['date']} com {data['total_assets']} ativos")
```

---

## 📚 Documentação Completa

Acesse a documentação interativa da API:

```
http://seu-ec2-ip:8000/docs
```

---

## 🎯 Resumo dos Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/health` | GET | Status da API |
| `/api/v1/ranking` | GET | Ranking completo |
| `/api/v1/top?n=10` | GET | Top N ações |
| `/api/v1/asset/{ticker}` | GET | Detalhes de uma ação |
| `/api/v1/ranking?date=YYYY-MM-DD` | GET | Ranking de data específica |

---

**Versão**: 2.7.0  
**Data**: Março 2026  
**Documentação Completa**: http://seu-ec2-ip:8000/docs
