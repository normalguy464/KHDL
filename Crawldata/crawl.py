import requests
import json
import time
import pandas as pd
import re
from datetime import datetime

url = "https://moso.vn/api"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Referer": "https://moso.vn/",
    "Origin": "https://moso.vn"
}

base_payload = {
    "action": "find",
    "modelName": "Transaction",
    "filter": {
        "pLocation": {
            "$geoWithin": {
                "$box": [
                    [106.52215625292972, 10.33126945476703],
                    [106.79818774707034, 11.193358141916859]
                ]
            }
        },
        "listingStatus": "published"
    },
    "options": {
        "offset": 0,
        "limit": 100,
        "refFields": [
            "@user_TransactionUserMark",
            "@transaction_TransactionPropertyImage",
            "@contact",
            "@page"
        ],
        "userMarks": True,
        "sort": {"_createdAt": -1},
        "backRefFields": [
            "@user_TransactionUserMark",
            "@transaction_TransactionPropertyImage",
            "@model_TransactionUserMarkSummary"
        ],
        "text": "",
        "count": True
    }
}

def clean_text(text):
    """Loai bo emoji va khoang trang thua"""
    if not isinstance(text, str):
        return text
    
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001F900-\U0001F9FF"
        u"\U0001FA00-\U0001FA6F"
        u"\U00002600-\U000026FF"
        u"\U0001F7E0-\U0001F7EB"
        u"\u2022" 
        u"\u25A0-\u25FF" 
        u"\u25CB"  
        "]+", flags=re.UNICODE)
    
    text = emoji_pattern.sub('', text)
    text = ' '.join(text.split())
    
    return text.strip()

# Cache du lieu dia chi tu API
address_cache = {
    'provinces': {},
    'districts': {},
    'wards': {}
}

def load_address_database():
    """Tai du lieu dia chi tu API provinces.open-api.vn"""
    print("\nDang tai CSDL dia chi tu API...")
    
    try:
        # Lay danh sach tinh/thanh pho
        resp = requests.get("https://provinces.open-api.vn/api/p/", timeout=10)
        if resp.status_code == 200:
            provinces = resp.json()
            for province in provinces:
                # Luu theo code va theo ten
                address_cache['provinces'][str(province['code'])] = province['name']
                # Luu theo ten viet tat (VD: "Hồ Chí Minh" hoặc "79")
                name_lower = province['name'].lower()
                if 'hồ chí minh' in name_lower or 'ho chi minh' in name_lower:
                    address_cache['provinces']['hcm'] = province['name']
                    address_cache['provinces']['79'] = province['name']
            print(f"  Da tai {len(provinces)} tinh/thanh pho")
        
        # Lay chi tiet Tp.HCM (code 79)
        resp = requests.get("https://provinces.open-api.vn/api/p/79?depth=3", timeout=10)
        if resp.status_code == 200:
            hcm_data = resp.json()
            
            # Luu quan/huyen
            for district in hcm_data.get('districts', []):
                district_code = str(district['code'])
                district_name = district['name']
                address_cache['districts'][district_code] = district_name
                
                # Luu theo so (VD: "10" -> "Quận 10")
                match = re.search(r'Quận\s+(\d+)', district_name)
                if match:
                    num = match.group(1)
                    address_cache['districts'][num] = district_name
                
                # Luu phuong/xa
                for ward in district.get('wards', []):
                    ward_code = str(ward['code'])
                    ward_name = ward['name']
                    # Key: district_code-ward_number
                    match_ward = re.search(r'Phường\s+(\d+)', ward_name)
                    if match_ward:
                        ward_num = match_ward.group(1)
                        address_cache['wards'][f"{num}-{ward_num}"] = ward_name
                        address_cache['wards'][ward_code] = ward_name
            
            print(f"  Da tai {len(address_cache['districts'])} quan/huyen")
            print(f"  Da tai {len(address_cache['wards'])} phuong/xa")
            print("  Hoan thanh tai CSDL!\n")
            return True
            
    except Exception as e:
        print(f"  Loi khi tai CSDL: {e}")
        print("  Se su dung dia chi goc tu API\n")
        return False

def normalize_address(address):
    """Chuan hoa dia chi su dung CSDL"""
    if not isinstance(address, str) or not address:
        return address
    
    # Tach dia chi thanh cac phan
    parts = [p.strip() for p in address.split(',')]
    
    if len(parts) < 3:
        return address
    
    normalized_parts = []
    
    # Phan 1: Duong/So nha (giu nguyen)
    normalized_parts.append(parts[0])
    
    # Phan 2: Phuong (neu la so)
    ward_part = parts[1].strip()
    if ward_part.isdigit():
        # Tim trong cache: district_num-ward_num
        if len(parts) > 2:
            district_part = parts[2].strip()
            if district_part.isdigit():
                ward_key = f"{district_part}-{ward_part}"
                if ward_key in address_cache['wards']:
                    normalized_parts.append(address_cache['wards'][ward_key])
                else:
                    normalized_parts.append(f"Phường {ward_part}")
            else:
                normalized_parts.append(f"Phường {ward_part}")
        else:
            normalized_parts.append(f"Phường {ward_part}")
    else:
        normalized_parts.append(ward_part)
    
    # Phan 3: Quan (neu la so)
    if len(parts) > 2:
        district_part = parts[2].strip()
        if district_part.isdigit():
            if district_part in address_cache['districts']:
                normalized_parts.append(address_cache['districts'][district_part])
            else:
                normalized_parts.append(f"Quận {district_part}")
        else:
            normalized_parts.append(district_part)
    
    # Phan 4: Thanh pho
    if len(parts) > 3:
        city_part = parts[3].strip().lower()
        if 'hồ chí minh' in city_part or 'ho chi minh' in city_part or city_part == 'hcm':
            if 'hcm' in address_cache['provinces']:
                normalized_parts.append(address_cache['provinces']['hcm'])
            else:
                normalized_parts.append("Thành phố Hồ Chí Minh")
        else:
            normalized_parts.append(parts[3])
    
    # Cac phan con lai
    for i in range(4, len(parts)):
        normalized_parts.append(parts[i])
    
    return ', '.join(normalized_parts)

