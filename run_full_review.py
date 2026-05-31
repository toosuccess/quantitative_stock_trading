
import sys
import os

# 添加技能目录到路径
skills_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'skills')
sys.path.insert(0, skills_dir)

from stock_review_skills import run_stock_review

if __name__ == '__main__':
    print("="*60)
    print("🚀 开始全量股票复审")
    print("="*60)
    
    try:
        results = run_stock_review()
        print(f"\n✅ 全量复审完成！共复审 {len(results)} 只股票")
    except Exception as e:
        print(f"\n❌ 全量复审失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

