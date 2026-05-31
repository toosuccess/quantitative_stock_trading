import json

with open('review_data.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

print(f'review count: {data["count"]}')
print(f'total_reviewed: {data["total_reviewed"]}')
print(f'statistics: {data["statistics"]}')

codes = [r['stock_code'] for r in data['reviews']]
print(f'\nTotal review codes: {len(codes)}')
print(f'First 10 codes: {codes[:10]}')
print(f'Last 10 codes: {codes[-10:]}')

pure_codes = [c.replace('sh','').replace('sz','').replace('bj','') for c in codes]
print(f'\nPure codes sample: {pure_codes[:10]}')

review_scores = [r['review_score'] for r in data['reviews'] if r['review_score'] is not None]
print(f'\nReview scores range: {min(review_scores):.1f} - {max(review_scores):.1f}')

zero_or_low = [r for r in data['reviews'] if r['review_score'] is not None and r['review_score'] <= 20]
print(f'\nLow score stocks (<=20): {len(zero_or_low)}')
for r in zero_or_low[:5]:
    print(f'  {r["stock_code"]} {r["stock_name"]} score={r["review_score"]}')

no_opinion = [r for r in data['reviews'] if not r.get('review_opinion')]
print(f'\nNo review opinion: {len(no_opinion)}')
