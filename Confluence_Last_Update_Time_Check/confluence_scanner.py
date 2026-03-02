import requests
import re
from datetime import datetime
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin
import html
import openai
import os

class ConfluenceScanner:
    def __init__(self, config_path="config.json"):
        """
        初始化Confluence扫描器，从配置文件读取配置
        """
        # 加载配置文件
        self.config = self.load_config(config_path)
        
        # Confluence配置
        self.username = self.config['confluence']['username']
        self.password = self.config['confluence']['password']
        
        # 创建会话
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        
        # AI配置
        self.openai_api_key = self.config['ai']['openai_api_key']
        self.use_ai = self.config['ai']['use_ai']
        if self.openai_api_key and self.use_ai:
            openai.api_key = self.openai_api_key
            self.client = openai.OpenAI(
                api_key=self.openai_api_key, 
                base_url=self.config['ai']['ai_base_url']
            )
            self.model = self.config['ai']['ai_model']
        else:
            self.use_ai = False
        
        # AI缓存（避免重复分析）
        self.ai_cache = {}
        
        # 存储所有数据
        self.data = {
            'summary_page': {},
            'parent_pages': [],
            'child_pages': [],  # 包含所有层级的子页面
            'hierarchy_data': {},  # 层级结构数据
            'report_page': {}
        }
        
        # 扫描配置
        self.scan_config = {
            'max_depth': self.config['scan']['default_max_depth'],
            'max_threads': self.config['scan']['default_max_threads']
        }
        
        # AI分析配置
        self.ai_config = {
            'max_analyze': self.config['ai']['max_analyze'],
            'batch_size': self.config['ai']['batch_size']
        }
        
        # 统计信息
        self.stats = {
            'start_time': None,
            'end_time': None,
            'total_parents': 0,
            'total_children': 0,
            'success_parents': 0,
            'failed_parents': 0,
            'depth_stats': {}  # 各深度页面统计
        }
    
    def load_config(self, config_path):
        """加载配置文件"""
        # 如果提供了相对路径，则在当前目录查找
        if not os.path.isabs(config_path):
            config_path = os.path.join(os.path.dirname(__file__), config_path)
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_default_config(self):
        """不再提供默认配置，如果配置文件不存在则报错"""
        raise NotImplementedError("默认配置已移除，请提供有效的配置文件")
    
    def set_scan_config(self, max_depth=None, max_threads=None):
        """
        设置扫描配置
        """
        if max_depth is not None:
            self.scan_config['max_depth'] = max_depth
        if max_threads is not None:
            self.scan_config['max_threads'] = max_threads
        
        print(f"📊 扫描配置: 最大深度={self.scan_config['max_depth']}, "
              f"并发线程数={self.scan_config['max_threads']}")
    
    def create_complete_report(self, summary_page_url, target_page_url, max_threads=None):
        """
        创建完整的报告：扫描 + 生成到自定义Confluence页面
        """
        print("="*80)
        print("🚀 Confluence自动报告生成系统")
        print("="*80)
        
        # 使用配置的线程数或传入的参数
        if max_threads is None:
            max_threads = self.scan_config['max_threads']
        
        # 步骤1：解析目标页面信息
        print("\n🎯 步骤1: 解析目标页面...")
        target_page_info = self.get_page_info_by_url(target_page_url)
        if not target_page_info:
            print(f"❌ 无法解析目标页面: {target_page_url}")
            return False
        
        print(f"   ✓ 目标页面: {target_page_info['title']}")
        print(f"   ✓ 空间: {target_page_info['space_key']}")
        print(f"   ✓ 页面ID: {target_page_info['id']}")
        
        # 步骤2：扫描汇总页面
        print("\n📊 步骤2: 扫描汇总页面...")
        if not self.scan_summary_page(summary_page_url, max_threads):
            print("❌ 扫描失败")
            return False
        
        # 步骤3：更新目标页面
        print(f"\n📝 步骤3: 更新目标页面...")
        report_url = self.update_target_page(
            target_page_info,
            summary_page_url
        )
        
        if report_url:
            print(f"✅ 报告页面更新成功!")
            print(f"🔗 报告页面URL: {report_url}")
            
            # 步骤4：添加附件（可选）
            print(f"\n📎 步骤4: 添加附件...")
            self.add_attachments_to_page(target_page_info['id'], target_page_info['base_url'])
            
            return report_url
        else:
            print("❌ 报告页面更新失败")
            return False
    
    def scan_summary_page(self, summary_url, max_threads=None):
        """
        扫描汇总页面及其链接的子页面（支持多层级）
        """
        if max_threads is None:
            max_threads = self.scan_config['max_threads']
        
        self.stats['start_time'] = datetime.now()
        
        # 1. 获取汇总页面信息
        summary_info = self.get_page_info_by_url(summary_url)
        if not summary_info:
            return False
        
        self.data['summary_page'] = summary_info
        
        print(f"   ✓ 汇总页面: {summary_info['title']}")
        print(f"   ✓ 空间: {summary_info['space_key']}")
        
        # 2. 提取页面中的链接
        links = self.extract_confluence_links(summary_info['id'], summary_info['base_url'])
        if not links:
            print("⚠️  没有找到Confluence页面链接")
            return True  # 仍然返回True，因为汇总页面扫描成功
        
        print(f"   ✓ 找到 {len(links)} 个Confluence链接")
        
        # 3. 获取父页面信息
        parent_pages = self.get_parent_pages_parallel(links, max_threads)
        self.data['parent_pages'] = parent_pages
        self.stats['total_parents'] = len(parent_pages)
        self.stats['success_parents'] = len([p for p in parent_pages if p.get('id')])
        self.stats['failed_parents'] = len([p for p in parent_pages if not p.get('id')])
        
        # 4. 获取子页面信息（支持多层级）
        print(f"\n🌳 步骤4: 扫描子页面 (深度={self.scan_config['max_depth']})...")
        
        # 递归扫描多层子页面
        all_hierarchy_data = {}
        all_child_pages = []
        
        for parent in parent_pages:
            if parent.get('id'):
                print(f"   正在扫描: {parent['title'][:40]}...")
                
                hierarchy_data = self.scan_page_hierarchy(
                    parent['id'],
                    parent['base_url'],
                    parent['title']
                )
                
                if hierarchy_data:
                    all_hierarchy_data[parent['title']] = hierarchy_data
                    
                    # 提取所有层级的页面
                    all_pages = self.extract_all_pages_from_hierarchy(hierarchy_data)
                    all_child_pages.extend(all_pages)
        
        self.data['hierarchy_data'] = all_hierarchy_data
        self.data['child_pages'] = all_child_pages
        self.stats['total_children'] = len(all_child_pages)
        
        # 初始化AI分析字段
        for page in all_child_pages:
            page['ai_suspicious'] = False
            page['ai_reason'] = '未分析'
            page['ai_analyzed'] = False
        
        # 统计各深度页面数量
        for page in all_child_pages:
            depth = page.get('depth', 1)
            self.stats['depth_stats'][depth] = self.stats['depth_stats'].get(depth, 0) + 1

        # 5. 使用AI分析页面是否有过期嫌疑
        if self.use_ai and self.data['child_pages']:
            print(f"\n🤖 步骤5: AI分析页面内容...")
            self.data['child_pages'] = self.analyze_pages_with_ai(self.data['child_pages'])

        self.stats['end_time'] = datetime.now()
        
        # 打印扫描摘要
        self.print_scan_summary()
        
        return True
    
    def scan_page_hierarchy(self, page_id, base_url, parent_title, current_depth=1, path=""):
        """
        递归扫描页面层级结构
        """
        if current_depth > self.scan_config['max_depth']:
            return None
        
        print(f"     深度 {current_depth}: 扫描 {parent_title[:30]}...")
        
        # 获取当前页面的信息
        page_info = self.get_page_by_id(page_id, base_url)
        if not page_info:
            return None
        
        hierarchy = {
            'id': page_info['id'],
            'title': html.escape(page_info['title']),
            'url': page_info['url'],
            'last_updated': page_info['last_updated'],
            'version': page_info['version'],
            'depth': current_depth,
            'path': f"{path} > {page_info['title']}" if path else page_info['title'],
            'children': []
        }

        
        # 获取子页面
        child_pages = self.get_child_pages_for_parent(page_id, base_url)
        
        # 递归扫描子页面
        for child in child_pages:
            child_hierarchy = self.scan_page_hierarchy(
                child['id'],
                base_url,
                child['title'],
                current_depth + 1,
                hierarchy['path']
            )
            
            if child_hierarchy:
                hierarchy['children'].append(child_hierarchy)
        
        return hierarchy
    
    def extract_all_pages_from_hierarchy(self, hierarchy):
        """从层级结构中提取所有页面"""
        all_pages = []
        
        def extract_recursive(node):
            # 添加当前节点（跳过根节点，因为它是父页面）
            if node.get('depth', 1) > 1:  # 只添加子页面及以上
                all_pages.append({
                    'id': node['id'],
                    'title': node['title'],
                    'url': node['url'],
                    'last_updated': node['last_updated'],
                    'version': node['version'],
                    'depth': node['depth'],
                    'path': node['path'],
                    'ai_suspicious': False,
                    'ai_reason': "未分析",
                    'ai_analyzed': False,
                    'parent_title': hierarchy['title']  # 记录根父页面
                })
                #print(f'{all_pages[1]}')
            
            # 递归提取子节点
            for child in node.get('children', []):
                extract_recursive(child)
        
        extract_recursive(hierarchy)

        
        return all_pages
    
    def get_page_by_id(self, page_id, base_url):
        """通过ID获取页面信息"""
        url = f"{base_url}/rest/api/content/{page_id}"
        params = {'expand': 'history.lastUpdated,version'}
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                page = response.json()
                return {
                    'id': page['id'],
                    'title': page['title'],
                    'url': f"{base_url}{page.get('_links', {}).get('webui', '')}",
                    'last_updated': page.get('history', {}).get('lastUpdated', {}).get('when', ''),
                    'version': page.get('version', {}).get('number', '')
                }
        
        except Exception as e:
            print(f"获取页面 {page_id} 时出错: {str(e)}")
        
        return None
    
    def get_page_info_by_url(self, url):
        """通过URL获取页面信息"""
        try:
            match = re.search(r'/display/([^/]+)/(.+)', url)
            if not match:
                return None
            
            space_key = match.group(1)
            page_title = match.group(2).replace('+', ' ')
            base_url = re.match(r'(https?://[^/]+)', url).group(1)
            
            search_url = f"{base_url}/rest/api/content"
            params = {
                'spaceKey': space_key,
                'title': page_title,
                'expand': 'history.lastUpdated,version,space'
            }
            
            response = self.session.get(search_url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    page = data['results'][0]
                    return {
                        'id': page['id'],
                        'title': html.escape(page['title']),
                        'space_key': space_key,
                        'base_url': base_url,
                        'url': url,
                        'last_updated': page.get('history', {}).get('lastUpdated', {}).get('when', ''),
                        'version': page.get('version', {}).get('number', ''),
                        'space_name': page.get('space', {}).get('name', '')
                    }
        
        except Exception as e:
            print(f"获取页面信息时出错: {str(e)}")
        
        return None
    
    def extract_confluence_links(self, page_id, base_url):
        """从页面中提取Confluence链接"""
        url = f"{base_url}/rest/api/content/{page_id}"
        params = {'expand': 'body.view'}
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                page = response.json()
                content = page.get('body', {}).get('view', {}).get('value', '')
                
                links = []
                
                # 提取HTML链接
                html_pattern = r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>'
                html_matches = re.finditer(html_pattern, content, re.IGNORECASE | re.DOTALL)
                
                for match in html_matches:
                    href = match.group(1)
                    text = re.sub(r'<[^>]+>', '', match.group(2)).strip()
                    
                    if href and base_url in href and '/display/' in href:
                        links.append({
                            'url': href,
                            'title': text or '无标题'
                        })
                
                # 去重
                unique_links = []
                seen = set()
                
                for link in links:
                    key = link['url']
                    if key not in seen:
                        seen.add(key)
                        unique_links.append(link)
                
                return unique_links
        
        except Exception as e:
            print(f"提取链接时出错: {str(e)}")
        
        return []
    
    def get_parent_pages_parallel(self, links, max_threads):
        """并行获取父页面信息"""
        parent_pages = []
        
        print(f"   正在获取 {len(links)} 个父页面信息...")
        
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            future_to_link = {
                executor.submit(self.get_page_info_by_url, link['url']): link 
                for link in links
            }
            
            for future in as_completed(future_to_link):
                link = future_to_link[future]
                
                try:
                    page_info = future.result(timeout=30)
                    if page_info:
                        parent_pages.append(page_info)
                        print(f"    ✓ {page_info['title'][:50]}")
                    else:
                        print(f"    ✗ {link['title']} (获取失败)")
                        self.stats['failed_parents'] += 1
                except Exception:
                    print(f"    ✗ {link['title']} (异常)")
                    self.stats['failed_parents'] += 1
        
        return parent_pages
    
    def get_child_pages_parallel(self, parent_pages, max_threads):
        """并行获取子页面信息（直接子页面）"""
        all_children = []
        
        print(f"   正在扫描 {len(parent_pages)} 个父页面的直接子页面...")
        
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            future_to_parent = {}
            
            for parent in parent_pages:
                if parent.get('id'):
                    future = executor.submit(
                        self.get_child_pages_for_parent,
                        parent['id'],
                        parent['base_url']
                    )
                    future_to_parent[future] = parent
            
            for future in as_completed(future_to_parent):
                parent = future_to_parent[future]
                
                try:
                    children = future.result(timeout=30)
                    for child in children:
                        child['title'] = html.escape(child['title'])
                        child['parent_title'] = parent['title']
                        child['parent_id'] = parent['id']
                        child['depth'] = 1  # 直接子页面深度为1
                        all_children.append(child)
                    
                    print(f"    ✓ {parent['title'][:40]}: {len(children)} 个直接子页面")
                except Exception:
                    print(f"    ✗ {parent['title']} (获取子页面失败)")
        
        return all_children
    
    def get_child_pages_for_parent(self, parent_id, base_url):
        """获取指定父页面的直接子页面"""
        url = f"{base_url}/rest/api/content/search"
        
        cql = f'parent = {parent_id} and type = page'
        params = {
            'cql': cql,
            'expand': 'history.lastUpdated,version,space',
            'limit': 100
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                children = []
                for page in data.get('results', []):
                    children.append({
                        'id': page['id'],
                        'title': page['title'],
                        'url': f"{base_url}{page.get('_links', {}).get('webui', '')}",
                        'last_updated': page.get('history', {}).get('lastUpdated', {}).get('when', ''),
                        'version': page.get('version', {}).get('number', ''),
                        'space_key': page.get('space', {}).get('key', '')
                    })
                
                return children
        
        except Exception as e:
            print(f"获取子页面时出错: {str(e)}")
        
        return []
    
    def print_scan_summary(self):
        """打印扫描摘要"""
        elapsed = self.stats['end_time'] - self.stats['start_time']
        
        print("\n" + "="*80)
        print("📊 扫描完成!")
        print("="*80)
        print(f"汇总页面: {self.data['summary_page'].get('title', 'N/A')}")
        print(f"父页面数量: {self.stats['total_parents']} (成功: {self.stats['success_parents']}, 失败: {self.stats['failed_parents']})")
        print(f"子页面总数: {self.stats['total_children']}")
        
        # 如果有AI分析结果，显示统计
        if self.use_ai and self.data['child_pages']:
            ai_analyzed = sum(1 for p in self.data['child_pages'] if p.get('ai_analyzed', False))
            ai_suspicious = sum(1 for p in self.data['child_pages'] if p.get('ai_suspicious', False))
            
            print(f"AI分析页面: {ai_analyzed}")
            print(f"🚨 AI标记有嫌疑: {ai_suspicious}")
        
        if self.stats['depth_stats']:
            print(f"各深度页面统计:")
            for depth in sorted(self.stats['depth_stats'].keys()):
                count = self.stats['depth_stats'][depth]
                print(f"  深度 {depth}: {count} 个页面")
        
        print(f"扫描耗时: {elapsed.total_seconds():.2f} 秒")
        print("="*80)
    
    def update_target_page(self, target_page_info, summary_url):
        """
        更新自定义目标页面
        """
        page_id = target_page_info['id']
        page_title = target_page_info['title']
        space_key = target_page_info['space_key']
        base_url = target_page_info['base_url']
        
        # 获取当前页面版本
        page_details = self.get_page_by_id(page_id, base_url)
        if not page_details:
            print(f"   无法获取页面详细信息: {page_id}")
            return None
        
        current_version = page_details.get('version', 1)
        new_version = current_version + 1
        
        print(f"   正在更新页面: {page_title}")
        print(f"   当前版本: v{current_version}, 新版本: v{new_version}")
        
        # 生成页面内容
        page_content = self.generate_report_content(summary_url, target_page_info)
        
        # 更新页面
        update_url = f"{base_url}/rest/api/content/{page_id}"
        
        payload = {
            'id': page_id,
            'type': 'page',
            'title': page_title,
            'space': {'key': space_key},
            'body': {
                'storage': {
                    'value': page_content,
                    'representation': 'storage'
                }
            },
            'version': {
                'number': new_version,
                'message': f'自动更新扫描报告 - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - 深度:{self.scan_config["max_depth"]}'
            }
        }
        
        try:
            response = self.session.put(update_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                updated_page = response.json()
                report_url = f"{base_url}{updated_page.get('_links', {}).get('webui', '')}"
                
                self.data['report_page'] = {
                    'id': updated_page['id'],
                    'title': updated_page['title'],
                    'url': report_url,
                    'version': updated_page['version']['number']
                }
                
                return report_url
            
            else:
                print(f"   更新失败: HTTP {response.status_code}")
                print(f"   响应: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"更新页面时出错: {str(e)}")
            return None
    
    def generate_report_content(self, summary_url, target_page_info):
        """
        生成Confluence页面内容
        """
        # 获取当前时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 计算统计信息
        elapsed = self.stats['end_time'] - self.stats['start_time']
        
        # 总是生成层级报告（不再有条件判断）
        content = self.generate_hierarchy_report(current_time, elapsed, summary_url)
        
        return content
        
    def is_outdated(self, last_updated_str, months=6):
        """判断是否过期（超过指定月数未更新）"""
        if not last_updated_str:
            return True
        
        from datetime import datetime, timedelta
        
        # 解析日期字符串
        last_updated = datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
        date_part = str(last_updated)[:19]
        last_update = datetime.strptime(date_part, "%Y-%m-%d %H:%M:%S")
        
        # 计算半年前的时间
        six_months_ago = datetime.now() - timedelta(days=30*months)

        # 如果最后更新时间早于半年前，则认为是过期的
        return last_update < six_months_ago
        
    def generate_cell_content(self, cell_text, is_outdated=False):
        """生成单元格内容，根据需要添加样式"""
        if is_outdated:
            return f"<strong><span style='color: red;'>{cell_text}</span></strong>"
        else:
            return cell_text
        
    def generate_direct_children_report(self, current_time, elapsed, summary_url):
        """生成直接子页面报告"""
        # 按父页面统计子页面数量
        parent_stats = {}
        for child in self.data['child_pages']:
            parent = child['parent_title']
            parent_stats[parent] = parent_stats.get(parent, 0) + 1
        
        # 按最后更新时间排序子页面
        recent_children = sorted(
            [c for c in self.data['child_pages'] if c.get('last_updated')],
            key=lambda x: x['last_updated'],
            reverse=True
        )
        
        content = f"""
<h1>📊 Confluence页面扫描报告 (直接子页面)</h1>

<p><strong>报告生成时间:</strong> {current_time}</p>
<p><strong>扫描耗时:</strong> {elapsed.total_seconds():.2f} 秒</p>
<p><strong>扫描深度:</strong> 直接子页面 (深度=1)</p>

<hr />

<h2>📋 执行摘要</h2>

<table>
<tbody>
<tr>
<th>项目</th>
<th>数量</th>
</tr>
<tr>
<td>汇总页面</td>
<td>1</td>
</tr>
<tr>
<td>父页面总数</td>
<td>{self.stats['total_parents']}</td>
</tr>
<tr>
<td>成功获取的父页面</td>
<td>{self.stats['success_parents']}</td>
</tr>
<tr>
<td>失败的父页面</td>
<td>{self.stats['failed_parents']}</td>
</tr>
<tr>
<td>子页面总数</td>
<td>{self.stats['total_children']}</td>
</tr>
</tbody>
</table>

<h2>🔗 汇总页面信息</h2>
<ul>
<li><strong>标题:</strong> {self.data['summary_page'].get('title', 'N/A')}</li>
<li><strong>URL:</strong> <a href="{summary_url}">{summary_url}</a></li>
<li><strong>最后更新:</strong> {self.data['summary_page'].get('last_updated', 'N/A')}</li>
<li><strong>版本:</strong> v{self.data['summary_page'].get('version', 'N/A')}</li>
</ul>

<h2>📈 按父页面统计</h2>

<table>
<tbody>
<tr>
<th>父页面标题</th>
<th>子页面数量</th>
<th>占比</th>
</tr>
"""
        
        # 添加父页面统计行
        total_children = self.stats['total_children']
        for parent_title, count in sorted(parent_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_children * 100) if total_children > 0 else 0
            
            # 查找父页面信息以获取URL
            parent_url = ""
            for parent in self.data['parent_pages']:
                if parent['title'] == parent_title:
                    parent_url = parent['url']
                    break
            
            if parent_url:
                parent_link = f'<a href="{parent_url}">{parent_title}</a>'
            else:
                parent_link = parent_title
            
            content += f"""
<tr>
<td>{parent_link}</td>
<td>{count}</td>
<td>{percentage:.1f}%</td>
</tr>
"""
        
        content += """
</tbody>
</table>
"""
        
        return content
    
    def generate_hierarchy_report(self, current_time, elapsed, summary_url):
        """生成层级结构报告"""
        content = f"""
<h1>📊 Confluence页面层级扫描报告</h1>

<p><strong>报告生成时间:</strong> {current_time}</p>
<p><strong>扫描耗时:</strong> {elapsed.total_seconds():.2f} 秒</p>
<p><strong>扫描深度:</strong> {self.scan_config['max_depth']} 级</p>

<hr />

<h2>📋 执行摘要</h2>

<table>
<tbody>
<tr>
<th>项目</th>
<th>数量</th>
</tr>
<tr>
<td>汇总页面</td>
<td>1</td>
</tr>
<tr>
<td>父页面总数</td>
<td>{self.stats['total_parents']}</td>
</tr>
<tr>
<td>成功获取的父页面</td>
<td>{self.stats['success_parents']}</td>
</tr>
<tr>
<td>失败的父页面</td>
<td>{self.stats['failed_parents']}</td>
</tr>
<tr>
<td>扫描页面总数</td>
<td>{self.stats['total_children']}</td>
</tr>
</tbody>
</table>

<h2>📊 各深度页面统计</h2>

<table>
<tbody>
<tr>
<th>深度</th>
<th>页面数量</th>
<th>说明</th>
</tr>
"""
        
        # 添加深度统计
        for depth in sorted(self.stats['depth_stats'].keys()):
            count = self.stats['depth_stats'][depth]
            description = self.get_depth_description(depth)
            content += f"""
<tr>
<td>{depth}</td>
<td>{count}</td>
<td>{description}</td>
</tr>
"""
        
        content += """
</tbody>
</table>

<h2>🔗 汇总页面信息</h2>
<ul>
<li><strong>标题:</strong> {self.data['summary_page'].get('title', 'N/A')}</li>
<li><strong>URL:</strong> <a href="{summary_url}">{summary_url}</a></li>
<li><strong>最后更新:</strong> {self.data['summary_page'].get('last_updated', 'N/A')}</li>
<li><strong>版本:</strong> v{self.data['summary_page'].get('version', 'N/A')}</li>
</ul>

<h2>🌳 页面层级结构</h2>
"""
        
        # 生成层级结构展示
        for parent_title, hierarchy in self.data['hierarchy_data'].items():
            content += f"""
<h3>{html.escape(parent_title)}</h3>
"""
            content += self.generate_hierarchy_html(hierarchy, 1)
        
        return content
    
    def get_depth_description(self, depth):
        """获取深度描述"""
        descriptions = {
            1: "直接子页面",
            2: "孙子页面",
            3: "曾孙页面",
            4: "第4级页面",
            5: "第5级页面"
        }
        return descriptions.get(depth, f"第{depth}级页面")
    
    def generate_hierarchy_html(self, node, indent_level):
        """生成层级HTML，包含过期标记"""
        indent = "&nbsp;" * (indent_level * 4)
        
        # 判断该节点是否过期
        is_outdated = False
        if indent_level != 1:
            for page in self.data['child_pages']:
                if node['title'] == page['title']:
                    is_outdated = page.get('ai_suspicious', False)
                    break
        
        # 根据是否过期设置样式
        if is_outdated:
            style = "color: red; font-weight: bold;"
            outdated_icon = "⚠️ "
        else:
            style = ""
            outdated_icon = ""
        
        # 构建标题显示
        title_display = f"{outdated_icon}{node['title']}"
        
        # 如果有样式，包裹span标签
        if style:
            title_display = f"<span style='{style}'>{title_display}</span>"
        
        # 版本和时间显示（时间也要标红）
        time_display = node['last_updated'][:10]
        if is_outdated:
            time_display = f"<span style='color: red; font-weight: bold;'>{time_display}</span>"
        
        html = f"""
    <p>{indent}├─ <a href="{node['url']}">{title_display}</a> (v{node['version']}, {time_display})</p>
    """
        
        # 递归处理子节点
        for child in node.get('children', []):
            html += self.generate_hierarchy_html(child, indent_level + 1)
        
        return html
    
    def add_attachments_to_page(self, page_id, base_url):
        """为报告页面添加附件（数据文件）"""
        try:
            # 生成JSON数据文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_filename = f"scan_data_depth{self.scan_config['max_depth']}_{timestamp}.json"
            
            # 准备附件数据
            attachment_data = {
                'scan_config': self.scan_config,
                'scan_time': datetime.now().isoformat(),
                'summary_page': self.data['summary_page'],
                'parent_pages': self.data['parent_pages'],
                'child_pages': self.data['child_pages'],
                'hierarchy_data': self.data['hierarchy_data'],
                'statistics': self.stats
            }
            
            # 将JSON数据转换为文件
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
                json.dump(attachment_data, f, ensure_ascii=False, indent=2, default=str)
                temp_file_path = f.name
            
            # 上传附件
            upload_url = f"{base_url}/rest/api/content/{page_id}/child/attachment"
            
            headers = {
                'X-Atlassian-Token': 'no-check'
            }
            
            with open(temp_file_path, 'rb') as f:
                files = {
                    'file': (json_filename, f, 'application/json'),
                    'comment': (None, f'扫描数据备份 - 深度{self.scan_config["max_depth"]} - {timestamp}')
                }
                
                response = self.session.post(
                    upload_url,
                    headers=headers,
                    files=files,
                    auth=self.session.auth
                )
                
                if response.status_code == 200:
                    print(f"    ✓ 数据附件已添加: {json_filename}")
                else:
                    print(f"    ⚠️  附件添加失败: HTTP {response.status_code}")
            
            # 清理临时文件
            os.unlink(temp_file_path)
            
        except Exception as e:
            print(f"    ⚠️  添加附件时出错: {str(e)}")
    
    def generate_ai_analysis_section(self):
        """生成AI分析部分"""
        if not self.use_ai or not self.data['child_pages']:
            return ""
        
        # 统计AI分析结果
        ai_analyzed = [p for p in self.data['child_pages'] if p.get('ai_analyzed', False)]
        ai_suspicious = [p for p in ai_analyzed if p.get('ai_suspicious', False)]
        
        if not ai_analyzed:
            return ""
        
        ai_section = f"""

<h2>🤖 AI智能分析结果</h2>

<p><em>AI分析了 {len(ai_analyzed)} 个页面，标记了 {len(ai_suspicious)} 个有"过期嫌疑"的页面。</em></p>

<h3>🚨 AI标记有"过期嫌疑"的页面</h3>

<table>
<tbody>
<tr>
<th>页面标题</th>
<th>父页面</th>
<th>最后更新</th>
<th>未更新天数</th>
<th>AI分析理由</th>
</tr>
"""
        
        # 显示有嫌疑的页面
        for page in ai_suspicious[:20]:  # 最多显示20个
            days = page.get('days_since_update', 0)
            reason = page.get('ai_reason', '')[:100]
            
            ai_section += f"""
<tr style="background-color: #fff3cd;">
<td><a href="{page['url']}">{page['title']}</a></td>
<td>{page.get('parent_title', '')}</td>
<td>{page.get('last_updated', '')[:10] if page.get('last_updated') else 'N/A'}</td>
<td>{days} 天</td>
<td>{reason}</td>
</tr>
"""
        
        ai_section += """
</tbody>
</table>
"""
        
        return ai_section
    
    def generate_direct_children_report_with_ai(self, current_time, elapsed, summary_url):
        """生成包含AI分析的直接子页面报告"""
        content = self.generate_direct_children_report(current_time, elapsed, summary_url)
        
        # 在报告最后添加AI分析部分
        ai_section = self.generate_ai_analysis_section()
        if ai_section:
            content += ai_section
        
        return content
    
    # ============ AI分析相关方法 ============
    
    def analyze_pages_with_ai(self, pages, max_analyze=None, batch_size=None):
        """
        使用AI分析页面是否有过期嫌疑
        """
        if max_analyze is None:
            max_analyze = self.ai_config['max_analyze']
        if batch_size is None:
            batch_size = self.ai_config['batch_size']
        
        print(f"   使用AI分析 {min(len(pages), max_analyze)} 个页面...")
        
        analyzed_pages = []
        not_analyzed_pages = []
        
        # 分离出要分析的和不分析的页面
        for i, page in enumerate(pages):
            if i < max_analyze:
                analyzed_pages.append(page)
            else:
                not_analyzed_pages.append(page)
        
        # 分批分析页面
        all_results = []
        total_batches = (len(analyzed_pages) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(analyzed_pages))
            batch = analyzed_pages[start_idx:end_idx]
            
            print(f"   分析批次 {batch_num + 1}/{total_batches}: {start_idx+1}-{end_idx}")
            
            # 批量分析
            batch_results = self.batch_analyze_with_ai(batch)
            all_results.extend(batch_results)
            
            # 防止API限制，添加延迟
            if batch_num < total_batches - 1:
                time.sleep(1)
        
        # 合并结果
        all_results.extend(not_analyzed_pages)
        
        # 统计AI分析结果
        suspicious_count = sum(1 for p in all_results if p.get('ai_suspicious', False))
        print(f"   AI分析完成: {len(analyzed_pages)}个页面已分析")
        print(f"   🚨 有过期嫌疑: {suspicious_count}个页面")
        
        return all_results
    
    def batch_analyze_with_ai(self, pages):
        """
        批量使用AI分析页面
        """
        # 构建批量分析的提示
        prompt = self.create_batch_ai_prompt(pages)
        print(f'{prompt}')
        try:
            # 调用OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": """你是一个技术文档分析专家。请根据页面标题和最后更新时间，判断这些页面是否有"过期嫌疑"。
                        请以JSON数组格式返回，每个元素包含：
                        {
                            "page_index": 序号,
                            "is_suspicious": true/false,
                            "reason": "简短理由"
                        }"""
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            # 解析AI响应
            ai_response = response.choices[0].message.content
            analysis_results = self.parse_ai_batch_response(ai_response, pages)
            
            # 更新页面数据
            for i, page in enumerate(pages):
                if i < len(analysis_results):
                    result = analysis_results[i]
                    page['ai_suspicious'] = result.get('is_suspicious', False)
                    page['ai_reason'] = result.get('reason', '')
                    page['ai_analyzed'] = True
                else:
                    page['ai_suspicious'] = False
                    page['ai_reason'] = '未分析'
                    page['ai_analyzed'] = False
            
            return pages
            
        except Exception as e:
            print(f"   ⚠️ AI分析出错: {str(e)}")
            for page in pages:
                page['ai_suspicious'] = False
                page['ai_reason'] = f'AI分析失败: {str(e)}'
                page['ai_analyzed'] = False
            
            return pages
    
    def create_batch_ai_prompt(self, pages):
        """
        创建批量分析的AI提示
        """
        prompt = "请分析以下Confluence页面是否有'过期嫌疑'：\n\n"
        
        for i, page in enumerate(pages):
            title = page.get('title', '')
            last_updated = page.get('last_updated', '')
            days_since = page.get('days_since_update', 0)
            parent = page.get('parent_title', '')
            
            # 计算天数
            if days_since == 0 and last_updated:
                days_since = self.calculate_days_since_update(last_updated)
                page['days_since_update'] = days_since
            
            prompt += f"{i+1}. 页面标题: {title}\n"
            prompt += f"   父页面: {parent}\n"
            prompt += f"   最后更新: {last_updated[:10] if last_updated else '未知'} ({days_since}天前)\n\n"
        
        prompt += "\n请返回JSON格式的分析结果。"
        return prompt
    
    def parse_ai_batch_response(self, ai_text, pages):
        """
        解析AI的批量响应
        """
        try:
            import re
            json_match = re.search(r'\[\s*\{.*\}\s*\]', ai_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                results = json.loads(json_str)
                return results
            else:
                print(f"   ⚠️ 无法解析AI响应中的JSON")
                return []
                
        except Exception as e:
            print(f"   ⚠️ 解析AI响应出错: {str(e)}")
            return []
    
    def calculate_days_since_update(self, last_updated_str):
        """
        计算距离上次更新的天数
        """
        try:
            if not last_updated_str:
                return 999
            
            # 解析日期
            last_updated = datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
            date_str = str(last_updated)[:19]
            last_update = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            
            # 计算天数差
            days_diff = (datetime.now() - last_update).days
            return days_diff
        
        except Exception:
            return 999

def main():
    print("="*80)
    print("Confluence页面扫描系统 (AI增强版)")
    print("="*80)
    
    # 从配置文件读取配置
    config_path = "config.json"
    scanner = ConfluenceScanner(config_path)
    
    # 从配置文件获取页面URL
    summary_url = scanner.config['confluence'].get('summary_page_url', '')
    target_url = scanner.config['confluence'].get('target_page_url', '')
    
    # 如果没有配置页面URL，则提示用户输入
    if not summary_url:
        print("\n📋 请输入汇总页面信息:")
        summary_url = input("汇总页面URL: ").strip()
        if not summary_url:
            print("❌ 必须提供汇总页面URL")
            return
    
    if not target_url:
        print("\n🎯 请输入目标报告页面:")
        target_url = input("目标报告页面URL: ").strip()
        if not target_url:
            print("❌ 必须提供目标报告页面URL")
            return
    
    # 显示配置信息
    print(f"\n📋 配置信息:")
    print(f"  汇总页面: {summary_url}")
    print(f"  目标页面: {target_url}")
    print(f"  用户名: {scanner.config['confluence']['username']}")
    print(f"  AI功能: {'启用' if scanner.use_ai else '禁用'}")
    
    # 询问是否要覆盖配置文件中的设置
    #override = input("\n是否覆盖配置文件中的扫描设置? (y/n, 默认n): ").strip().lower()
    override = 'n'
    if override == 'y':
        print("\n🤖 AI配置:")
        use_ai_input = input("启用AI分析页面过期嫌疑? (y/n, 默认y): ").strip().lower()
        use_ai = use_ai_input != 'n' if use_ai_input else True
        
        if use_ai and not scanner.config['ai']['openai_api_key']:
            print("⚠️ 配置文件中未设置AI API密钥，将不使用AI功能")
            use_ai = False
        
        scanner.use_ai = use_ai
        
        print("\n⚡ 配置扫描选项:")
        depth_choice = input("请选择扫描深度 (1=直接子页面, 2=包含孙子页面, 3=包含曾孙页面, 默认1): ").strip()
        max_depth = int(depth_choice) if depth_choice in ['1', '2', '3'] else 1
        
        max_threads_input = input("并发线程数 (默认3): ").strip()
        max_threads = int(max_threads_input) if max_threads_input else 3
        
        # 设置扫描配置
        scanner.set_scan_config(max_depth=max_depth,
                               max_threads=max_threads)
    else:
        # 使用配置文件中的默认设置
        max_depth = scanner.scan_config['max_depth']
        max_threads = scanner.scan_config['max_threads']
        scanner.set_scan_config(
            max_depth=max_depth,
            max_threads=max_threads
        )
    
    # 扫描并生成报告
    try:
        print(f"\n{'='*80}")
        print("开始扫描...")
        print("="*80)
        
        # 执行完整的报告生成流程
        report_url = scanner.create_complete_report(
            summary_page_url=summary_url,
            target_page_url=target_url,
            max_threads=max_threads
        )
        
        if report_url:
            print(f"\n✅ 报告生成成功!")
            print(f"📊 总页面数: {len(scanner.data['child_pages'])}")
            
            if scanner.use_ai:
                ai_analyzed = sum(1 for p in scanner.data['child_pages'] if p.get('ai_analyzed', False))
                ai_suspicious = sum(1 for p in scanner.data['child_pages'] if p.get('ai_suspicious', False))
                print(f"🤖 AI分析页面: {ai_analyzed}")
                print(f"🚨 AI标记有嫌疑: {ai_suspicious}")
                
            # 询问是否打开浏览器
            open_browser = input("\n是否在浏览器中打开报告页面? (y/n): ").lower()
            if open_browser == 'y':
                import webbrowser
                webbrowser.open(report_url)
        else:
            print("\n❌ 报告生成失败")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
    except Exception as e:
        print(f"\n❌ 执行过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