# Tai CSDL truoc khi crawl
has_address_db = load_address_database()

all_data = []
page = 0
max_retries = 3

print(f"Bat dau crawl du lieu tu moso.vn")
print(f"Thoi gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

while True:
    payload = base_payload.copy()
    payload["options"]["offset"] = page * 100
    
    retry_count = 0
    success = False
    
    while retry_count < max_retries and not success:
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if resp.status_code == 200:
                result = resp.json()
                
                if page == 0:
                    print(f"Cau truc response:")
                    print(f"   Type: {type(result)}")
                    if isinstance(result, dict):
                        print(f"   Keys: {list(result.keys())}")
                    print()
                
                if isinstance(result, dict):
                    data = result.get('models')
                    if data is None:
                        data = result.get('data') or result.get('results') or result.get('items') or result.get('docs')
                    
                    if page == 0 and 'count' in result:
                        print(f"Tong so ban ghi theo API: {result['count']}\n")
                    
                    if data is None:
                        print(f"Khong tim thay data key trong response. Keys: {result.keys()}")
                        break
                        
                elif isinstance(result, list):
                    data = result
                else:
                    print(f"Response type khong mong doi: {type(result)}")
                    break
                
                if not data or len(data) == 0:
                    print("\nDa crawl het du lieu!")
                    success = True
                    break
                
                all_data.extend(data)
                print(f"Trang {page + 1} - Thu thap {len(data)} ban ghi | Tong: {len(all_data)}")
                success = True
                page += 1
                
            elif resp.status_code == 429:
                print(f"Rate limit - Cho 5 giay...")
                time.sleep(5)
                retry_count += 1
                
            else:
                print(f"HTTP {resp.status_code} - {resp.text[:200]}")
                retry_count += 1
                
        except requests.exceptions.Timeout:
            print(f"Timeout - Thu lai lan {retry_count + 1}")
            retry_count += 1
            time.sleep(2)
            
        except Exception as e:
            print(f"Loi: {str(e)}")
            retry_count += 1
            time.sleep(2)
    
    if retry_count >= max_retries and not success:
        print(f"\nDung o trang {page + 1} sau {max_retries} lan thu")
        break
    
    if success and (not data or len(data) == 0):
        break
    
    time.sleep(1.5)
    
    if page >= 100:
        print("\nDa dat gioi han 100 trang")
        break

print(f"\n{'='*50}")
print(f"TONG KET")
print(f"{'='*50}")
print(f"Tong so ban ghi: {len(all_data)}")
print(f"So trang da crawl: {page}")

if len(all_data) > 0:
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_filename = f"moso_raw_{timestamp}.json"
    
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"Da luu JSON: {json_filename}")
    
    try:
        filtered_data = []
        for idx, item in enumerate(all_data, start=1):
            # Lay dia chi goc
            pAddress_obj = item.get('pAddress', {})
            address_full = ''
            if isinstance(pAddress_obj, dict):
                address_full = pAddress_obj.get('full', '')
            if not address_full:
                address_full = item.get('_pAddress', '')
            
            # Chuan hoa dia chi neu co CSDL
            if has_address_db:
                address_normalized = normalize_address(address_full)
            else:
                address_normalized = address_full
            
            filtered_item = {
                'index': idx,
                'address_original': clean_text(address_full),
                'address': clean_text(address_normalized),
                'price': item.get('price', ''),
                'type': clean_text(str(item.get('type', ''))),
                'pType': clean_text(str(item.get('pType', ''))),
                'pWidth': item.get('pWidth', ''),
                'pLength': item.get('pLength', ''),
                'pArea': item.get('pArea', ''),
                'pLandArea': item.get('pLandArea', ''),
                'pNumberOfFloors': item.get('pNumberOfFloors', ''),
                'pNumberOfBathrooms': item.get('pNumberOfBathrooms', ''),
                'pNumberOfBedrooms': item.get('pNumberOfBedrooms', ''),
                'pCertificateType': clean_text(str(item.get('pCertificateType', ''))),
                'pFurnitureStatus': clean_text(str(item.get('pFurnitureStatus', ''))),
                'description': clean_text(str(item.get('description', ''))),
                '_createdAt': item.get('_createdAt', '')
            }
            filtered_data.append(filtered_item)
        
        df = pd.DataFrame(filtered_data)
        csv_filename = f"moso_filtered_{timestamp}.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        print(f"Da luu CSV: {csv_filename}")
        print(f"So cot: {len(df.columns)}")
        print(f"\nCac cot da luu:")
        print(df.columns.tolist())
        print(f"\nPreview du lieu:")
        print(df.head())
        
        # In so sanh dia chi
        if has_address_db:
            print(f"\nVi du chuan hoa dia chi:")
            for i in range(min(3, len(filtered_data))):
                print(f"  Goc: {filtered_data[i]['address_original']}")
                print(f"  =>  {filtered_data[i]['address']}\n")
        
    except Exception as e:
        print(f"Loi khi xu ly CSV: {e}")
else:
    print("Khong co du lieu de luu")

print(f"\nHoan thanh luc: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")