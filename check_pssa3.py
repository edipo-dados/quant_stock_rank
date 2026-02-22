import requests

r = requests.get('http://localhost:8000/api/v1/ranking')
data = r.json()

# Find PSSA3.SA in the rankings
pssa = None
for asset in data['rankings']:
    if asset['ticker'] == 'PSSA3.SA':
        pssa = asset
        break

if pssa:
    print(f"\n{'='*60}")
    print(f"PSSA3.SA - Porto Seguro (Insurance - Diversified)")
    print(f"{'='*60}")
    print(f"Position: {pssa['rank']}/{data['total_assets']}")
    print(f"Final Score: {pssa['final_score']:.3f}")
    print(f"  Momentum Score: {pssa['momentum_score']:.2f}")
    print(f"  Quality Score:  {pssa['quality_score']:.2f}")
    print(f"  Value Score:    {pssa['value_score']:.2f}")
    print(f"{'='*60}\n")
else:
    print("PSSA3.SA not found in ranking")
