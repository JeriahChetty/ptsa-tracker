#!/usr/bin/env python3
"""
View exported data
"""

import json

def view_data():
    with open('original_data_export.json', 'r') as f:
        data = json.load(f)

    print('🏢 Your Companies:')
    print('=' * 50)
    for company in data['tables']['companies']:
        print(f'- {company.get("name", "Unknown")} (ID: {company.get("id", "?")}, Industry: {company.get("industry_category", "Unknown")})')

    print(f'\n👥 Your Users:')
    print('=' * 50)
    for user in data['tables']['users']:
        company_id = user.get('company_id', 'None')
        print(f'- {user.get("email", "Unknown")} (Role: {user.get("role", "Unknown")}, Company ID: {company_id})')

    print(f'\n📋 Your Measures:')
    print('=' * 50)
    for measure in data['tables']['measures']:
        print(f'- {measure.get("name", "Unknown")} ({measure.get("category", "Unknown")})')

if __name__ == '__main__':
    view_data()