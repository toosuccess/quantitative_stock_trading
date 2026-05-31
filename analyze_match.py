import json

with open('pool_data.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

stocks = data.get('stocks', [])
print(f'Stock pool total: {len(stocks)}')

pool_codes = [s['stock_code'] for s in stocks]
print(f'Pool codes sample: {pool_codes[:10]}')

with open('review_data.json', 'r', encoding='utf-8-sig') as f:
    rdata = json.load(f)

review_codes = set()
for r in rdata['reviews']:
    code = r['stock_code']
    pure = code.replace('sh','').replace('sz','').replace('bj','')
    review_codes.add(code)
    review_codes.add(pure)
    review_codes.add(f'sh{pure}')
    review_codes.add(f'sz{pure}')
    review_codes.add(f'bj{pure}')

review_map = {}
for r in rdata['reviews']:
    code = r['stock_code']
    pure = code.replace('sh','').replace('sz','').replace('bj','')
    for c in [code, pure, f'sh{pure}', f'sz{pure}', f'bj{pure}']:
        review_map[c] = r

no_match = []
for s in stocks:
    code = s['stock_code']
    pure = code.replace('sh','').replace('sz','').replace('bj','')
    matched = review_map.get(code) or review_map.get(pure) or review_map.get(f'sh{pure}') or review_map.get(f'sz{pure}') or review_map.get(f'bj{pure}')
    if not matched:
        rating = s.get('latest_rating', '')
        score = s.get('composite_score', 0)
        no_match.append((code, s['stock_name'], rating, score))

print(f'\nStocks in pool but NOT in review data: {len(no_match)}')
for code, name, rating, score in no_match[:30]:
    print(f'  {code} {name} rating={rating} score={score}')

watch_no_review = [(c,n,r,s) for c,n,r,s in no_match if r == '观望']
print(f'\n观望 stocks without review: {len(watch_no_review)}')
for code, name, rating, score in watch_no_review:
    print(f'  {code} {name} score={score}')
