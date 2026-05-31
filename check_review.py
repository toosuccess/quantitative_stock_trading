import pymysql
from pymysql.cursors import DictCursor

MYSQL_CONFIG = {
    'host': '118.25.137.191',
    'user': 'root',
    'password': 'Root@2026Mysql!',
    'database': 'stock',
    'charset': 'utf8mb4'
}

conn = pymysql.connect(**MYSQL_CONFIG, cursorclass=DictCursor)
cursor = conn.cursor()

print('=== 观望股票(composite_score 30-50)在stock_basic_info中的复审情况 ===')
cursor.execute('''
    SELECT sr.stock_code as sr_code, sr.stock_name, sr.composite_score, sr.rating,
           sbi.stock_code as sbi_code, sbi.review_score, sbi.review_opinion IS NOT NULL as has_opinion
    FROM score_record sr
    INNER JOIN (
        SELECT stock_code, MAX(id) as max_id FROM score_record GROUP BY stock_code
    ) latest ON sr.id = latest.max_id
    LEFT JOIN stock_basic_info sbi ON (
        sbi.stock_code = sr.stock_code 
        OR sbi.stock_code = CONCAT('sh', sr.stock_code)
        OR sbi.stock_code = CONCAT('sz', sr.stock_code)
        OR sbi.stock_code = CONCAT('bj', sr.stock_code)
        OR REPLACE(sbi.stock_code, 'sh', '') = sr.stock_code
        OR REPLACE(sbi.stock_code, 'sz', '') = sr.stock_code
        OR REPLACE(sbi.stock_code, 'bj', '') = sr.stock_code
    )
    WHERE sr.composite_score >= 30 AND sr.composite_score < 50
    ORDER BY sr.composite_score DESC
''')
watch_stocks = cursor.fetchall()
print(f'观望股票总数: {len(watch_stocks)}')
no_review_count = 0
for s in watch_stocks:
    has_review = s['review_score'] is not None
    has_opinion = s['has_opinion']
    if not has_review or not has_opinion:
        no_review_count += 1
        sbi_code = s['sbi_code'] or 'NOT_FOUND'
        print(f'  ❌ {s["sr_code"]}({s["stock_name"]}) score={s["composite_score"]} sbi_code={sbi_code} review_score={s["review_score"]} has_opinion={has_opinion}')

print(f'\n观望股票中缺少复审意见的数量: {no_review_count}/{len(watch_stocks)}')

print()
print('=== 所有评级股票在stock_basic_info中的复审覆盖情况 ===')
cursor.execute('''
    SELECT sr.rating, 
           COUNT(*) as total,
           SUM(CASE WHEN sbi.review_score IS NOT NULL THEN 1 ELSE 0 END) as reviewed,
           SUM(CASE WHEN sbi.review_score IS NULL OR sbi.review_score IS NULL THEN 1 ELSE 0 END) as not_reviewed
    FROM score_record sr
    INNER JOIN (
        SELECT stock_code, MAX(id) as max_id FROM score_record GROUP BY stock_code
    ) latest ON sr.id = latest.max_id
    LEFT JOIN stock_basic_info sbi ON (
        sbi.stock_code = sr.stock_code 
        OR sbi.stock_code = CONCAT('sh', sr.stock_code)
        OR sbi.stock_code = CONCAT('sz', sr.stock_code)
        OR sbi.stock_code = CONCAT('bj', sr.stock_code)
        OR REPLACE(sbi.stock_code, 'sh', '') = sr.stock_code
        OR REPLACE(sbi.stock_code, 'sz', '') = sr.stock_code
        OR REPLACE(sbi.stock_code, 'bj', '') = sr.stock_code
    )
    WHERE sr.composite_score >= 30
    GROUP BY sr.rating
    ORDER BY MIN(sr.composite_score) DESC
''')
for row in cursor.fetchall():
    print(f'  {row["rating"]}: 总数={row["total"]}, 已复审={row["reviewed"]}, 未复审={row["not_reviewed"]}')

print()
print('=== stock_basic_info中review_score IS NULL的股票(按是否在score_record中有记录) ===')
cursor.execute('''
    SELECT sbi.stock_code, sbi.stock_name,
           sr.composite_score, sr.rating
    FROM stock_basic_info sbi
    LEFT JOIN (
        SELECT sr.stock_code as sr_code, sr.stock_name as sr_name, sr.composite_score, sr.rating, sr.id
        FROM score_record sr
        INNER JOIN (
            SELECT stock_code, MAX(id) as max_id FROM score_record GROUP BY stock_code
        ) latest ON sr.id = latest.max_id
    ) sr ON (
        sr.sr_code = sbi.stock_code
        OR sr.sr_code = REPLACE(sbi.stock_code, 'sh', '')
        OR sr.sr_code = REPLACE(sbi.stock_code, 'sz', '')
        OR sr.sr_code = REPLACE(sbi.stock_code, 'bj', '')
        OR sr.sr_code = CONCAT('sh', REPLACE(REPLACE(sbi.stock_code, 'sz', ''), 'bj', ''))
        OR sr.sr_code = CONCAT('sz', REPLACE(REPLACE(sbi.stock_code, 'sh', ''), 'bj', ''))
    )
    WHERE sbi.review_score IS NULL
    AND sr.composite_score >= 30
    ORDER BY sr.composite_score DESC
    LIMIT 50
''')
missing_review = cursor.fetchall()
print(f'stock_basic_info中review_score为空且score_record有记录(score>=30)的股票: {len(missing_review)}')
for s in missing_review:
    sr_score = s['composite_score'] or 'N/A'
    sr_rating = s['rating'] or 'N/A'
    print(f'  {s["stock_code"]} {s["stock_name"]} score_record_score={sr_score} rating={sr_rating}')

conn.close()
