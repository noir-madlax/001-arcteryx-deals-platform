// 德国男款数据提取脚本
(async function() {
  // 滚动页面加载所有商品
  for (let i = 0; i < 25; i++) {
    window.scrollBy(0, 5000);
    await new Promise(r => setTimeout(r, 600));
  }
  
  // 提取所有产品和图片
  const allLinks = Array.from(document.querySelectorAll('a'));
  const shopLinks = allLinks.filter(a => a.href.includes('/shop/'));
  const images = Array.from(document.querySelectorAll('img'));
  const imgixImages = images.filter(img => {
    const src = img.src || img.dataset?.src || '';
    return src.includes('imgix');
  });
  
  const products = [];
  const seen = new Set();
  
  for (const a of shopLinks) {
    const text = a.textContent.trim().replace(/\s+/g, ' ');
    const href = a.href;
    
    if (text.length < 15) continue;
    if (seen.has(href)) continue;
    seen.add(href);
    
    // 匹配价格 - 德国站使用美国格式：€220.00€154.00
    const priceMatch = text.match(/€\d+\.\d+/g);
    if (!priceMatch || priceMatch.length < 1) continue;
    
    // 提取名称（第一个价格之前）
    const fp = text.search(/€/);
    let name = fp > 0 ? text.substring(0, fp).trim() : text;
    
    // 解析价格
    const prices = priceMatch.map(p => {
      const num = p.replace('€', '').trim();
      return parseFloat(num);
    }).filter(n => !isNaN(n) && n > 0);
    
    if (prices.length === 0) continue;
    
    // 提取图片URL - 查找匹配的图片
    let imageUrl = '';
    for (const img of imgixImages) {
      const alt = img.alt || '';
      const src = img.src || img.dataset?.src || '';
      if (alt && name.toLowerCase().includes(alt.toLowerCase().substring(0, 15))) {
        imageUrl = src.split('?')[0]; // 移除查询参数
        break;
      }
    }
    
    // 计算折扣
    const original = prices[0];
    const sale = prices[1] || 0;
    const discount = sale > 0 ? Math.round((1 - sale/original) * 100) : 0;
    
    products.push({
      name,
      original_price: original,
      sale_price: sale,
      sale_price_max: prices[2] || sale,
      discount_pct: discount,
      currency: 'EUR',
      symbol: '€',
      gender: 'men',
      region: 'de',
      region_name: '德国',
      url: href,
      image_url: imageUrl,
      last_updated: new Date().toISOString().slice(0, 19).replace('T', ' ')
    });
  }
  
  return JSON.stringify(products);
})()