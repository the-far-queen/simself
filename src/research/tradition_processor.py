import requests
from bs4 import BeautifulSoup
import re
import json
import time
from collections import defaultdict

class TraditionProcessor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.core_knowledge = defaultdict(dict)
        self.api_cache = {}
    
    def load_traditions(self):
        with open(self.file_path, 'r') as f:
            raw_text = f.read()
        
        entries = re.split(r'\n\d+\.\s*|\n\n', raw_text.strip())
        for entry in entries:
            if not entry.strip():
                continue
            parts = re.split(r'–|:', entry, maxsplit=1)
            if len(parts) >= 2:
                name = parts[0].strip()
                desc = parts[1].strip()
                self.core_knowledge[name] = {
                    'description': desc,
                    'sources': [],
                    'connections': []
                }
        return self.core_knowledge
    
    def augment_with_api(self, name):
        if name in self.api_cache:
            return self.api_cache[name]
        
        try:
            wiki_url = f"https://en.wikipedia.org/w/api.php?action=query&format=json&titles={name}&prop=extracts&exintro=True"
            response = requests.get(wiki_url, timeout=5)
            data = response.json()
            
            pages = data.get('query', {}).get('pages', {})
            if pages:
                page = next(iter(pages.values()))
                extract = page.get('extract', '')
                soup = BeautifulSoup(extract, 'html.parser')
                first_para = soup.find('p').get_text() if soup.find('p') else ""
            
            self.api_cache[name] = first_para
            return first_para
        
        except Exception as e:
            print(f"API lookup failed for {name}: {str(e)}")
            return ""
    
    def find_connections(self):
        names = list(self.core_knowledge.keys())
        for i, name1 in enumerate(names):
            for name2 in names[i+1:]:
                desc1 = self.core_knowledge[name1]['description'].lower()
                desc2 = self.core_knowledge[name2]['description'].lower()
                
                common_terms = set(desc1.split()) & set(desc2.split())
                if len(common_terms) > 2:
                    self.core_knowledge[name1]['connections'].append({
                        'tradition': name2,
                        'shared_terms': list(common_terms)
                    })
                    self.core_knowledge[name2]['connections'].append({
                        'tradition': name1,
                        'shared_terms': list(common_terms)
                    })
    
    def recursive_integrate(self, depth=2, current_depth=0):
        if current_depth >= depth:
            return
        
        new_additions = []
        for name in list(self.core_knowledge.keys()):
            if not self.core_knowledge[name].get('augmented'):
                api_data = self.augment_with_api(name)
                if api_data:
                    self.core_knowledge[name]['sources'].append({
                        'source': 'wikipedia',
                        'content': api_data
                    })
                    self.core_knowledge[name]['augmented'] = True
                    new_additions.append(name)
        
        for name in new_additions:
            self.recursive_integrate(depth, current_depth + 1)
    
    def save_core(self, output_file='core_knowledge.json'):
        with open(output_file, 'w') as f:
            json.dump(dict(self.core_knowledge), f, indent=2)

if __name__ == "__main__":
    processor = TraditionProcessor('1-100-ALL.txt')
    
    print("Loading traditions...")
    processor.load_traditions()
    
    print("Finding connections...")
    processor.find_connections()
    
    print("Recursive integration...")
    processor.recursive_integrate(depth=2)
    
    print("Saving core knowledge...")
    processor.save_core()
    
    print("Integration complete.")
