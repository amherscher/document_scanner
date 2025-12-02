from __future__ import annotations
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
import os

def get_expense_file(workdir: Path) -> Path:
    return workdir / "expenses.csv"

def save_expense(workdir: Path, filename: str, classification: Dict, receipt_data: Dict) -> bool:
    expense_file = get_expense_file(workdir)
    file_exists = expense_file.exists()
    
    amounts = receipt_data.get('amounts', {})
    total = amounts.get('total')
    
    row = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'scan_date': receipt_data.get('date') or datetime.now().strftime('%Y-%m-%d'),
        'filename': filename,
        'category': classification.get('category', 'Unknown'),
        'confidence': f"{classification.get('confidence', 0):.2%}",
        'amount': f"${total:.2f}" if total else '',
        'amount_value': total if total else '',
        'vendor': receipt_data.get('vendor', ''),
        'invoice_number': receipt_data.get('invoice_number', ''),
        'subtotal': f"${amounts.get('subtotal', 0):.2f}" if amounts.get('subtotal') else '',
        'tax': f"${amounts.get('tax', 0):.2f}" if amounts.get('tax') else '',
    }
    
    try:
        with open(expense_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
        return True
    except Exception as e:
        print(f"Error saving expense: {e}")
        return False

def get_expenses(workdir: Path, limit: Optional[int] = None) -> List[Dict]:
    expense_file = get_expense_file(workdir)
    if not expense_file.exists():
        return []
    
    expenses = []
    try:
        with open(expense_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            expenses = list(reader)
            if limit:
                expenses = expenses[-limit:]
        return expenses[::-1]
    except Exception as e:
        print(f"Error reading expenses: {e}")
        return []

def get_expense_summary(workdir: Path) -> Dict:
    expense_file = get_expense_file(workdir)
    if not expense_file.exists():
        return {'total': 0, 'count': 0, 'by_category': {}}
    
    total_expenses = 0
    total_amount = 0.0
    by_category = {}
    
    try:
        with open(expense_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_expenses += 1
                amount_str = row.get('amount_value', '').replace('$', '').strip()
                if amount_str:
                    try:
                        amount = float(amount_str)
                        total_amount += amount
                        category = row.get('category', 'Unknown')
                        if category not in by_category:
                            by_category[category] = {'count': 0, 'total': 0.0}
                        by_category[category]['count'] += 1
                        by_category[category]['total'] += amount
                    except:
                        pass
    except Exception as e:
        print(f"Error calculating summary: {e}")
    
    return {
        'total': round(total_amount, 2),
        'count': total_expenses,
        'by_category': {k: {'count': v['count'], 'total': round(v['total'], 2)} for k, v in by_category.items()}
    }

